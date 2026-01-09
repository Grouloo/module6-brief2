import sqlite3
import os
from loguru import logger

DB_PATH = "/app/data/corrections.db"

def init_db():
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT NOT NULL,
                true_label INTEGER NOT NULL,
                predicted_label INTEGER NOT NULL,
                processed BOOLEAN DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if 'processed' column exists (migration for existing DB)
        cursor.execute("PRAGMA table_info(corrections)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'processed' not in columns:
            logger.info("Migrating database: adding 'processed' column")
            cursor.execute("ALTER TABLE corrections ADD COLUMN processed BOOLEAN DEFAULT 0")
            
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
            INSERT INTO corrections (image_path, true_label, predicted_label, processed)
            VALUES (?, ?, ?, 0)
        ''', (image_path, true_label, predicted_label))
        conn.commit()
        conn.close()
        logger.info(f"Correction saved: {image_path}, True: {true_label}, Pred: {predicted_label}")
    except Exception as e:
        logger.error(f"Error saving correction: {e}")
        raise e

def get_corrections(processed_status: bool = None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM corrections'
        params = []
        
        if processed_status is not None:
            query += ' WHERE processed = ?'
            params.append(1 if processed_status else 0)
            
        cursor.execute(query, params)
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Error retrieving corrections: {e}")
        return []

def mark_corrections_as_processed(ids: list):
    if not ids:
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # id_list_str = ','.join(['?'] * len(ids))
        # cursor.execute(f'UPDATE corrections SET processed = 1 WHERE id IN ({id_list_str})', ids)
        # Simplified for safer large lists or just easier logic:
        cursor.execute(f'UPDATE corrections SET processed = 1 WHERE id IN ({",".join(map(str, ids))})')
        conn.commit()
        conn.close()
        logger.info(f"Marked {len(ids)} corrections as processed.")
    except Exception as e:
        logger.error(f"Error marking corrections as processed: {e}")
