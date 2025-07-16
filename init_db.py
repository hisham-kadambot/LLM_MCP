#!/usr/bin/env python3
"""
Database initialization script for the MCP server application.
This script creates the SQLite database and tables.
"""

import os
import sys

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import create_tables, engine
from app.auth import create_user, get_password_hash
from app.database import SessionLocal, User

def init_database():
    """Initialize the database with tables"""
    print("Creating database tables...")
    create_tables()
    print("Database tables created successfully!")
    
    # Create a default admin user if no users exist
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            print("Creating default admin user...")
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                is_active=1
            )
            db.add(admin_user)
            db.commit()
            print("Default admin user created!")
            print("Username: admin")
            print("Password: admin123")
            print("Please change these credentials after first login!")
        else:
            print(f"Database already contains {user_count} user(s)")
    except Exception as e:
        print(f"Error creating default user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_database() 