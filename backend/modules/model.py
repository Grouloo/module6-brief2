import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Conv2D, Flatten, MaxPooling2D, Dropout
from tensorflow.keras.datasets import mnist
from tensorflow.keras.utils import to_categorical
from loguru import logger
from PIL import Image
import io

MODEL_PATH = "/app/data/mnist_model.h5"

class MNISTModel:
    def __init__(self):
        self.model = None
        self.load_or_train()

    def load_or_train(self):
        if os.path.exists(MODEL_PATH):
            try:
                logger.info(f"Loading model from {MODEL_PATH}")
                self.model = load_model(MODEL_PATH)
            except Exception as e:
                logger.error(f"Error loading model: {e}. Retraining...")
                self.train_initial_model()
        else:
            logger.info("Model not found. Training initial model...")
            self.train_initial_model()

    def train_initial_model(self):
        (x_train, y_train), (x_test, y_test) = mnist.load_data()
        
        # Preprocessing
        x_train = x_train.reshape(x_train.shape[0], 28, 28, 1).astype('float32') / 255
        x_test = x_test.reshape(x_test.shape[0], 28, 28, 1).astype('float32') / 255
        y_train = to_categorical(y_train)
        y_test = to_categorical(y_test)

        # Build model
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
        model.fit(x_train, y_train, validation_data=(x_test, y_test), epochs=5, batch_size=200, verbose=1)
        
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        model.save(MODEL_PATH)
        self.model = model
        logger.info(f"Model trained and saved to {MODEL_PATH}")

    def predict(self, image_bytes):
        if self.model is None:
            raise Exception("Model not loaded")

        img = Image.open(io.BytesIO(image_bytes))
        img = img.resize((28, 28))
        img = img.convert('L')
        img_array = np.array(img)
        
        # Normalize and reshape
        img_array = img_array.astype('float32') / 255
        img_array = img_array.reshape(1, 28, 28, 1)

        prediction_probs = self.model.predict(img_array)
        prediction = np.argmax(prediction_probs)
        return int(prediction), prediction_probs.tolist()[0]

    def reload(self):
        self.load_or_train()

# Global instance
mnist_model = MNISTModel()
