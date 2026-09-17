-- Stage 4: SQL queries to run manually in DB Browser for SQLite
-- Open tasks.db, go to the Execute SQL tab, and run these one at a time.

-- List every task
SELECT * FROM tasks;

-- Show only completed tasks
SELECT * FROM tasks WHERE done = 1;

-- Show only pending tasks
SELECT * FROM tasks WHERE done = 0;

-- Count all tasks
SELECT COUNT(*) FROM tasks;

-- Count completed tasks
SELECT COUNT(*) FROM tasks WHERE done = 1;

-- Search tasks by keyword (case-insensitive)
SELECT * FROM tasks WHERE title LIKE '%grocery%';

-- Mark every task as completed
UPDATE tasks SET done = 1;

-- Mark a single task as pending (replace 1 with the actual id)
UPDATE tasks SET done = 0 WHERE id = 1;

-- Delete all completed tasks
DELETE FROM tasks WHERE done = 1;

-- Delete a single task by id (replace 1 with the actual id)
DELETE FROM tasks WHERE id = 1;
