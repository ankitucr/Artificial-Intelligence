import json
import os

TODOS_FILE = 'todos.json'

def load_todos():
    if os.path.exists(TODOS_FILE):
        with open(TODOS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_todos(todos):
    with open(TODOS_FILE, 'w') as f:
        json.dump(todos, f, indent=4)

def add_todo(title):
    todos = load_todos()
    todos.append({'id': len(todos) + 1, 'title': title, 'completed': False})
    save_todos(todos)

def list_todos():
    return load_todos()

def complete_todo(todo_id):
    todos = load_todos()
    try:
        todo_id = int(todo_id)
        for todo in todos:
            if todo['id'] == todo_id:
                todo['completed'] = True
                save_todos(todos)
                return
        raise ValueError(f"Todo with id {todo_id} not found")
    except ValueError as e:
        raise ValueError(f"Invalid todo id: {e}")

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python todo_app.py <command> [args]")
        return

    command = sys.argv[1]
    if command == 'add':
        if len(sys.argv) < 3:
            print("Usage: python todo_app.py add <title>")
            return
        title = ' '.join(sys.argv[2:])
        add_todo(title)
        print(f"Added todo: {title}")
    elif command == 'list':
        todos = list_todos()
        for todo in todos:
            status = '✓' if todo['completed'] else ' '
            print(f"[{status}] {todo['id']}: {todo['title']}")
    elif command == 'complete':
        if len(sys.argv) < 3:
            print("Usage: python todo_app.py complete <id>")
            return
        try:
            todo_id = sys.argv[2]
            complete_todo(todo_id)
            print(f"Completed todo {todo_id}")
        except ValueError as e:
            print(str(e))
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()