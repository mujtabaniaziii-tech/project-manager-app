import sqlite3

# Connect to the SQLite database (it will create the file if it doesn't exist)
def create_connection():
    conn = sqlite3.connect('project_manager.db', check_same_thread=False)
    return conn

# Create the tables for Projects and Tasks
def init_db():
    conn = create_connection()
    c = conn.cursor()
    
    # Create Projects Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT
        )
    ''')
    
    # Create Tasks Table (We will use this later)
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            task_name TEXT NOT NULL,
            status TEXT,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Function to add a new project
def add_project(name, description, status):
    conn = create_connection()
    c = conn.cursor()
    c.execute('INSERT INTO projects (name, description, status) VALUES (?, ?, ?)', (name, description, status))
    conn.commit()
    conn.close()

# Function to view all projects
def view_all_projects():
    conn = create_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM projects')
    data = c.fetchall()
    conn.close()
    return data
# Function to delete a project
def delete_project(project_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute('DELETE FROM projects WHERE id = ?', (project_id,))
    conn.commit()
    conn.close()
# --- TASK FUNCTIONS ---

# Naya task add karne ke liye
def add_task(project_id, task_name, status):
    conn = create_connection()
    c = conn.cursor()
    c.execute('INSERT INTO tasks (project_id, task_name, status) VALUES (?, ?, ?)', (project_id, task_name, status))
    conn.commit()
    conn.close()

# Kisi specific project ke tasks dekhne ke liye
def view_tasks_by_project(project_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM tasks WHERE project_id = ?', (project_id,))
    data = c.fetchall()
    conn.close()
    return data
# --- ANALYTICS FUNCTION ---
def get_task_stats():
    conn = create_connection()
    c = conn.cursor()
    c.execute('SELECT status, COUNT(*) FROM tasks GROUP BY status')
    data = c.fetchall()
    conn.close()
    return dict(data) # Yeh dictionary return karega jaise {'To-Do': 2, 'Done': 1}