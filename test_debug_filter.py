import requests
import json

def test_filtering():
    base_url = "http://127.0.0.1:5000"
    
    # Reset database
    response = requests.post(f"{base_url}/reset-db")
    print(f"Reset DB: {response.status_code}")
    
    # Add test todos
    todos = [
        {"task": "Task for John"},
        {"task": "Task for Jane"}, 
        {"task": "Unassigned task"}
    ]
    
    for todo in todos:
        response = requests.post(f"{base_url}/todos", json=todo)
        print(f"Added todo '{todo['task']}': {response.status_code}")
    
    # Get all todos
    response = requests.get(f"{base_url}/todos")
    todos_data = response.json()
    print(f"\nAll todos: {json.dumps(todos_data, indent=2)}")
    
    # Update first todo to assign to John
    if todos_data:
        response = requests.put(f"{base_url}/todos/{todos_data[0]['id']}", 
                              json={"task": todos_data[0]['task'], "assignee": "John"})
        print(f"Assigned first todo to John: {response.status_code}")
    
    # Update second todo to assign to Jane  
    if len(todos_data) > 1:
        response = requests.put(f"{base_url}/todos/{todos_data[1]['id']}", 
                              json={"task": todos_data[1]['task'], "assignee": "Jane"})
        print(f"Assigned second todo to Jane: {response.status_code}")
    
    # Get updated todos
    response = requests.get(f"{base_url}/todos")
    todos_data = response.json()
    print(f"\nUpdated todos: {json.dumps(todos_data, indent=2)}")

if __name__ == "__main__":
    test_filtering() 