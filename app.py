import streamlit as st
import pandas as pd
import database as db
import requests
import os
from dotenv import load_dotenv

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()

# --- PAGE CONFIG ---
st.set_page_config(page_title="Project Manager Pro", page_icon="🚀", layout="wide")

# --- INITIALIZE DATABASE ---
db.init_db()

# --- INITIALIZE SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- GITHUB API FUNCTIONS ---
def fetch_recent_github_repos():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return None, "GitHub Token missing in .env file!"
        
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    url = "https://api.github.com/user/repos?sort=updated&per_page=5"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"GitHub API Error: {response.status_code}"
    except Exception as e:
        return None, f"Connection Error: {str(e)}"

# NAYA FUNCTION: Commits fetch karne ke liye
def fetch_recent_commits(repo_full_name):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return []
        
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/repos/{repo_full_name}/commits?per_page=3" # Sirf aakhri 3 commits
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# --- LOGIN FUNCTION ---
def login():
    st.title("🔐 Login to Project Manager")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if username == "admin" and password == "1234":
                st.session_state.logged_in = True
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid credentials (Hint: admin/1234)")

# --- LOGOUT FUNCTION ---
def logout():
    st.session_state.logged_in = False
    st.rerun()

# --- MAIN APP UI ---
def main_dashboard():
    st.sidebar.title("🛠 Project Manager")
    st.sidebar.write(f"Logged in as: **Admin**")
    
    page = st.sidebar.radio("Go to", ["🏠 Dashboard", "📂 My Projects", "⚙️ Settings"])
    
    if st.sidebar.button("Logout"):
        logout()

    # --- DASHBOARD PAGE ---
    if page == "🏠 Dashboard":
        st.header("Welcome back, Mujtaba! 🚀")
        st.write("Here is the live overview of your local projects and GitHub activity.")
        
        projects = db.view_all_projects()
        total_projects = len(projects)
        task_stats = db.get_task_stats()
        pending_tasks = task_stats.get("To-Do", 0) + task_stats.get("In-Progress", 0)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Local Active Projects", total_projects)
        col2.metric("Pending Tasks", pending_tasks) 
        col3.metric("System Status", "Online 🟢") 
        
        st.divider()
        
        st.subheader("📊 Task Progress Analytics")
        if task_stats:
            df_chart = pd.DataFrame(list(task_stats.items()), columns=["Status", "Count"])
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                st.write("**Tasks by Status**")
                st.bar_chart(df_chart.set_index("Status"), color="#3498db")
            with chart_col2:
                st.write("**Quick Breakdown**")
                st.dataframe(df_chart, hide_index=True, use_container_width=True)
        else:
            st.info("No tasks added yet. Add tasks in 'My Projects' to see analytics here!")
            
        st.divider()
        
        # --- GITHUB LIVE FEED (UPDATED WITH COMMITS) ---
        st.subheader("🐙 Recent GitHub Activity")
        
        with st.spinner("Fetching live data and commits from GitHub..."):
            repos, error = fetch_recent_github_repos()
            
            if error:
                st.error(error)
            elif repos:
                st.success("GitHub Connection Successful!")
                for repo in repos:
                    # Har repo ke liye ek box banayenge
                    with st.expander(f"📦 {repo.get('name')} (Updated: {repo.get('updated_at').split('T')[0]})", expanded=True):
                        repo_url = repo.get("html_url", "#")
                        repo_full_name = repo.get("full_name") # Owner/Repo name needed for commits
                        
                        st.markdown(f"**[Open Repository on GitHub]({repo_url})**")
                        
                        # Commits fetch karna
                        commits = fetch_recent_commits(repo_full_name)
                        if commits:
                            st.write("*Recent Commits:*")
                            for commit in commits:
                                msg = commit.get("commit", {}).get("message", "No message")
                                date = commit.get("commit", {}).get("author", {}).get("date", "").split("T")[0]
                                # Agar message bohot lamba ho toh usko chota kar diya
                                st.caption(f"🔧 `{date}`: {msg[:80]}...")
                        else:
                            st.caption("No recent commits found or repository is empty.")
            else:
                st.info("No repositories found on your GitHub account.")
        
    # --- MY PROJECTS PAGE ---
    elif page == "📂 My Projects":
        st.header("📂 Your Projects")
        
        with st.expander("➕ Add New Project"):
            with st.form("add_project_form", clear_on_submit=True):
                p_name = st.text_input("Project Name")
                p_desc = st.text_area("Description")
                p_status = st.selectbox("Status", ["Active", "On Hold", "Completed"])
                submit_project = st.form_submit_button("Save Project")
                
                if submit_project:
                    if p_name:
                        db.add_project(p_name, p_desc, p_status)
                        st.success(f"Project '{p_name}' added to database!")
                        st.rerun() 
                    else:
                        st.error("Project Name is required.")

        st.divider()

        st.subheader("Current Projects")
        projects = db.view_all_projects()
        
        if projects:
            df = pd.DataFrame(projects, columns=["ID", "Project Name", "Description", "Status"])
            st.dataframe(df, hide_index=True, use_container_width=True)
            
            st.divider()
            
            st.subheader("🗑️ Delete a Project")
            project_options = {f"ID: {p[0]} - {p[1]}": p[0] for p in projects}
            
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_project_to_delete = st.selectbox("Select a project to delete:", list(project_options.keys()))
            with col2:
                st.write("") 
                st.write("")
                if st.button("Delete Project", type="primary"):
                    project_id_to_delete = project_options[selected_project_to_delete]
                    db.delete_project(project_id_to_delete)
                    st.success("Project deleted successfully!")
                    st.rerun() 
                    
            st.divider()
            
            st.subheader("📝 Manage Project Tasks")
            selected_project_for_tasks = st.selectbox("Select Project to view/add tasks:", list(project_options.keys()), key="task_project_select")
            selected_project_id = project_options[selected_project_for_tasks]

            col3, col4 = st.columns([1, 2])
            with col3:
                with st.form("add_task_form", clear_on_submit=True):
                    task_name = st.text_input("New Task Name")
                    task_status = st.selectbox("Task Status", ["To-Do", "In-Progress", "Done"])
                    submit_task = st.form_submit_button("Add Task")
                    
                    if submit_task:
                        if task_name:
                            db.add_task(selected_project_id, task_name, task_status)
                            st.success("Task Added!")
                            st.rerun()
                        else:
                            st.error("Task name cannot be empty.")

            with col4:
                tasks = db.view_tasks_by_project(selected_project_id)
                if tasks:
                    df_tasks = pd.DataFrame(tasks, columns=["Task ID", "Project ID", "Task Name", "Status"])
                    st.dataframe(df_tasks.drop(columns=["Project ID"]), hide_index=True, use_container_width=True)
                else:
                    st.info("No tasks yet for this project. Add one from the left!")

        else:
            st.info("No projects found. Create your first project above!")

    # --- SETTINGS PAGE ---
    elif page == "⚙️ Settings":
        st.header("⚙️ Settings")
        st.info("Update your environment variables in the `.env` file to change GitHub settings.")

# --- APP EXECUTION ---
if not st.session_state.logged_in:
    login()
else:
    main_dashboard()