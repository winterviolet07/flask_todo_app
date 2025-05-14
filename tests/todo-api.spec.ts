// todo-api.spec.ts
import { test, expect, request, APIRequestContext, APIResponse } from '@playwright/test';

// Define the Todo interface
interface Todo {
  id: number;
  task: string;
  done: boolean;
}

// Helper function to delete all todos
async function deleteAllTodos(api: APIRequestContext) {
  const response = await api.get('/todos');
  const todos: Todo[] = await response.json();
  for (const todo of todos) {
    await api.delete(`/todos/${todo.id}`);
  }
}

test.describe('To-Do API', () => {
  let api: APIRequestContext;
  let todoId: number;

  // Setup before all tests
  test.beforeAll(async ({ playwright }) => {
    api = await request.newContext({
      baseURL: 'http://127.0.0.1:5000',
    });
  });

  // Cleanup before each test
  test.beforeEach(async () => {
    // Delete all existing todos to ensure a clean state
    await deleteAllTodos(api);

    // Create a fresh test todo
    const createResponse = await api.post('/todos', {
      data: { task: 'Test todo' },
    });
    const createdTodo: Todo = await createResponse.json();
    todoId = createdTodo.id;
  });

  // Cleanup after each test
  test.afterEach(async () => {
    await deleteAllTodos(api);
  });

  // Cleanup after all tests
  test.afterAll(async () => {
    await deleteAllTodos(api);
    await api.dispose();
  });

  test('should create a new to-do', async () => {
    const response: APIResponse = await api.post('/todos', {
      data: { task: 'Buy milk' },
    });
    expect(response.ok()).toBeTruthy();
    const body: Todo = await response.json();
    expect(body).toHaveProperty('id');
    expect(body.task).toBe('Buy milk');
    expect(body.done).toBe(false);
  });

  test('should list all to-dos', async () => {
    const response: APIResponse = await api.get('/todos');
    expect(response.ok()).toBeTruthy();
    const todos: Todo[] = await response.json();
    expect(Array.isArray(todos)).toBe(true);
    expect(todos.some(todo => todo.id === todoId)).toBe(true);
  });

  test('should update a to-do', async () => {
    const response: APIResponse = await api.put(`/todos/${todoId}`, {
      data: { done: true },
    });
    expect(response.ok()).toBeTruthy();
    const body: Todo = await response.json();
    expect(body.done).toBe(true);
  });

  test('should delete a to-do', async () => {
    const response: APIResponse = await api.delete(`/todos/${todoId}`);
    expect(response.status()).toBe(204);

    // Verify deletion
    const getResponse: APIResponse = await api.get('/todos');
    const todos: Todo[] = await getResponse.json();
    expect(todos.some(todo => todo.id === todoId)).toBe(false);
  });

  // Additional test cases for error conditions
  test('should return 404 when updating non-existent todo', async () => {
    const nonExistentId = 99999;
    const response: APIResponse = await api.put(`/todos/${nonExistentId}`, {
      data: { done: true },
    });
    expect(response.status()).toBe(404);
  });

  test('should return 400 when creating todo without task', async () => {
    const response: APIResponse = await api.post('/todos', {
      data: { },
    });
    expect(response.status()).toBe(400);
  });
}); 