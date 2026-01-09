import sqlite3
import os
from loguru import logger

DB_PATH = "/app/data/corrections.db"

def init_db():
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT NOT NULL,
                true_label INTEGER NOT NULL,
                predicted_label INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

def save_correction(image_path: str, true_label: int, predicted_label: int):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO corrections (image_path, true_label, predicted_label)
            VALUES (?, ?, ?)
        ''', (image_path, true_label, predicted_label))
        conn.commit()
        conn.close()
        logger.info(f"Correction saved: {image_path}, True: {true_label}, Pred: {predicted_label}")
    except Exception as e:
        logger.error(f"Error saving correction: {e}")
        raise e

def get_corrections():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM corrections')
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Error retrieving corrections: {e}")
        return []
