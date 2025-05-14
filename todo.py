import sys
print(sys.executable)

from flask import Flask, request, jsonify, render_template, redirect, url_for
import requests

app = Flask(__name__)

# In-memory storage for to-dos
todos = []
next_id = 1

@app.route('/', methods=['GET', 'POST'])
def index():
    global next_id
    if request.method == 'POST':
        task = request.form.get('task')
        if task:
            todos.append({'id': next_id, 'task': task, 'done': False})
            next_id += 1
        return redirect(url_for('index'))
    return render_template('index.html', todos=todos)

@app.route('/toggle/<int:todo_id>', methods=['POST'])
def toggle_todo(todo_id):
    for todo in todos:
        if todo['id'] == todo_id:
            todo['done'] = not todo['done']
            break
    return redirect(url_for('index'))

@app.route('/delete/<int:todo_id>', methods=['POST'])
def delete_todo_ui(todo_id):
    global todos
    todos = [todo for todo in todos if todo['id'] != todo_id]
    return redirect(url_for('index'))

@app.route('/todos', methods=['GET'])
def get_todos():
    return jsonify(todos)

@app.route('/todos', methods=['POST'])
def add_todo():
    global next_id
    data = request.get_json()
    if not data or 'task' not in data:
        return jsonify({'error': 'Task is required'}), 400
    todo = {'id': next_id, 'task': data['task'], 'done': False}
    todos.append(todo)
    next_id += 1
    return jsonify(todo), 201

@app.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    data = request.get_json()
    for todo in todos:
        if todo['id'] == todo_id:
            todo['task'] = data.get('task', todo['task'])
            todo['done'] = data.get('done', todo['done'])
            return jsonify(todo)
    return jsonify({'error': 'Todo not found'}), 404

@app.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    global todos
    todos = [todo for todo in todos if todo['id'] != todo_id]
    return '', 204

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use PORT from Render
    app.run(host="0.0.0.0", port=port, debug=True)
