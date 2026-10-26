import streamlit as st
import google.generativeai as genai
import sqlite3
import os
from database_utils import initialize_db, hash_password, verify_password, save_chat_message, get_chat_history, DB_NAME
from security_utils import generate_entropy_histogram_data
from streamlit_ace import st_ace
import pandas as pd
import plotly.graph_objects as go
from content import COURSE_CONTENT

# --- 1. SINGLE APP CONFIGURATION & INITIALIZATION ---
st.set_page_config(page_title="VaultCode", layout="wide", initial_sidebar_state="collapsed")
initialize_db()

# Configure Google GenAI API Key
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

AVERAGE_BASELINE = 3.01
DANGER_THRESHOLD = 4.50
SHOW_DEBUG = st.secrets.get("SHOW_DEBUG", False)

# --- 2. SESSION STATE INITIALIZATION ---
if "page" not in st.session_state:
    st.session_state.page = "home"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "files" not in st.session_state:
    st.session_state.files = {
        "main.py": "# Welcome to VaultCode\n# Write or paste your secure code here\n\nAPI_KEY = 'AKIAIOSFODNN7EXAMPLE' # Test secret for scanning\n"
    }

if "active_file" not in st.session_state:
    st.session_state.active_file = "main.py"

if "selected_model_alias" not in st.session_state:
    st.session_state.selected_model_alias = 'gemini-3.8-flash'

def set_page(page):
    st.session_state.page = page

# --- 3. PAGES ---

def home_page():
    st.markdown("""
    <style>
        .stApp {
            background-color: #0e1117;
            color: #ffffff;
        }
        div[data-testid="stVerticalBlock"] {
            background-color: #1e1e1e;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
            max-width: 800px;
            margin: 0 auto;
            text-align: center;
        }
        h1 {
            color: #4CAF50;
            font-size: 2.5em;
            margin-bottom: 0.5em;
        }
        p {
            color: #cccccc;
            font-size: 1.1em;
            line-height: 1.6;
            margin-bottom: 2em;
        }
        .stButton > button {
            width: auto;
            padding: 10px 30px;
            border-radius: 20px;
            border: 1px solid #4CAF50;
            color: #ffffff;
            background-color: #4CAF50;
            font-size: 1.2em;
            cursor: pointer;
            display: block;
            margin: 0 auto;
        }
        .stButton > button:hover {
            background-color: #45a049;
            border-color: #45a049;
        }
    </style>
    """, unsafe_allow_html=True)

    icon_col1, icon_col2, icon_col3 = st.columns([1, 1.5, 1])
    with icon_col2:
        st.image("appicon.jpeg", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center;'>" \
                "<h1>VaultCode: AI-powered Secure Coding</h1>" \
                "<p>An interactive AI coding mentor that identifies security risks—like hard-coded API keys—and teaches developers to build safer, production-ready software.</p>" \
                "</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Get Started", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()

def features_guide_page():
    st.markdown("""
        <style>
            .stApp { 
                background-color: #0e1117;
                color: #ffffff;
            }
            div[data-testid="stVerticalBlock"] {
                background-color: #1e1e1e;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
                margin-bottom: 20px;
                border: 1px solid #333;
            }
            h1, h2, h3 { color: #4CAF50; }
        </style>
    """, unsafe_allow_html=True)

    if st.button("⬅️ Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

    st.markdown("<h1>📖 VaultCode Feature Guide</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #cccccc;'>Welcome! Here is a quick breakdown of what each feature does and how to use it.</p>", unsafe_allow_html=True)
    st.markdown("---")

    with st.container():
        st.markdown("### 🔍 Run Security Audit / Code Analysis")
        st.write("Scans your code snippets or uploaded scripts to detect common vulnerabilities, hard-coded API keys, and insecure practices.")

    with st.container():
        st.markdown("### 🤖 Advanced AI Security Mentor (Gemini 3.8 Flash)")
        st.write("Powered by Google's high-performance **Gemini 3.8 Flash** model. It provides deep contextual code analysis, answers your security questions, and acts as an interactive mentor.")

    with st.container():
        st.markdown("### 🔐 Password & Key Entropy Checker")
        st.write("A built-in security tool that calculates password strength and entropy, teaching you cryptographic best practices.")

    with st.container():
        st.markdown("### 💻 Interactive Workspace")
        st.write("An embedded code editor where you can test, write, and interact directly with your AI mentor in real-time.")

    st.markdown("---")
    if st.button("🚀 Return to Dashboard", key="return_dash_bottom"):
        st.session_state.page = "dashboard"
        st.rerun()

def login_page():
    st.markdown("""
        <style>
            [data-testid="stVerticalBlockBorderWrapper"] {
                background-color: #1e1e1e !important;
                border-radius: 15px !important;
                padding: 40px !important;
                box-shadow: 0 8px 24px rgba(0,0,0,0.5) !important;
                border: 1px solid #333 !important;
            }
            div[data-testid="stWidgetLabel"] p {
                font-size: 1.1rem !important;
                font-weight: 600 !important;
                color: #4CAF50 !important;
            }
            .stButton button {
                background-color: #4CAF50 !important;
                color: white !important;
                font-weight: bold !important;
                height: 3.5rem !important;
                border-radius: 10px !important;
                border: none !important;
                margin-top: 20px !important;
                transition: 0.3s;
            }
            .stButton button:hover {
                background-color: #45a049 !important;
                transform: translateY(-2px);
            }
            h1 { color: #4CAF50; text-align: center; margin-bottom: 40px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1>VaultCode AI Mentor</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            mode = st.radio('Authentication Mode', ['Login', 'Sign Up'], key="auth_mode_toggle", horizontal=True, label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True)

            username = st.text_input("Username", key="login_user", placeholder="Enter your username")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="Enter your password")

            if mode == "Sign Up":
                from security_utils import calculate_entropy
                pw_entropy = calculate_entropy(password)
                
                if password:
                    progress_val = min(pw_entropy / 5.0, 1.0)
                    if pw_entropy < 3.5:
                        st.write(f"Strength: 🟠 **{pw_entropy:.2f}** (Target: >3.5)")
                        st.progress(progress_val)
                        st.warning("Password is too weak for a security product.")
                    else:
                        st.write(f"Strength: 🟢 **{pw_entropy:.2f}** (Secure)")
                        st.progress(progress_val)
                        st.success("Strong password detected!")
                else:
                    st.info("💡 Goal: Entropy score > **3.5** (mix cases, numbers, and symbols).")

                if st.button("Create Secure Account", use_container_width=True):
                    if pw_entropy < 3.5:
                        st.error("❌ Minimum security standards not met.")
                    else:
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        c.execute("SELECT * FROM users WHERE username = ?", (username,))
                        if c.fetchone():
                            st.error("Username already taken.")
                        else:
                            hashed, salt = hash_password(password)
                            c.execute("INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)", 
                                      (username, hashed, salt))
                            conn.commit()
                            st.success("✅ Account Created! Now switch to Login mode.")
                        conn.close()

            else:
                if st.button("Sign In to Dashboard", use_container_width=True):
                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    c.execute("SELECT * FROM users WHERE username = ?", (username,))
                    user = c.fetchone()
                    conn.close()
                    
                    if user and verify_password(password, user[1], user[2]):
                        st.session_state.logged_in = True
                        st.session_state.user_id = username
                        st.session_state.messages = get_chat_history(username)
                        st.session_state.page = "dashboard" 
                        st.rerun()
                    else:
                        st.error("Invalid username or password. Please try again.")

def dashboard_page():
    st.markdown("""
        <style>
            .stApp { 
                background-color: #0e1117;
                color: #ffffff;
            }
            .stMetric > div > div:first-child { color: #4CAF50; }
            .stMetric > div > div:nth-child(2) { color: #cccccc; }
            div[data-testid="stVerticalBlock"] {
                background-color: #1e1e1e;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
                margin-bottom: 20px;
            }
            .stButton > button {
                width: 100%;
                border-radius: 15px;
                border: 1px solid #4CAF50;
                color: #ffffff;
                background-color: #4CAF50;
            }
            .stButton > button:hover {
                background-color: #45a049;
                border-color: #45a049;
            }
            h2 { color: #4CAF50; }
        </style>
    """, unsafe_allow_html=True)

    if not st.session_state.logged_in:
        st.warning("Please login to access the dashboard.")
        set_page("login")
        st.rerun()
        return

    st.markdown("<h1 style='color: #4CAF50;'>Dashboard</h1>", unsafe_allow_html=True)

    if SHOW_DEBUG:
        st.write("### Security Points")
        st.metric(label="Total Points", value="1250", delta="50")
    else:
        st.write("### System Status")
        st.success("✅ Security Engine Active & Monitoring")

    col1, col2 = st.columns([1, 1])

    with col1:
        with st.container():
            st.markdown("<h2>New Code Segment</h2>", unsafe_allow_html=True)
            st.write("Start analyzing a new piece of code.")
            st.button("Start New", key="dash_start_new", on_click=set_page, args=("workspace",))

    with col2:
        with st.container():
            st.markdown("<h2>Training Modules</h2>", unsafe_allow_html=True)
            st.write("Enhance your secure coding skills.")
            st.button("Browse Modules", key="dash_browse_training", on_click=set_page, args=("training",))
            
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<h2>ℹ️ Need Help Getting Started?</h2>", unsafe_allow_html=True)
        st.write("New to VaultCode? Learn what each feature, AI model, and security tool does before diving in.")
        if st.button("📖 View Feature Guide", key="dash_feature_guide"):
            st.session_state.page = "features_guide"
            st.rerun()

# --- 4. UNIFIED CHATBOT ENGINE (GEMINI 3.8 FLASH) ---
def render_unified_chatbot(context_label, context_data=""):
    st.markdown("### 🤖 Security & Study Mentor")

    if "hide_history" not in st.session_state:
        st.session_state.hide_history = False

    st.markdown("""
        <style>
            .stButton > button {
                font-size: 12px !important;
                padding: 4px 8px !important;
                border-radius: 5px !important;
                height: auto !important;
                width: auto !important;
            }
        </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.2])
    with col1:
        if st.button("Clear Chat Memory", key=f"permanent_wipe_{context_label}", use_container_width=True):
            st.session_state.messages = []
            st.session_state.hide_history = False
            st.success("Chat history wiped.")
            st.rerun()
    with col2:
        if st.button("Hide History (Memory Saved)", key=f"soft_clear_{context_label}", use_container_width=True):
            st.session_state.messages = []
            st.session_state.hide_history = True
            st.success("Chat view cleared.")
            st.rerun()

    with st.container(height=650, border=True):
        if "messages" not in st.session_state:
            st.session_state.messages = []

        if not st.session_state.hide_history:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    if isinstance(message["content"], list):
                        for part in message["content"]:
                            st.markdown(part.get("text", ""))
                    else:
                        st.markdown(message["content"])
        
        if prompt := st.chat_input(f"Ask your {context_label} mentor..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            try:
                save_chat_message(st.session_state.user_id, "user", prompt)
            except Exception:
                pass # Prevent DB locks from hanging UI
                
            with st.chat_message("user"):
                st.markdown(prompt)

            full_message = f"[{context_label} Context]\n{context_data}\n\nUser Question: {prompt}"
            
            with st.chat_message("assistant"):
                answer = ""
                try:
                    # Direct text generation to prevent streaming/hanging issues
                    model = genai.GenerativeModel(model_name="gemini-3.5-flash-lite")
                    response = model.generate_content(full_message)
                    
                    if response and hasattr(response, 'text') and response.text:
                        answer = response.text
                    else:
                        answer = "⚠️ Received an empty response from the AI model."
                except Exception as e:
                    answer = f"⚠️ Connection or API error occurred: {str(e)}"
                
                st.markdown(answer)
                try:
                    save_chat_message(st.session_state.user_id, "assistant", answer)
                except Exception:
       
                    pass
                    
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun() # Forces clean exit from the loading state

def workspace_page():
    st.markdown("""
        <style>
            .stApp {
                background-color: #0e1117;
                color: #ffffff;
            }
            .stTextArea > label, .stTextInput > label {
                color: #ffffff;
            }
            .stButton > button {
                width: 100%;
                border-radius: 15px;
                border: 1px solid #4CAF50;
                color: #ffffff;
                background-color: #4CAF50;
            }
            .stButton > button:hover {
                background-color: #45a049;
                border-color: #45a049;
            }
            h2, h3 {
                color: #4CAF50;
            }
        </style>
    """, unsafe_allow_html=True)

    if not st.session_state.logged_in:
        st.warning("Please login to access the workspace.")
        set_page("login")
        st.rerun()
        return

    left_col, right_col = st.columns([2, 1], gap="medium")

    with st.sidebar:
        st.markdown("### 🤖 AI Model")
        st.info("Active: **Gemini 3.8 Flash**")
        st.markdown("### 📁 Project Files")

        def set_active_file(filename):
            st.session_state.active_file = filename
            st.rerun()

        for filename in st.session_state.files.keys():
            label = f"📄 {filename}" if filename == st.session_state.active_file else filename
            if st.button(label, key=f"file_button_{filename}", use_container_width=True):
                set_active_file(filename)

        with st.expander("➕ New File", expanded=False):
            new_filename = st.text_input("New filename", key="new_filename_input")
            if st.button("Create File"):
                if new_filename and new_filename not in st.session_state.files:
                    st.session_state.files[new_filename] = ""
                    st.session_state.active_file = new_filename
                    st.rerun()
                elif new_filename:
                    st.error("File already exists.")
                else:
                    st.error("Filename cannot be empty.")

    with left_col:
        st.markdown(f"### 📝 {st.session_state.active_file}")
        editor_state_key = f"editor_state_{st.session_state.active_file}"

        code_content = st_ace(
            value=st.session_state.files.get(st.session_state.active_file, ""), 
            language="python", 
            theme="dracula", 
            height=500, 
            key=editor_state_key,
            auto_update=True  
        )

        if code_content:
            histogram_data = generate_entropy_histogram_data(code_content)
            if histogram_data:
                max_entropy = max(histogram_data)
                if max_entropy > DANGER_THRESHOLD:
                    st.error(f"⚠️ CRITICAL RISK: High-entropy string detected ({max_entropy:.2f} bits).")

        if code_content != st.session_state.files.get(st.session_state.active_file, ""):
            st.session_state.files[st.session_state.active_file] = code_content
            st.caption("✅ Syncing...")
        
        st.write("---")
        if st.button("← Back to Dashboard", type="primary", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

        st.markdown("---")
        st.markdown("### 📊 Security Distribution")

        if st.button("🔍 Run Security Audit", use_container_width=True):
            if code_content:
                st.session_state.histogram_data = generate_entropy_histogram_data(code_content)
                st.session_state.max_entropy = max(st.session_state.histogram_data) if st.session_state.histogram_data else 0.0
            else:
                st.session_state.histogram_data = None
                st.session_state.max_entropy = 0.0
            st.rerun()

        st.caption("(or press CMD+ENTER)")

        if st.session_state.get("histogram_data"):
            df = pd.DataFrame({"Line Number": range(1, len(st.session_state.histogram_data) + 1), "Entropy": st.session_state.histogram_data})
            colors = ["#FF4B4B" if entropy > DANGER_THRESHOLD else "#636EFA" for entropy in df["Entropy"]]
            fig = go.Figure(data=[go.Bar(x=df["Line Number"], y=df["Entropy"], marker_color=colors)])

            fig.add_hline(y=AVERAGE_BASELINE, line_dash="dash", line_color="green", annotation_text=f"Average Baseline ({AVERAGE_BASELINE:.2f})", annotation_position="top right")
            fig.add_hline(y=DANGER_THRESHOLD, line_dash="solid", line_color="red", annotation_text=f"Danger ({DANGER_THRESHOLD:.2f})", annotation_position="top left")

            fig.update_layout(
                xaxis=dict(tickmode='linear', tick0=1, dtick=1, title="Line Number"),
                yaxis_title="Entropy Score",
                font=dict(color="white"),
                margin=dict(l=20, r=20, t=20, b=20)
            )

            st.plotly_chart(fig, use_container_width=True, theme=None)
            st.metric(label="Max Line Entropy", value=f"{st.session_state.max_entropy:.2f}", delta=f"{st.session_state.max_entropy - DANGER_THRESHOLD:.2f}", delta_color="inverse")
        else:
            st.info("Click \"Run Security Audit\" to see entropy distribution.")

    with right_col:
        all_files_content = ""
        for filename, content in st.session_state.files.items():
            all_files_content += f"File: {filename}\n```python\n{content}\n```\n\n"
        render_unified_chatbot("Workspace", all_files_content)

def learning_center():
    st.title("📚 Secure Coding Learning Center")
    st.write("Professional modules on Python security.")
    st.write("---")
    if st.button("← Back to Dashboard", type="primary", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()
        
    col_content, col_chat = st.columns([1.5, 1])

    with col_content:
        for mod_name, lessons in COURSE_CONTENT.items():
            with st.expander(f"📁 {mod_name}"):
                sub_cols = st.columns(2)
                for i, lesson_title in enumerate(lessons.keys()):
                    if sub_cols[i % 2].button(lesson_title, key=f"btn_{lesson_title}", use_container_width=True):
                        st.session_state.active_lesson = (mod_name, lesson_title)

        st.divider()

        if "active_lesson" in st.session_state:
            mod, les = st.session_state.active_lesson
            data = COURSE_CONTENT[mod][les]

            st.header(les)
            st.markdown("### 📖 Lesson Content")
            st.write(data["reading"])
            st.warning(f"🛡️ **Security Mindset:**\n\n{data['security']}")
            
            if st.button("Mark as Complete ✅"):
                st.balloons()

    with col_chat:
        all_files_content = ""
        if "files" in st.session_state:
            for filename, content in st.session_state.files.items():
                all_files_content += f"File: {filename}\n```python\n{content}\n```\n\n"
        render_unified_chatbot("Learning Center", all_files_content)

# --- 5. PAGE ROUTING ROUTER ---
if st.session_state.page == "home":
    home_page()
elif st.session_state.page == "login":
    login_page()
elif st.session_state.page == "dashboard":
    dashboard_page()
elif st.session_state.page == "workspace":
    workspace_page()
elif st.session_state.page == "training": 
    learning_center()
elif st.session_state.page == "features_guide":  
    features_guide_page()    

# Heartbeat to keep connection alive
@st.fragment(run_every=60)
def heartbeat():
    with st.empty():
        pass

heartbeat()