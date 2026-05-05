import streamlit as st
import pandas as pd
import database as db
import requests

# --- PAGE CONFIG ---
st.set_page_config(page_title="Project Manager Pro", page_icon="🚀", layout="wide")

# --- CUSTOM UI (Glassmorphism & Animated BG) ---
def inject_custom_css():
    st.markdown("""
    <style>
    /* Animated Moving Background */
    .stApp {
        background: linear-gradient(-45deg, #1e3b2b, #0d1a12, #2c523d, #000000);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
    }
    
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Glassmorphism Effect for Forms (Login/Signup/Add Project) */
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 30px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
    }
    
    /* Neon Green Button Styling */
    div[data-testid="stForm"] button {
        background-color: #7ce38b !important;
        color: #000000 !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        border: none !important;
        transition: 0.3s !important;
    }
    
    div[data-testid="stForm"] button:hover {
        box-shadow: 0 0 15px #7ce38b !important;
        transform: scale(1.02);
    }
    </style>
    """, unsafe_allow_html=True)

# CSS ko apply karein
inject_custom_css()

# --- INITIALIZE DATABASE ---
db.init_db()

# --- INITIALIZE SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = ""

# --- GITHUB API FUNCTIONS ---
def fetch_recent_github_repos(token):
    if not token:
        return None, "GitHub Token missing! Please add it in Settings."
        
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

def fetch_recent_commits(repo_full_name, token):
    if not token:
        return []
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/repos/{repo_full_name}/commits?per_page=3"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# --- AUTHENTICATION (Login / Sign Up) ---
def auth_screen():
    st.title("🔐 Project Manager Pro")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login to your account")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")
            
            if submit_login:
                user = db.login_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.session_state.username = user[1]
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password.")
                    
    with tab2:
        st.subheader("Create a new account")
        with st.form("signup_form"):
            new_username = st.text_input("Choose a Username")
            new_password = st.text_input("Choose a Password", type="password")
            submit_signup = st.form_submit_button("Sign Up")
            
            if submit_signup:
                if new_username and len(new_password) >= 4:
                    if db.add_user(new_username, new_password):
                        st.success("Account created successfully! You can now login.")
                    else:
                        st.error("Username already exists! Choose another one.")
                else:
                    st.warning("Please provide a username and a password (min 4 chars).")

# --- MAIN APP UI ---
def main_dashboard():
    st.sidebar.title("🛠 Project Manager")
    st.sidebar.write(f"Welcome, **{st.session_state.username}** 👋")
    
    page = st.sidebar.radio("Navigation", ["🏠 Dashboard", "📂 My Projects", "⚙️ Settings"])
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = ""
        st.rerun()

    # --- DASHBOARD PAGE ---
    if page == "🏠 Dashboard":
        st.header(f"Welcome back, {st.session_state.username}! 🚀")
        
        projects = db.view_all_projects(st.session_state.user_id)
        task_stats = db.get_task_stats(st.session_state.user_id)
        pending_tasks = task_stats.get("To-Do", 0) + task_stats.get("In-Progress", 0)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Your Active Projects", len(projects))
        col2.metric("Your Pending Tasks", pending_tasks) 
        col3.metric("System Status", "Online 🟢") 
        
        st.divider()
        
        st.subheader("📊 Task Progress Analytics")
        if task_stats:
            df_chart = pd.DataFrame(list(task_stats.items()), columns=["Status", "Count"])
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                st.bar_chart(df_chart.set_index("Status"), color="#7ce38b")
            with chart_col2:
                st.dataframe(df_chart, hide_index=True, use_container_width=True)
        else:
            st.info("No tasks added yet. Add tasks in 'My Projects'!")
            
        st.divider()
        
        st.subheader("🐙 Your Recent GitHub Activity")
        user_token = db.get_github_token(st.session_state.user_id)
        
        if not user_token:
            st.warning("⚠️ You haven't added your GitHub Token yet. Go to **Settings** to add it.")
        else:
            with st.spinner("Fetching your live data from GitHub..."):
                repos, error = fetch_recent_github_repos(user_token)
                
                if error:
                    st.error(error)
                elif repos:
                    for repo in repos:
                        with st.expander(f"📦 {repo.get('name')} (Updated: {repo.get('updated_at').split('T')[0]})"):
                            repo_url = repo.get("html_url", "#")
                            repo_full_name = repo.get("full_name")
                            st.markdown(f"**[Open Repository]({repo_url})**")
                            
                            commits = fetch_recent_commits(repo_full_name, user_token)
                            if commits:
                                for commit in commits:
                                    msg = commit.get("commit", {}).get("message", "No message")
                                    date = commit.get("commit", {}).get("author", {}).get("date", "").split("T")[0]
                                    st.caption(f"🔧 `{date}`: {msg[:80]}...")
                else:
                    st.info("No repositories found.")
        
    # --- MY PROJECTS PAGE ---
    elif page == "📂 My Projects":
        st.header("📂 Your Projects")
        
        with st.expander("➕ Add New Project"):
            with st.form("add_project_form", clear_on_submit=True):
                p_name = st.text_input("Project Name")
                p_desc = st.text_area("Description")
                p_status = st.selectbox("Status", ["Active", "On Hold", "Completed"])
                if st.form_submit_button("Save Project") and p_name:
                    db.add_project(st.session_state.user_id, p_name, p_desc, p_status)
                    st.success("Project added!")
                    st.rerun()

        st.divider()
        projects = db.view_all_projects(st.session_state.user_id)
        
        if projects:
            df = pd.DataFrame(projects, columns=["ID", "Project Name", "Description", "Status"])
            st.dataframe(df, hide_index=True, use_container_width=True)
            
            project_options = {f"ID: {p[0]} - {p[1]}": p[0] for p in projects}
            selected_project_for_tasks = st.selectbox("Select Project to manage tasks:", list(project_options.keys()))
            selected_project_id = project_options[selected_project_for_tasks]

            col1, col2 = st.columns([1, 2])
            with col1:
                with st.form("add_task_form", clear_on_submit=True):
                    task_name = st.text_input("New Task Name")
                    task_status = st.selectbox("Task Status", ["To-Do", "In-Progress", "Done"])
                    if st.form_submit_button("Add Task") and task_name:
                        db.add_task(selected_project_id, task_name, task_status)
                        st.success("Task Added!")
                        st.rerun()

            with col2:
                tasks = db.view_tasks_by_project(selected_project_id)
                if tasks:
                    df_tasks = pd.DataFrame(tasks, columns=["Task ID", "Project ID", "Task Name", "Status"])
                    st.dataframe(df_tasks.drop(columns=["Project ID"]), hide_index=True, use_container_width=True)
                else:
                    st.info("No tasks for this project yet.")

    # --- SETTINGS PAGE ---
    elif page == "⚙️ Settings":
        st.header("⚙️ Account Settings")
        st.write("Manage your API keys here.")
        
        current_token = db.get_github_token(st.session_state.user_id)
        
        with st.form("token_form"):
            new_token = st.text_input("GitHub Personal Access Token", value=current_token if current_token else "", type="password")
            st.caption("Don't worry, this token is saved securely in your personal account.")
            
            if st.form_submit_button("Save Token"):
                db.update_github_token(st.session_state.user_id, new_token)
                st.success("GitHub Token updated successfully!")
                st.rerun()

# --- APP EXECUTION ---
if not st.session_state.logged_in:
    auth_screen()
else:
    main_dashboard()