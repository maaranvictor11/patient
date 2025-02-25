import streamlit as st
import sqlite3
import bcrypt
from datetime import datetime
import os
import re

# Ensure the denied_documents folder exists
if not os.path.exists("denied_documents"):
    os.makedirs("denied_documents")

# Initialize the main user database
def init_db():
    conn = sqlite3.connect('patient_helpdesk.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            patient_id TEXT,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database for AI Policy Inquiry
def init_policy_db():
    conn = sqlite3.connect('policy_inquiries.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS policy_inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            mobile_number TEXT NOT NULL,
            dob TEXT NOT NULL,
            place TEXT NOT NULL,
            insurance_policy TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database for Denied Inquiry with document_path column
def init_denied_db():
    conn = sqlite3.connect('denied_inquiries.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS denied_inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            policy_id TEXT NOT NULL,
            policy_name TEXT NOT NULL,
            denial_reason TEXT NOT NULL,
            document_path TEXT,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()
init_policy_db()
init_denied_db()

# Helper functions for user authentication
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def save_user(full_name, email, patient_id, password):
    conn = sqlite3.connect('patient_helpdesk.db')
    c = conn.cursor()
    hashed_password = hash_password(password)
    try:
        c.execute('''
            INSERT INTO users (full_name, email, patient_id, password)
            VALUES (?, ?, ?, ?)
        ''', (full_name, email, patient_id, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        st.error("Email already exists.")
    finally:
        conn.close()

def get_user(email, password):
    conn = sqlite3.connect('patient_helpdesk.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    if user and check_password(password, user[4]):  # user[4] is the password field
        return user
    return None

# Grok-like chatbot response function
def grok_response(user_input, chat_history):
    user_input = user_input.lower().strip()
    
    # Greetings
    if re.search(r"(hi|hello|hey|greetings)", user_input):
        return "Greetings, human! I’m your trusty Patient Assistant, here to help with a dash of cosmic curiosity. How can I assist you today? 🌌"
    
    # Health-related queries
    elif re.search(r"(health|symptom|sick|doctor)", user_input):
        return "Sounds like you’re pondering the mysteries of the human body! Tell me more—symptoms, questions, or something specific? I’ll do my best to enlighten you! 🩺"
    
    # Insurance-related queries
    elif re.search(r"(insurance|policy|denied|claim)", user_input):
        if "denied" in user_input:
            return "Oh no, a denial! Fear not, I’m here to help. Want to check a denied inquiry or need tips on what might’ve gone wrong? 📜"
        return "Insurance, huh? A labyrinth of paperwork! Are you asking about a policy, a claim, or something else? Let’s unravel it together! 💸"
    
    # Helpdesk support
    elif re.search(r"(help|support|assist)", user_input):
        return "Help is my middle name—well, not really, but I’m here for it! What’s on your mind? Forms, inquiries, or just a chat? 🤝"
    
    # Farewell
    elif re.search(r"(bye|goodbye|exit|log out)", user_input):
        return "Farewell, traveler! If you need me again, I’ll be floating in the digital ether. Stay curious! 🚀"
    
    # Check previous context
    if chat_history and len(chat_history) > 1:
        last_user_msg = chat_history[-2]["content"].lower() if chat_history[-2]["role"] == "user" else ""
        if "more" in user_input and "symptom" in last_user_msg:
            return "More symptoms, eh? Spill the beans—what else are you feeling? I’ll try to connect the dots! 🔍"
        if "yes" in user_input and "denied" in last_user_msg:
            return "Alright, let’s dig into that denial. Got a patient ID or policy ID handy? I can guide you through the form! 🕵️‍♂️"

    # Default response
    return "Hmm, I’m picking up signals, but I need a bit more to lock on! Could you clarify—health, insurance, or something else? I’m all ears (or rather, all text)! 🌟"

# Session state to track login and chat
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'page_state' not in st.session_state:
    st.session_state.page_state = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# App title and description with emoji
st.title("Patient Helpdesk Assistance 🌟")
st.markdown("Welcome to the Patient Helpdesk! 👋 Log in or sign up to get started.")

# Sidebar navigation (only show if not logged in)
if not st.session_state.logged_in:
    page = st.sidebar.selectbox("Choose a page", ["Login", "Signup"])
else:
    page = "Homepage"

# Login Page
if page == "Login" and not st.session_state.logged_in:
    st.header("Login to Patient Helpdesk 🔑")
    st.write("Enter your credentials to access support. ✨")

    with st.form(key="login_form"):
        username = st.text_input("Username or Email 📧")
        password = st.text_input("Password 🔒", type="password")
        submit_button = st.form_submit_button(label="Login 🚀")

    if submit_button:
        if username and password:
            user = get_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_email = username
                st.success(f"Welcome back, {user[1]}! 🎉")
                st.rerun()
            else:
                st.error("Invalid email or password. ❌")
        else:
            st.error("Please fill in all fields. ⚠️")

# Signup Page
elif page == "Signup" and not st.session_state.logged_in:
    st.header("Sign Up for Patient Helpdesk ✍️")
    st.write("Create an account to access personalized assistance. 🌈")

    with st.form(key="signup_form"):
        full_name = st.text_input("Full Name 👤")
        email = st.text_input("Email 📧")
        patient_id = st.text_input("Patient ID (optional) 🏥")
        new_password = st.text_input("Password 🔒", type="password")
        confirm_password = st.text_input("Confirm Password 🔐", type="password")
        submit_button = st.form_submit_button(label="Sign Up 🌟")

    if submit_button:
        if not all([full_name, email, new_password, confirm_password]):
            st.error("Please fill in all required fields. ⚠️")
        elif new_password != confirm_password:
            st.error("Passwords do not match. ❌")
        else:
            save_user(full_name, email, patient_id, new_password)
            st.success(f"Account created for {full_name}! Please log in. ✅")

# Homepage
elif page == "Homepage" and st.session_state.logged_in:
    # Custom CSS for dark theme, enhanced styling, and chatbot
    st.markdown("""
        <style>
            .stApp {
                background-color: #2b2d42;
                color: #edf2f4;
            }
            .stButton>button {
                background-color: #ef233c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                margin: 5px;
                font-weight: bold;
                transition: background-color 0.3s;
            }
            .stButton>button:hover {
                background-color: #d90429;
            }
            .stHeader {
                color: #8d99ae;
                font-size: 28px;
                font-family: 'Arial', sans-serif;
            }
            .sidebar .stButton>button {
                background-color: #48cae4;
            }
            .sidebar .stButton>button:hover {
                background-color: #0096c7;
            }
            .logout-button {
                position: fixed;
                bottom: 10px;
                left: 10px;
                width: 200px;
            }
            .chatbot-container {
                position: fixed;
                bottom: 10px;
                right: 10px;
                width: 320px;
                max-height: 400px;
                background-color: #3a3f5b;
                border-radius: 10px;
                padding: 10px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                z-index: 1000;
                overflow-y: auto;
            }
            .chat-message {
                background-color: #48cae4;
                color: white;
                border-radius: 8px;
                padding: 8px;
                margin: 5px 0;
                max-width: 80%;
                word-wrap: break-word;
            }
            .user-message {
                background-color: #ef233c;
                margin-left: auto;
            }
            .chat-input-container {
                position: sticky;
                bottom: 0;
                background-color: #3a3f5b;
                padding: 5px;
            }
            .chat-input {
                width: 100%;
                background-color: #edf2f4;
                border: none;
                border-radius: 5px;
                padding: 5px;
                color: #2b2d42;
            }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar layout with Back to Home and Log Out buttons
    st.sidebar.markdown("---")
    if st.sidebar.button("🏠 Back to Home"):
        st.session_state.page_state = None  # Reset to homepage

    st.header(f"Patient Helpdesk Assistant – Hi, {st.session_state.user_email.split('@')[0]}! 👋")
    if st.session_state.page_state is None:
        st.write("Select an option below to proceed: 🚀")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("AI Policy Inquiry 📝"):
                st.session_state.page_state = "policy_inquiry"
        with col2:
            if st.button("Denied Inquiry 🚫"):
                st.session_state.page_state = "denied_inquiry"

    # AI Policy Inquiry Form
    if st.session_state.page_state == "policy_inquiry":
        st.subheader("AI Policy Inquiry 📋")
        with st.form(key="policy_form"):
            name = st.text_input("Name 👤")
            age = st.number_input("Age 🎂", min_value=0, max_value=150)
            gender = st.selectbox("Gender 🚻", ["Male", "Female", "Other"])
            mobile_number = st.text_input("Mobile Number 📱")
            dob = st.date_input("Date of Birth 🗓️")
            place = st.text_input("Place 🌍")
            insurance_policy = st.text_area("About Insurance Policy 📜")
            submit_button = st.form_submit_button(label="Submit ✅")

            if submit_button:
                if all([name, age, gender, mobile_number, dob, place, insurance_policy]):
                    policy_type = "Basic Health Insurance" if age < 30 else "Comprehensive Health Insurance"
                    st.success(f"Recommended Insurance Policy: {policy_type} 🎉")
                    conn = sqlite3.connect('policy_inquiries.db')
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO policy_inquiries (name, age, gender, mobile_number, dob, place, insurance_policy, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (name, age, gender, mobile_number, str(dob), place, insurance_policy, str(datetime.now())))
                    conn.commit()
                    conn.close()
                else:
                    st.error("Please fill in all fields. ⚠️")

    # Denied Inquiry Form with Document Attachment
    elif st.session_state.page_state == "denied_inquiry":
        st.subheader("Denied Inquiry 🚫")
        with st.form(key="denied_form"):
            patient_name = st.text_input("Patient Name 👤")
            patient_id = st.text_input("Patient ID 🏥")
            policy_id = st.text_input("Policy ID #️⃣")
            policy_name = st.text_input("Policy Name 📜")
            document = st.file_uploader("Attach Document 📎 (e.g., PDF, Image)", type=["pdf", "png", "jpg", "txt"])
            submit_button = st.form_submit_button(label="Submit ✅")

            if submit_button:
                if all([patient_name, patient_id, policy_id, policy_name]):
                    denial_reason = "Insufficient documentation" if len(patient_id) < 5 else "Policy expired"
                    document_path = None
                    if document:
                        document_path = f"denied_documents/{patient_id}_{policy_id}_{document.name}"
                        with open(document_path, "wb") as f:
                            f.write(document.getbuffer())
                        st.success(f"Document '{document.name}' uploaded successfully! ✅")

                    st.warning(f"Reason for Denial: {denial_reason} ⚠️")
                    conn = sqlite3.connect('denied_inquiries.db')
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO denied_inquiries (patient_name, patient_id, policy_id, policy_name, denial_reason, document_path, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (patient_name, patient_id, policy_id, policy_name, denial_reason, document_path, str(datetime.now())))
                    conn.commit()
                    conn.close()
                else:
                    st.error("Please fill in all required fields. ⚠️")

    # Log Out button at bottom-left of sidebar
    st.sidebar.markdown('<div class="logout-button">', unsafe_allow_html=True)
    if st.sidebar.button("🚪 Log Out"):
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.session_state.page_state = None
        st.session_state.chat_history = []
        st.rerun()
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    st.sidebar.write("Patient Helpdesk Assistance © 2025 🌟")

    # Chatbot at bottom-right with Grok-like interaction
    with st.container():
        st.markdown('<div class="chatbot-container">', unsafe_allow_html=True)
        st.markdown("🤖 **Patient Assistant Chat**")
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(f'<div class="chat-message user-message">{message["content"]} 👤</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message">{message["content"]} 🤖</div>', unsafe_allow_html=True)

        # Chat input with form to handle submission
        with st.form(key="chat_form", clear_on_submit=True):
            chat_input = st.text_input("Ask me anything! 💬", placeholder="Type here...", key="chat_input_unique")
            submit_chat = st.form_submit_button(label="Send 📤")
            if submit_chat and chat_input:
                st.session_state.chat_history.append({"role": "user", "content": chat_input})
                bot_response = grok_response(chat_input, st.session_state.chat_history)
                st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# Footer (only for non-logged-in pages)
if not st.session_state.logged_in:
    st.sidebar.markdown("---")
    st.sidebar.write("Patient Helpdesk Assistance © 2025 🌟")
