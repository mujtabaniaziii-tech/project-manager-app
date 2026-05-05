import sqlite3
import hashlib

def create_connection():
    return sqlite3.connect('project_manager.db')

# Password secure karne ke liye
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = create_connection()
    c = conn.cursor()
    
    # 1. Users Table (Nayi)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    github_token TEXT
                )''')
                
    # 2. Projects Table (Updated: isme user_id add kiya hai)
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )''')
                
    # 3. Tasks Table
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    task_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                )''')
                
    conn.commit()
    conn.close()

# --- USER AUTHENTICATION FUNCTIONS ---
def add_user(username, password):
    conn = create_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Agar username pehle se mojood ho
    finally:
        conn.close()

def login_user(username, password):
    conn = create_connection()
    c = conn.cursor()
    c.execute('SELECT id, username FROM users WHERE username=? AND password=?', (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user # Return (id, username) agar sahi ho, warna None

def update_github_token(user_id, token):
    conn = create_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET github_token=? WHERE id=?', (token, user_id))
    conn.commit()
    conn.close()

def get_github_token(user_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute('SELECT github_token FROM users WHERE id=?', (user_id,))
    token = c.fetchone()
    conn.close()
    return token[0] if token else None

# --- PROJECT & TASK FUNCTIONS (Updated for Users) ---
def add_project(user_id, name, description, status):
    conn = create_connection()
    c = conn.cursor()
    c.execute('INSERT INTO projects (user_id, name, description, status) VALUES (?, ?, ?, ?)', (user_id, name, description, status))
    conn.commit()
    conn.close()

def view_all_projects(user_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute('SELECT id, name, description, status FROM projects WHERE user_id=?', (user_id,))
    data = c.fetchall()
    conn.close()
    return data

def delete_project(project_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute('PRAGMA foreign_keys = ON')
    c.execute('DELETE FROM projects WHERE id=?', (project_id,))
    conn.commit()
    conn.close()

def add_task(project_id, task_name, status):
    conn = create_connection()
    c = conn.cursor()
    c.execute('INSERT INTO tasks (project_id, task_name, status) VALUES (?, ?, ?)', (project_id, task_name, status))
    conn.commit()
    conn.close()

def view_tasks_by_project(project_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM tasks WHERE project_id=?', (project_id,))
    data = c.fetchall()
    conn.close()
    return data

def get_task_stats(user_id):
    conn = create_connection()
    c = conn.cursor()
    # Har user ke sirf apne tasks count honge
    c.execute('''SELECT tasks.status, COUNT(*) 
                 FROM tasks 
                 JOIN projects ON tasks.project_id = projects.id 
                 WHERE projects.user_id=? 
                 GROUP BY tasks.status''', (user_id,))
    data = c.fetchall()
    conn.close()
    return dict(data)