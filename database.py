import sqlite3
import logging
from typing import Optional, List, Dict, Any
import json

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                phone_number TEXT UNIQUE,
                session_string TEXT,
                is_active INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP,
                total_stars REAL DEFAULT 0,
                registration_state TEXT DEFAULT 'none'
            )
        """)
        
        # Tasks table to track completed tasks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task_type TEXT,
                channel_link TEXT,
                reward REAL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Settings table for user-specific settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                auto_collect INTEGER DEFAULT 0,
                notifications INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def add_user(self, user_id: int, phone_number: str = None) -> bool:
        """Add a new user to the database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR IGNORE INTO users (user_id, phone_number) 
                VALUES (?, ?)
            """, (user_id, phone_number))
            
            cursor.execute("""
                INSERT OR IGNORE INTO user_settings (user_id) 
                VALUES (?)
            """, (user_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            return False
    
    def update_user_session(self, user_id: int, session_string: str) -> bool:
        """Update user's session string"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET session_string = ?, registration_state = 'completed'
                WHERE user_id = ?
            """, (session_string, user_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating session for user {user_id}: {e}")
            return False
    
    def update_user_phone(self, user_id: int, phone_number: str) -> bool:
        """Update user's phone number"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET phone_number = ?, registration_state = 'phone_added'
                WHERE user_id = ?
            """, (phone_number, user_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating phone for user {user_id}: {e}")
            return False
    
    def update_registration_state(self, user_id: int, state: str) -> bool:
        """Update user's registration state"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET registration_state = ?
                WHERE user_id = ?
            """, (state, user_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating registration state for user {user_id}: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM users WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def get_user_settings(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user settings"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM user_settings WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(f"Error getting settings for user {user_id}: {e}")
            return None
    
    def set_auto_collect(self, user_id: int, enabled: bool) -> bool:
        """Enable/disable auto collection for user"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE user_settings 
                SET auto_collect = ?
                WHERE user_id = ?
            """, (1 if enabled else 0, user_id))
            
            cursor.execute("""
                UPDATE users 
                SET is_active = ?, last_activity = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (1 if enabled else 0, user_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error setting auto collect for user {user_id}: {e}")
            return False
    
    def add_task(self, user_id: int, task_type: str, channel_link: str, reward: float) -> bool:
        """Add a completed task to the database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO tasks (user_id, task_type, channel_link, reward)
                VALUES (?, ?, ?, ?)
            """, (user_id, task_type, channel_link, reward))
            
            cursor.execute("""
                UPDATE users 
                SET total_stars = total_stars + ?, last_activity = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (reward, user_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error adding task for user {user_id}: {e}")
            return False
    
    def get_active_users(self) -> List[Dict[str, Any]]:
        """Get all users with auto collection enabled"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.*, s.auto_collect 
                FROM users u
                JOIN user_settings s ON u.user_id = s.user_id
                WHERE s.auto_collect = 1 AND u.session_string IS NOT NULL
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    total_stars,
                    (SELECT COUNT(*) FROM tasks WHERE user_id = ?) as total_tasks,
                    (SELECT COUNT(*) FROM tasks WHERE user_id = ? AND DATE(completed_at) = DATE('now')) as today_tasks
                FROM users 
                WHERE user_id = ?
            """, (user_id, user_id, user_id))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'total_stars': row[0] or 0,
                    'total_tasks': row[1] or 0,
                    'today_tasks': row[2] or 0
                }
            return {'total_stars': 0, 'total_tasks': 0, 'today_tasks': 0}
        except Exception as e:
            logger.error(f"Error getting stats for user {user_id}: {e}")
            return {'total_stars': 0, 'total_tasks': 0, 'today_tasks': 0}