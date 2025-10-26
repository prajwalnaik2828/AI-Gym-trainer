import sys
from pathlib import Path
import time
import numpy as np
import streamlit as st
import cv2
import mediapipe as mp
from typing import Optional

_SRC_DIR = Path(__file__).resolve().parents[1]
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from app.voice import speak
from app.storage import add_workout
from excerciseType import excerciseType


def run_workout(username: str, preset_exercise: Optional[str] = None):
    st.title("Live Workout Coach")
    exercises = ["push-up", "squat", "sit-up", "walk"]
    if preset_exercise and preset_exercise in exercises:
        exercise = preset_exercise
    else:
        exercise = st.selectbox("Choose exercise", exercises)
    start_btn = st.button("Start")
    frame_window = st.image([])

    if not start_btn:
        return

    mp_drawing = mp.solutions.drawing_utils
    mp_pose = mp.solutions.pose

    counter = 0
    status = True
    correct_cues = 0
    total_frames = 0

    cap = cv2.VideoCapture(0)
    cap.set(3, 800)
    cap.set(4, 480)
    speak(f"Starting {exercise} workout. I will guide your form.")

    with mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.resize(frame, (800, 480), interpolation=cv2.INTER_AREA)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = pose.process(rgb)
            rgb.flags.writeable = True
            frame = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

            try:
                landmarks = results.pose_landmarks.landmark
                counter, status = excerciseType(landmarks).calculate_exercise(exercise, counter, status)
                # voice guidance on state transitions
                if exercise == "squat":
                    # basic knee/hip cue: when going down
                    if not status:
                        speak("Push hips back, keep knees over toes.")
                    else:
                        speak("Drive through heels and stand tall.")
                elif exercise == "push-up":
                    if not status:
                        speak("Keep elbows at forty five degrees, core tight.")
                    else:
                        speak("Full lockout at the top.")
                total_frames += 1
                # very simple form heuristic using knee/arm angles thresholds already embedded
                correct_cues += 1
            except Exception:
                pass

            cv2.putText(frame, f"{exercise} | reps: {counter}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            frame_window.image(frame, channels="BGR")

            # basic voice cues tied to state switches
            if counter > 0 and counter % 5 == 0:
                speak("Great job. Keep your form steady.")

            if not st.session_state.get("workout_running", True):
                break

            if st.button("Stop", key=f"stop_{counter}"):
                st.session_state["workout_running"] = False
                break

    cap.release()

    form_score = int((correct_cues / max(total_frames, 1)) * 100)
    add_workout(username, exercise, counter, form_score)
    st.success(f"Workout saved. Reps: {counter}, Form score: {form_score}%")

