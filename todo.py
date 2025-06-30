import sys
from flask import Flask, request, jsonify, render_template, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import openai
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('todo.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='todo')  # Can be 'todo', 'in_progress', or 'done'
    assignee = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert todo item to dictionary format."""
        return {
            'id': self.id,
            'task': self.task,
            'done': self.done,
            'status': self.status,
            'assignee': self.assignee,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def get_by_id(todo_id: int) -> Optional['Todo']:
        """Get todo by ID or return None if not found."""
        return Todo.query.get(todo_id)

def init_db():
    """Initialize the database by creating tables if they don't exist."""
    with app.app_context():
        # Only create tables if they don't exist
        db.create_all()
        logger.info("Database initialized")

# Initialize the database
init_db()

# Load GitHub credentials
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')

print("GITHUB_TOKEN:", GITHUB_TOKEN)
print("GITHUB_REPO:", GITHUB_REPO)

def create_github_issue(title, body=None):
    """Create a GitHub issue in the configured repository."""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        logger.error("GitHub token or repo not set in environment variables.")
        return False, 'Missing GitHub credentials'
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    data = {"title": title}
    if body:
        data["body"] = body
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            logger.info(f"Created GitHub issue: {title}")
            return True, response.json()
        else:
            logger.error(f"Failed to create GitHub issue: {title} | Status: {response.status_code} | Response: {response.text}")
            return False, response.text
    except Exception as e:
        logger.error(f"Exception while creating GitHub issue: {title} | Error: {str(e)}")
        return False, str(e)

@app.route('/', methods=['GET', 'POST'])
def index() -> Any:
    """Main page for todo list."""
    if request.method == 'POST':
        task = request.form.get('task', '').strip()
        if not task:
            return render_template('index.html', todos=Todo.query.all(), error='Task cannot be empty')
        try:
            todo = Todo(task=task)
            db.session.add(todo)
            db.session.commit()
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Error creating todo: {str(e)}")
            db.session.rollback()
            return render_template('index.html', todos=Todo.query.all(), error='Failed to create todo')
    return render_template('index.html', todos=Todo.query.all())

@app.route('/toggle/<int:todo_id>', methods=['POST'])
def toggle_todo(todo_id: int) -> Any:
    """Toggle todo status between todo, in_progress, and done."""
    todo = Todo.get_by_id(todo_id)
    if not todo:
        abort(404, description="Todo not found")
    try:
        if todo.status == 'todo':
            todo.status = 'in_progress'
        elif todo.status == 'in_progress':
            todo.status = 'done'
            todo.done = True
        else:  # done
            todo.status = 'todo'
            todo.done = False
            todo.assignee = None
        db.session.commit()
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error toggling todo: {str(e)}")
        db.session.rollback()
        abort(500, description="Failed to update todo status")

@app.route('/delete/<int:todo_id>', methods=['POST'])
def delete_todo_ui(todo_id: int) -> Any:
    """Delete a todo item from the UI."""
    todo = Todo.get_by_id(todo_id)
    if not todo:
        abort(404, description="Todo not found")
    try:
        db.session.delete(todo)
        db.session.commit()
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error deleting todo: {str(e)}")
        db.session.rollback()
        abort(500, description="Failed to delete todo")

@app.route('/todos', methods=['GET'])
def get_todos() -> Any:
    """Get all todos as JSON."""
    try:
        todos = Todo.query.all()
        return jsonify([todo.to_dict() for todo in todos])
    except Exception as e:
        logger.error(f"Error getting todos: {str(e)}")
        abort(500, description="Failed to retrieve todos")

@app.route('/todos', methods=['POST'])
def add_todo() -> Any:
    """Add a new todo via API."""
    data = request.get_json()
    if not data or not data.get('task', '').strip():
        return jsonify({'error': 'Task is required'}), 400
    try:
        todo = Todo(task=data['task'].strip())
        db.session.add(todo)
        db.session.commit()
        return jsonify(todo.to_dict()), 201
    except Exception as e:
        logger.error(f"Error creating todo via API: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create todo'}), 500

@app.route('/export', methods=['GET'])
def export_todos_as_json():
    """Export all todos as a downloadable JSON file."""
    try:
        todos = Todo.query.all()
        todo_dicts = [todo.to_dict() for todo in todos]
        return jsonify(todo_dicts), 200
    except Exception as e:
        logger.error(f"Error exporting todos: {str(e)}")
        return jsonify({'error': 'Failed to export todos'}), 500


@app.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id: int) -> Any:
    """Update a todo via API."""
    todo = Todo.get_by_id(todo_id)
    if not todo:
        return jsonify({'error': 'Todo not found'}), 404
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    try:
        if 'task' in data and data['task'].strip():
            todo.task = data['task'].strip()
        if 'done' in data:
            todo.done = bool(data['done'])
        db.session.commit()
        return jsonify(todo.to_dict())
    except Exception as e:
        logger.error(f"Error updating todo: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update todo'}), 500

@app.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id: int) -> Any:
    """Delete a todo via API."""
    todo = Todo.get_by_id(todo_id)
    if not todo:
        return jsonify({'error': 'Todo not found'}), 404
    try:
        db.session.delete(todo)
        db.session.commit()
        return '', 204
    except Exception as e:
        logger.error(f"Error deleting todo via API: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete todo'}), 500

@app.route('/update_todo/<int:todo_id>', methods=['POST'])
def update_todo_details(todo_id: int) -> Any:
    """Update assignee and notes for a todo item."""
    todo = Todo.get_by_id(todo_id)
    if not todo:
        abort(404, description="Todo not found")
    
    try:
        data = request.form
        if 'assignee' in data:
            todo.assignee = data['assignee'].strip() or None
        if 'notes' in data:
            todo.notes = data['notes'].strip() or None
        
        db.session.commit()
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error updating todo details: {str(e)}")
        db.session.rollback()
        abort(500, description="Failed to update todo details")

@app.route('/test', methods=['GET'])
def test_endpoint() -> Any:
    """Test endpoint to verify server is running."""
    return jsonify({
        "status": "ok",
        "message": "Server is running",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/reset-db', methods=['POST'])
def reset_database() -> Any:
    """Reset database for testing purposes."""
    try:
        with app.app_context():
            db.drop_all()
            db.create_all()
            logger.info("Database reset for testing")
        return jsonify({"message": "Database reset successfully"}), 200
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        return jsonify({"error": "Failed to reset database"}), 500

@app.errorhandler(404)
def not_found_error(error: Any) -> Any:
    """Handle 404 errors."""
    return jsonify({'error': str(error.description)}), 404

@app.errorhandler(500)
def internal_error(error: Any) -> Any:
    """Handle 500 errors."""
    db.session.rollback()
    return jsonify({'error': str(error.description)}), 500

def extract_action_items_with_ai(text: str) -> List[str]:
    """Extract action items from meeting transcript using OpenAI GPT."""
    try:
        # Prepare the prompt for GPT
        prompt = f"""
Rewrite the following meeting transcript into a list of clear, actionable tasks.
- Do NOT copy sentences verbatim from the transcript.
- For each action item, rewrite it as a concise, actionable task starting with a verb (e.g., Meet, Build, Handle, Transition, Get, Start, Complete, Send, Review, Update, Prepare, Schedule, Create, Implement, etc.).
- Ignore vague, incomplete, or conversational statements.
- Only output clear, actionable tasks, one per line.
- If there are no clear action items, return an empty list.

Positive Examples:
Input: "Next week we gonna try to get a couple other things done."
Output: "Complete outstanding tasks next week"

Input: "You know, we gotta make a payment service and all the stuff that revolves around that."
Output: "Build or configure the payment service"

Input: "The handle data doing autopay scheduled payments, stuff like that, and then transitioning everything over."
Output: "Handle data for autopay and scheduled payments"
Output: "Transition everything over"

Input: "So there's a lot of work to be done, but yeah, definitely we, me and Eugene had talked about. We're gonna meet with Arista next week and kinda get their eyes on it and see what we need to do, see if they have any feedback or and then get."
Output: "Meet with Arista next week"
Output: "Get Arista's feedback on the transition process"

Negative Examples:
Input: "There's gonna be some."
Output: (ignore)

Input: "Yeah."
Output: (ignore)

Input: "Umm."
Output: (ignore)

Input: "Them kind of started moving to what they need to do."
Output: "Start moving Arista to what they need to do"

Transcript:
{text}

Output only the action items, one per line. Do not copy sentences verbatim.
"""
        # Call OpenAI API
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts clear, actionable items from meeting transcripts. You focus on identifying specific tasks, assignments, and follow-ups."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more focused, consistent output
            max_tokens=500
        )
        # Process the response
        extracted_text = response.choices[0].message.content.strip()
        # Split into individual action items and clean them
        action_items = [
            item.strip() 
            for item in extracted_text.split('\n') 
            if item.strip() and not item.strip().startswith(('No action items', 'No clear', 'None found'))
        ]
        # Post-processing: keep only lines that start with a strong action verb
        def is_action_item(line: str) -> bool:
            action_verbs = [
                'Meet', 'Get', 'Start', 'Build', 'Handle', 'Transition', 'Complete', 'Send', 'Review', 'Update', 'Prepare', 'Schedule', 'Create', 'Implement'
            ]
            return any(line.strip().startswith(verb) for verb in action_verbs)
        action_items = [item for item in action_items if is_action_item(item)]
        logger.debug(f"AI extracted {len(action_items)} action items")
        for i, item in enumerate(action_items, 1):
            logger.debug(f"{i}. {item}")
        return action_items
    except Exception as e:
        logger.error(f"Error in AI extraction: {str(e)}")
        # Fallback to basic extraction if AI fails
        return extract_action_items_basic(text)

def extract_action_items_basic(text: str) -> List[str]:
    """Basic pattern matching fallback for action item extraction."""
    # Common action item triggers
    triggers = [
        'need to', 'should', 'must', 'have to', 'will', 'going to',
        'action item', 'todo', 'task', 'follow up', 'next steps',
        'meet with', 'schedule', 'set up', 'create', 'implement',
        'review', 'update', 'prepare', 'send', 'get', 'make'
    ]
    
    # Clean and split the text into lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    action_items = []
    for line in lines:
        # Skip empty lines and timestamps
        if not line or any(c.isdigit() for c in line[:5]):
            continue
            
        # Skip speaker labels
        if line.startswith('Speaker') or line.startswith('@'):
            continue
            
        # Convert to lowercase for matching
        line_lower = line.lower()
        
        # Check if line contains any trigger words
        if any(trigger in line_lower for trigger in triggers):
            # Clean up the action item
            item = line.strip()
            if item not in action_items:  # Avoid duplicates
                action_items.append(item)
    
    return action_items

@app.route('/extract-todos', methods=['POST'])
def extract_todos() -> Any:
    """Extract action items from submitted text and add them to the todo list."""
    logger.debug("\n=== Extract Todos Endpoint Called ===")
    
    # Get text from either JSON or form data
    if request.is_json:
        data = request.get_json()
        text = data.get('text', '')
    else:
        text = request.form.get('text', '')
    
    if not text:
        logger.error("No text provided")
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        # Extract action items using AI
        logger.debug("\nCalling extract_action_items...")
        action_items = extract_action_items_with_ai(text)
        logger.debug("\nExtracted %d action items:", len(action_items))
        for i, item in enumerate(action_items, 1):
            logger.debug("%d. %s", i, item)
        
        # Add each action item to the todo list
        created_todos = []
        github_results = []
        for item in action_items:
            logger.debug("\nProcessing item: %s", item)
            existing_todo = Todo.query.filter_by(task=item).first()
            if existing_todo:
                logger.debug("Item already exists: %s", item)
                continue
            logger.debug("Creating new todo: %s", item)
            todo = Todo(task=item)
            db.session.add(todo)
            created_todos.append(todo)
            # Create GitHub issue for each new action item
            success, result = create_github_issue(item)
            github_results.append({"item": item, "success": success, "result": result})
        logger.debug("\nCommitting %d new todos to database", len(created_todos))
        db.session.commit()
        response = {
            'message': f'Successfully extracted {len(created_todos)} new action items',
            'action_items': [todo.to_dict() for todo in created_todos],
            'github_results': github_results,
            'debug_info': {
                'total_items_found': len(action_items),
                'items_created': len(created_todos),
                'items_skipped': len(action_items) - len(created_todos)
            }
        }
        logger.debug("\nSending response: %s", response)
        return jsonify(response), 201
    except Exception as e:
        logger.error(f"Error during extraction: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
