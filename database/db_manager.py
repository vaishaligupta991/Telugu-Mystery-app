import sqlite3
import os
from datetime import datetime
import uuid

class TeluguCorpusDB:
    def __init__(self, db_path="data/database/telugu_corpus.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    location TEXT,
                    native_dialect TEXT,
                    age_group TEXT,
                    total_points INTEGER DEFAULT 0,
                    mysteries_solved INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Text responses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS text_responses (
                    response_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    mystery_id TEXT,
                    response_text TEXT,
                    word_count INTEGER,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Voice responses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS voice_responses (
                    response_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    mystery_id TEXT,
                    audio_file_path TEXT,
                    duration_seconds REAL,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Image responses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS image_responses (
                    response_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    mystery_id TEXT,
                    image_file_path TEXT,
                    description TEXT,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            conn.commit()
    
    def create_user(self, user_data):
        """Create a new user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, username, location, native_dialect, age_group)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_data['user_id'],
                user_data['username'],
                user_data.get('location', ''),
                user_data.get('native_dialect', ''),
                user_data.get('age_group', '')
            ))
            conn.commit()
    
    def get_user(self, user_id):
        """Get user by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
        return None
    
    def save_response(self, response_data):
        """Save a text response"""
        response_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO text_responses 
                (response_id, user_id, mystery_id, response_text, word_count)
                VALUES (?, ?, ?, ?, ?)
            """, (
                response_id,
                response_data['user_id'],
                response_data['mystery_id'],
                response_data['response_text'],
                response_data['word_count']
            ))
            conn.commit()
    
    def update_user_points(self, user_id, points):
        """Update user points and mystery count"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET total_points = total_points + ?, 
                    mysteries_solved = mysteries_solved + 1
                WHERE user_id = ?
            """, (points, user_id))
            conn.commit()
    
    def get_total_responses(self):
        """Get total number of responses"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM text_responses")
            return cursor.fetchone()[0]
    
    def get_active_users_count(self):
        """Get count of active users"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE total_points > 0")
            return cursor.fetchone()[0]
    
    def get_leaderboard(self, limit=20):
        """Get leaderboard data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, total_points, mysteries_solved, location
                FROM users 
                WHERE total_points > 0
                ORDER BY total_points DESC 
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
