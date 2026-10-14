import os
import json
import unittest
from todo_app import load_todos, save_todos, add_todo, complete_todo, TODOS_FILE

class TestTodoApp(unittest.TestCase):

    def setUp(self):
        if os.path.exists(TODOS_FILE):
            os.remove(TODOS_FILE)

    def test_add_todo(self):
        add_todo("Buy groceries")
        todos = load_todos()
        self.assertEqual(len(todos), 1)
        self.assertEqual(todos[0]['title'], "Buy groceries")
        self.assertFalse(todos[0]['completed'])

    def test_list_todos(self):
        add_todo("Buy groceries")
        add_todo("Clean house")
        todos = load_todos()
        self.assertEqual(len(todos), 2)

    def test_complete_todo(self):
        add_todo("Buy groceries")
        todos = load_todos()
        todo_id = todos[0]['id']
        complete_todo(todo_id)
        todos = load_todos()
        self.assertTrue(todos[0]['completed'])

    def test_invalid_todo_id(self):
        with self.assertRaises(ValueError):
            complete_todo("invalid_id")

    def test_non_existent_todo_id(self):
        with self.assertRaises(ValueError):
            complete_todo(999)

if __name__ == '__main__':
    unittest.main()