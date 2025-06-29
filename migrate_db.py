import sqlite3
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_database():
    """Migrate the database to add new columns."""
    try:
        # Connect to the database
        conn = sqlite3.connect('instance/todos.db')
        cursor = conn.cursor()
        
        # Check if columns exist
        cursor.execute("PRAGMA table_info(todo)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add new columns if they don't exist
        if 'created_at' not in columns:
            logger.info("Adding created_at column")
            cursor.execute('ALTER TABLE todo ADD COLUMN created_at DATETIME')
        
        if 'updated_at' not in columns:
            logger.info("Adding updated_at column")
            cursor.execute('ALTER TABLE todo ADD COLUMN updated_at DATETIME')
        
        # Update existing rows with current timestamp
        current_time = datetime.utcnow()
        cursor.execute(
            'UPDATE todo SET created_at = ?, updated_at = ? WHERE created_at IS NULL',
            (current_time, current_time)
        )
        
        # Commit changes
        conn.commit()
        logger.info("Database migration completed successfully")
        
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_database() 