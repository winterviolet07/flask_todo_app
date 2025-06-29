import { test, expect } from '@playwright/test';
import { Server } from './server';

test.describe('To-Do UI', () => {
  let server: Server;

  // Start server before all tests
  test.beforeAll(async () => {
    server = new Server();
    await server.start();
  });

  // Stop server after all tests
  test.afterAll(async () => {
    await server.stop();
  });

  // Helper function to add a todo through the UI
  async function addTodo(page: any, task: string) {
    await page.fill('input[name="task"]', task);
    await page.click('button[type="submit"]');
    // Wait for the form to reset
    await page.waitForSelector('input[name="task"]');
  }

  test.beforeEach(async ({ page }) => {
    // Reset database before each test
    try {
      const response = await fetch('http://127.0.0.1:5000/reset-db', { method: 'POST' });
      if (!response.ok) {
        console.warn('Failed to reset database, continuing with test');
      }
    } catch (error) {
      console.warn('Could not reset database:', error);
    }
    
    // Navigate to the app before each test
    await page.goto('http://127.0.0.1:5000');
    // Wait for the page to be fully loaded
    await page.waitForLoadState('networkidle');
  });

  test('should display empty todo list initially', async ({ page }) => {
    // Check that the "No tasks yet" message is shown
    await expect(page.locator('.todo-item').filter({ hasText: 'No tasks yet' }).first()).toBeVisible();
    // Verify no todo items are present
    await expect(page.locator('.todo-item:not(:has-text("No tasks yet"))')).toHaveCount(0);
  });

  test('should add a new todo', async ({ page }) => {
    const taskText = 'Buy groceries';
    await addTodo(page, taskText);

    // Wait for the todo to appear
    const todoItem = page.locator('.todo-item').filter({ hasText: taskText }).first();
    await todoItem.waitFor({ state: 'visible' });
    
    // Verify it's not marked as done
    await expect(todoItem).not.toHaveClass(/done/);
  });

  test('should mark todo as done and undo', async ({ page }) => {
    // Add a todo
    const taskText = 'Test task';
    await addTodo(page, taskText);

    // Find the todo item and wait for it
    const todoItem = page.locator('.todo-item').filter({ hasText: taskText }).first();
    await todoItem.waitFor({ state: 'visible' });
    
    // Click "Start" button and wait for the change
    const startButton = todoItem.locator('button:has-text("Start")').first();
    await startButton.click();
    await expect(todoItem).toHaveClass(/in_progress/);
    await expect(todoItem.locator('button:has-text("Complete")').first()).toBeVisible();

    // Click "Complete" button and wait for the change
    const completeButton = todoItem.locator('button:has-text("Complete")').first();
    await completeButton.click();
    await expect(todoItem).toHaveClass(/done/);
    await expect(todoItem.locator('button:has-text("Reset")').first()).toBeVisible();

    // Click "Reset" button and wait for the change
    const resetButton = todoItem.locator('button:has-text("Reset")').first();
    await resetButton.click();
    await expect(todoItem).toHaveClass(/todo/);
    await expect(todoItem.locator('button:has-text("Start")').first()).toBeVisible();
  });

  test('should delete a todo', async ({ page }) => {
    // Add a todo
    const taskText = 'Task to delete';
    await addTodo(page, taskText);

    // Find the todo item and wait for it
    const todoItem = page.locator('.todo-item').filter({ hasText: taskText }).first();
    await todoItem.waitFor({ state: 'visible' });

    // Click delete button and wait for removal
    const deleteButton = todoItem.locator('button:has-text("Delete")').first();
    await deleteButton.click();
    await todoItem.waitFor({ state: 'hidden' });
  });

  test('should not add empty todo', async ({ page }) => {
    // First, delete any existing todos
    const deleteButtons = page.locator('.delete-btn');
    const count = await deleteButtons.count();
    for (let i = 0; i < count; i++) {
      await deleteButtons.first().click();
      // Wait for the delete to complete
      await page.waitForTimeout(500);
    }

    // Verify we have no todos - look for the "No tasks yet" message
    await expect(page.locator('.todo-item').filter({ hasText: 'No tasks yet' })).toBeVisible();

    // Try to submit empty form
    await page.click('button[type="submit"]');
    
    // Wait a moment to ensure no todo was added
    await page.waitForTimeout(1000);

    // Verify no new todo was added - should still show "No tasks yet"
    await expect(page.locator('.todo-item').filter({ hasText: 'No tasks yet' })).toBeVisible();
  });

  test('should add multiple todos', async ({ page }) => {
    const tasks = ['First task', 'Second task', 'Third task'];
    
    // Add multiple todos
    for (const task of tasks) {
      await addTodo(page, task);
      // Wait for the specific todo to be visible
      const todoItem = page.locator('.todo-item').filter({ hasText: task }).first();
      await todoItem.waitFor({ state: 'visible' });
    }

    // Verify correct count by checking each task individually
    for (const task of tasks) {
      await expect(page.locator('.todo-item').filter({ hasText: task })).toHaveCount(1);
    }
  });

  test('should maintain todo state after page refresh', async ({ page }) => {
    // Add a todo
    const taskText = 'Persistent task';
    await addTodo(page, taskText);

    // Find and mark the todo as done
    const todoItem = page.locator('.todo-item').filter({ hasText: taskText }).first();
    await todoItem.waitFor({ state: 'visible' });
    
    // Click Start and Complete buttons to mark as done
    await todoItem.locator('button:has-text("Start")').first().click();
    await todoItem.locator('button:has-text("Complete")').first().click();
    await expect(todoItem).toHaveClass(/done/);

    // Refresh the page and wait for load
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify the todo is still there and marked as done
    const refreshedTodo = page.locator('.todo-item').filter({ hasText: taskText }).first();
    await refreshedTodo.waitFor({ state: 'visible' });
    await expect(refreshedTodo).toHaveClass(/done/);
    await expect(refreshedTodo.locator('button:has-text("Reset")').first()).toBeVisible();
  });

  test('should filter tasks by assignee', async ({ page }) => {
    // Add multiple todos with different assignees
    await addTodo(page, 'Task for John');
    await addTodo(page, 'Task for Jane');
    await addTodo(page, 'Unassigned task');

    // Find the todo items
    const todos = page.locator('.todo-item');
    await expect(todos).toHaveCount(3);

    // Edit the first task to assign to John
    const firstTodo = todos.nth(0);
    await firstTodo.locator('button:has-text("Edit")').click();
    await firstTodo.locator('input[name="assignee"]').fill('John');
    await firstTodo.locator('button:has-text("Update Details")').click();
    
    // Wait for page reload after form submission
    await page.waitForLoadState('networkidle');

    // Edit the second task to assign to Jane
    const secondTodo = todos.nth(1);
    await secondTodo.locator('button:has-text("Edit")').click();
    await secondTodo.locator('input[name="assignee"]').fill('Jane');
    await secondTodo.locator('button:has-text("Update Details")').click();
    
    // Wait for page reload after form submission
    await page.waitForLoadState('networkidle');

    // Wait for assignee filter checkboxes to be created
    await page.waitForSelector('input[type="checkbox"][name="assignee"][value="John"]', { timeout: 5000 });
    await page.waitForSelector('input[type="checkbox"][name="assignee"][value="Jane"]', { timeout: 5000 });

    // Filter for John's tasks
    // Check John's filter and uncheck others
    await page.locator('input[type="checkbox"][name="assignee"][value="John"]').check();
    await page.locator('input[type="checkbox"][name="assignee"][value="Jane"]').uncheck();
    await page.locator('input[type="checkbox"][name="assignee"][value="unassigned"]').uncheck();

    // Dispatch change event to ensure filtering is triggered
    await page.evaluate(() => {
      document.querySelectorAll('input[name="assignee"]').forEach(cb => {
        cb.dispatchEvent(new Event('change', { bubbles: true }));
      });
    });
    await page.waitForTimeout(1000);
    
    // Verify John's filter is checked and others are unchecked
    await expect(page.locator('input[type="checkbox"][name="assignee"][value="John"]')).toBeChecked();
    await expect(page.locator('input[type="checkbox"][name="assignee"][value="Jane"]')).not.toBeChecked();
    await expect(page.locator('input[type="checkbox"][name="assignee"][value="unassigned"]')).not.toBeChecked();
    
    await expect(todos.filter({ hasText: 'Task for John' })).toBeVisible();
    await expect(todos.filter({ hasText: 'Task for Jane' })).not.toBeVisible();
    await expect(todos.filter({ hasText: 'Unassigned task' })).not.toBeVisible();
  });

  test('should handle multiple assignee filters', async ({ page }) => {
    // Add multiple todos with different assignees
    await addTodo(page, 'Task for John');
    await addTodo(page, 'Task for Jane');
    await addTodo(page, 'Unassigned task');

    // Assign tasks
    const todos = page.locator('.todo-item');
    
    // Assign first task to John
    await todos.nth(0).locator('button:has-text("Edit")').click();
    await todos.nth(0).locator('input[name="assignee"]').fill('John');
    await todos.nth(0).locator('button:has-text("Update Details")').click();
    
    // Wait for page reload after form submission
    await page.waitForLoadState('networkidle');

    // Assign second task to Jane
    await todos.nth(1).locator('button:has-text("Edit")').click();
    await todos.nth(1).locator('input[name="assignee"]').fill('Jane');
    await todos.nth(1).locator('button:has-text("Update Details")').click();
    
    // Wait for page reload after form submission
    await page.waitForLoadState('networkidle');

    // Wait for assignee filter checkboxes to be created
    await page.waitForSelector('input[type="checkbox"][name="assignee"][value="John"]', { timeout: 5000 });
    await page.waitForSelector('input[type="checkbox"][name="assignee"][value="Jane"]', { timeout: 5000 });

    // Select both John and Jane filters
    await page.locator('input[type="checkbox"][name="assignee"][value="John"]').check();
    await page.locator('input[type="checkbox"][name="assignee"][value="Jane"]').check();
    await page.locator('input[type="checkbox"][name="assignee"][value="unassigned"]').uncheck();

    // Wait for the UI to update: wait for "Unassigned task" to be hidden
    await expect(page.locator('.todo-item').filter({ hasText: 'Unassigned task' })).not.toBeVisible();

    // Wait for filtering to apply
    await page.waitForTimeout(1000);

    // Verify both John and Jane's tasks are visible
    await expect(todos.filter({ hasText: 'Task for John' })).toBeVisible();
    await expect(todos.filter({ hasText: 'Task for Jane' })).toBeVisible();
    await expect(todos.filter({ hasText: 'Unassigned task' })).not.toBeVisible();

    // Add unassigned filter
    await page.locator('input[type="checkbox"][name="assignee"][value="unassigned"]').click();
    await page.waitForTimeout(500); // Wait for JavaScript filtering to apply

    // Verify all tasks are visible
    await expect(todos.filter({ hasText: 'Task for John' })).toBeVisible();
    await expect(todos.filter({ hasText: 'Task for Jane' })).toBeVisible();
    await expect(todos.filter({ hasText: 'Unassigned task' })).toBeVisible();
  });

  test('should update assignee filter counts when tasks are modified', async ({ page }) => {
    // Add a todo
    await addTodo(page, 'Test task');
    
    // Verify initial unassigned count
    await expect(page.locator('#unassigned-count')).toHaveText('1');

    // Assign the task
    const todo = page.locator('.todo-item').first();
    await todo.locator('button:has-text("Edit")').click();
    await todo.locator('input[name="assignee"]').fill('John');
    await todo.locator('button:has-text("Update Details")').click();
    
    // Wait for page reload after form submission
    await page.waitForLoadState('networkidle');

    // Wait for John filter checkbox to be created
    await page.waitForSelector('input[type="checkbox"][name="assignee"][value="John"]', { timeout: 5000 });

    // Verify counts updated
    await expect(page.locator('#unassigned-count')).toHaveText('0');
    await expect(page.locator('#John-count')).toHaveText('1');

    // Remove assignee
    await todo.locator('button:has-text("Edit")').click();
    await todo.locator('input[name="assignee"]').fill('');
    await todo.locator('button:has-text("Update Details")').click();
    
    // Wait for page reload after form submission
    await page.waitForLoadState('networkidle');

    // Verify counts updated again
    await expect(page.locator('#unassigned-count')).toHaveText('1');
    // The John-count element might be removed when there are no John tasks, so check if it exists
    const johnCount = page.locator('#John-count');
    if (await johnCount.count() > 0) {
      await expect(johnCount).toHaveText('0');
    }
  });
}); 