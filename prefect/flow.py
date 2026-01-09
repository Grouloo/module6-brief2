import os
import sqlite3
import pandas as pd
import numpy as np
import requests
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Conv2D, Flatten, MaxPooling2D, Dropout
from tensorflow.keras.datasets import mnist
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from prefect import flow, task, get_run_logger
from PIL import Image

DB_PATH = "/app/data/corrections.db"
MODEL_PATH = "/app/data/mnist_model.h5"
DRIFT_THRESHOLD = int(os.getenv("DRIFT_THRESHOLD", "5")) # Retrain if > 5 corrections

@task
def check_corrections():
    logger = get_run_logger()
    if not os.path.exists(DB_PATH):
        logger.info("Database not found. No corrections yet.")
        return []
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM corrections", conn)
    conn.close()
    
    logger.info(f"Found {len(df)} corrections.")
    return df

@task
def retrain_model(corrections_df):
    logger = get_run_logger()
    logger.info("Starting retraining process...")
    
    # Load base MNIST data
    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    
    # Preprocessing MNIST
    x_train = x_train.reshape(x_train.shape[0], 28, 28, 1).astype('float32') / 255
    x_test = x_test.reshape(x_test.shape[0], 28, 28, 1).astype('float32') / 255
    y_train = to_categorical(y_train, 10)
    y_test = to_categorical(y_test, 10)
    
    # Process corrections
    new_images = []
    new_labels = []
    
    for idx, row in corrections_df.iterrows():
        try:
            img_path = row['image_path']
            true_label = row['true_label']
            
            img = Image.open(img_path).convert('L')
            img = img.resize((28, 28))
            img_array = np.array(img).astype('float32') / 255
            img_array = img_array.reshape(28, 28, 1)
            
            new_images.append(img_array)
            new_labels.append(true_label)
        except Exception as e:
            logger.warning(f"Could not process correction image {row['image_path']}: {e}")
            
    if new_images:
        new_x = np.array(new_images)
        new_y = to_categorical(np.array(new_labels), 10)
        
        # Combine datasets
        x_train = np.concatenate((x_train, new_x), axis=0)
        y_train = np.concatenate((y_train, new_y), axis=0)
        logger.info(f"Added {len(new_images)} correction images to training set.")
        
    # Data Augmentation
    aug = ImageDataGenerator(rotation_range=10, zoom_range=0.1, width_shift_range=0.1, height_shift_range=0.1)
    
    # Build model (same architecture as backend to be consistent)
    model = Sequential([
        Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(28, 28, 1)),
        MaxPooling2D(pool_size=(2, 2)),
        Conv2D(64, kernel_size=(3, 3), activation='relu'),
        MaxPooling2D(pool_size=(2, 2)),
        Flatten(),
        Dense(128, activation='relu'),
        Dropout(0.5),
        Dense(10, activation='softmax')
    ])
    
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    
    # Train
    logger.info("Training model...")
    model.fit(aug.flow(x_train, y_train, batch_size=64),
              epochs=5, 
              validation_data=(x_test, y_test),
              verbose=1)
              
    # Save
    model.save(MODEL_PATH)
    logger.info(f"Model saved to {MODEL_PATH}")
    return True

@task
def notify_backend():
    logger = get_run_logger()
    try:
        response = requests.post("http://backend:8000/reload")
        if response.status_code == 200:
            logger.info("Backend successfully reloaded model.")
        else:
            logger.error(f"Backend failed to reload model: {response.status_code}")
    except Exception as e:
        logger.error(f"Error calling backend reload: {e}")

@task
def mark_processed(ids):
    logger = get_run_logger()
    if not ids:
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f'UPDATE corrections SET processed = 1 WHERE id IN ({",".join(map(str, ids))})')
        conn.commit()
        conn.close()
        logger.info(f"Marked {len(ids)} corrections as processed.")
    except Exception as e:
        logger.error(f"Error marking corrections as processed: {e}")

@flow(name="mnist_retraining_flow")
def mnist_retraining_flow():
    logger = get_run_logger()
    logger.info("Checking for model drift/corrections...")
    
    corrections = check_corrections()
    
    if corrections.empty:
        logger.info("No corrections found.")
        return

    # Check for unprocessed corrections
    if 'processed' not in corrections.columns:
        # Handle case where column might be missing if DB wasn't migrated (though backend init_db does it)
        # or if older records exist. 
        # For robustness, assume all are unprocessed if column missing, or 0.
        # But we added the column in backend. The flow reads what's there.
        # If the column is missing in the DF, it means the SELECT * didn't return it? 
        # SQLite adds column on ALTER, so it should be there.
        unprocessed_count = len(corrections)
        unprocessed_ids = corrections['id'].tolist()
    else:
        # Filter where processed == 0 or False (SQLite uses 0/1)
        unprocessed = corrections[corrections['processed'] == 0]
        unprocessed_count = len(unprocessed)
        unprocessed_ids = unprocessed['id'].tolist()
    
    logger.info(f"Found {len(corrections)} total corrections, {unprocessed_count} new (unprocessed).")

    # Logic: If we have enough NEW corrections
    if unprocessed_count > DRIFT_THRESHOLD: 
        logger.info(f"Threshold exceeded ({unprocessed_count} > {DRIFT_THRESHOLD}). Retraining model.")
        success = retrain_model(corrections)
        if success:
            notify_backend()
            mark_processed(unprocessed_ids)
    else:
        logger.info(f"Not enough new data to justify retraining (Threshold: {DRIFT_THRESHOLD}).")

if __name__ == "__main__":
    mnist_retraining_flow.serve(name="mnist-retraining-deployment", cron="0 * * * *") # Every hour