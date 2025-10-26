import sys
from pathlib import Path

import streamlit as st

_SRC_DIR = Path(__file__).resolve().parents[1]
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from app.storage import signup, login, get_user, list_workouts, update_user
from app.workout import run_workout


st.set_page_config(page_title="AI Gym Trainer", page_icon="🏋️", layout="wide")


def ensure_session():
    if "auth_user" not in st.session_state:
        st.session_state["auth_user"] = None


def show_auth():
    tabs = st.tabs(["Login", "Sign up"])
    with tabs[0]:
        st.subheader("Login")
        username = st.text_input("Email", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if login(username, password):
                st.session_state["auth_user"] = username
                st.success("Logged in")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")
    with tabs[1]:
        st.subheader("Sign up")
        username = st.text_input("Email", key="signup_user")
        full_name = st.text_input("Full name")
        password = st.text_input("Password", type="password", key="signup_pass")
        if st.button("Create account"):
            if signup(username, password, full_name):
                st.success("Account created. Please log in.")
            else:
                st.warning("User already exists")


def show_dashboard():
    st.sidebar.title("AI Gym Trainer")
    st.sidebar.write(f"Signed in as: {st.session_state['auth_user']}")
    if st.sidebar.button("Log out"):
        st.session_state["auth_user"] = None
        st.experimental_rerun()

    page = st.sidebar.radio("Navigate", ["Dashboard", "Workout", "Profile"]) 

    if page == "Dashboard":
        st.title("Dashboard")
        st.write("Choose an exercise to start coaching or review your history.")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Start a workout")
            ex = st.selectbox("Exercise", ["push-up", "squat", "sit-up", "walk"]) 
            if st.button("Start now"):
                st.session_state["nav_to"] = ("Workout", ex)
                st.experimental_rerun()
        with col2:
            st.subheader("Your last workouts")
            rows = list_workouts(st.session_state["auth_user"]) or []
            for w in rows[-5:][::-1]:
                st.write(f"{w['exercise']}: {w['reps']} reps, form {w['form_score']}%")

    elif page == "Workout":
        preset = None
        if st.session_state.get("nav_to"):
            _, preset = st.session_state.pop("nav_to")
        run_workout(st.session_state["auth_user"], preset)

    elif page == "Profile":
        st.title("Profile")
        user = get_user(st.session_state["auth_user"]) or {}
        with st.form("profile_form"):
            full_name = st.text_input("Full name", value=user.get("full_name", ""))
            level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"], index=["Beginner", "Intermediate", "Advanced"].index(user.get("level", "Beginner")))
            age = st.number_input("Age", min_value=0, value=int(user.get("age") or 0))
            height_cm = st.number_input("Height (cm)", min_value=0, value=int(user.get("height_cm") or 0))
            weight_kg = st.number_input("Weight (kg)", min_value=0, value=int(user.get("weight_kg") or 0))
            submitted = st.form_submit_button("Save")
        if submitted:
            update_user(st.session_state["auth_user"], {
                "full_name": full_name,
                "level": level,
                "age": int(age) if age else None,
                "height_cm": int(height_cm) if height_cm else None,
                "weight_kg": int(weight_kg) if weight_kg else None,
            })
            st.success("Profile saved")


def main():
    ensure_session()
    if not st.session_state["auth_user"]:
        show_auth()
    else:
        show_dashboard()


if __name__ == "__main__":
    main()








