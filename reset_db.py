#!/usr/bin/env python3
"""
Script to reset the database for testing purposes.
"""

import os
from todo import app, db

def reset_database():
    """Reset the database by dropping all tables and recreating them."""
    print("Resetting database...")
    
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("Dropped all tables")
        
        # Create new tables
        db.create_all()
        print("Created fresh database")
        
        # Verify database is empty
        from todo import Todo
        todos = Todo.query.all()
        print(f"Database is empty: {len(todos) == 0}")

if __name__ == "__main__":
    reset_database() 