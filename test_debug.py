#!/usr/bin/env python3
"""
Simple test script to verify database initialization works correctly.
"""

import os
import sys
from todo import app, db, Todo

def test_database_init():
    """Test that database initialization works without dropping tables."""
    print("Testing database initialization...")
    
    with app.app_context():
        # Check if database file exists
        db_path = os.path.join(app.instance_path, 'todos.db')
        print(f"Database path: {db_path}")
        print(f"Database exists: {os.path.exists(db_path)}")
        
        # Initialize database
        db.create_all()
        print("Database tables created successfully")
        
        # Add a test todo
        test_todo = Todo(task="Test task")
        db.session.add(test_todo)
        db.session.commit()
        print("Test todo added successfully")
        
        # Query todos
        todos = Todo.query.all()
        print(f"Number of todos in database: {len(todos)}")
        for todo in todos:
            print(f"  - {todo.task} (ID: {todo.id})")
        
        # Clean up test todo
        db.session.delete(test_todo)
        db.session.commit()
        print("Test todo cleaned up")

if __name__ == "__main__":
    test_database_init() 