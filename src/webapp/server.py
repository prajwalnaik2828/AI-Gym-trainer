import base64
import io
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Optional

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
import secrets

_SRC_DIR = Path(__file__).resolve().parents[1]
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

import cv2
import numpy as np
import mediapipe as mp
import threading

from app.storage import signup as store_signup, login as store_login, get_user, list_workouts, add_workout, update_user, set_goal, list_goals, update_goal
from excerciseType import excerciseType
from bodyPartAngle import BodyPartAngle
from app.trainer_coach import get_trainer_coach


app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-change-me")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=False if os.environ.get('DEV', '1') == '1' else True,
)


# MediaPipe Pose instance
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(model_complexity=0, min_detection_confidence=0.6, min_tracking_confidence=0.6)
POSE_LOCK = threading.Lock()

# YOLO11 Pose instance
try:
    from yolo_pose import YOLOPoseDetector
    yolo_detector = YOLOPoseDetector()
    YOLO_LOCK = threading.Lock()
    HAS_YOLO11 = True
except Exception as _e:
    yolo_detector = None
    YOLO_LOCK = threading.Lock()
    HAS_YOLO11 = False
TUTORIALS = {
    "squat": "https://www.youtube-nocookie.com/embed/aclHkVaku9U?rel=0&modestbranding=1",
    "push-up": "https://www.youtube-nocookie.com/embed/IODxDxX7oi4?rel=0&modestbranding=1",
    "sit-up": "https://www.youtube-nocookie.com/embed/jDwoBqPH0jk?rel=0&modestbranding=1",
    "walk": "https://www.youtube-nocookie.com/embed/3Ka7B3hCg08?rel=0&modestbranding=1",
}


@dataclass
class SessionState:
    counter: int = 0
    status: bool = True
    last_exercise: str = "squat"
    last_cue_ts: float = 0.0
    last_cue: str = ""
    started_at: float = 0.0


session_states: Dict[str, SessionState] = {}


def get_state() -> SessionState:
    sid = session.get("sid")
    if not sid:
        sid = os.urandom(16).hex()
        session["sid"] = sid
    if sid not in session_states:
        session_states[sid] = SessionState()
    return session_states[sid]


def require_auth():
    if not session.get("user"):
        return redirect(url_for("login"))
    return None


def get_csrf_token() -> str:
    token = session.get('_csrf')
    if not token:
        token = secrets.token_hex(16)
        session['_csrf'] = token
    return token


def verify_csrf(token: str) -> bool:
    return token and session.get('_csrf') and secrets.compare_digest(token, session['_csrf'])


@app.route("/")
def index():
    if session.get("user"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.after_request
def set_security_headers(resp):
    # Basic hardening headers
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['X-Frame-Options'] = 'DENY'
    resp.headers['Referrer-Policy'] = 'no-referrer'
    resp.headers['Permissions-Policy'] = 'camera=*'
    # Only set CSP on HTML responses to avoid flagging for non-HTML resources
    if (resp.mimetype or '').startswith('text/html'):
        csp = "default-src 'self' data: blob:; img-src 'self' data: blob:; media-src 'self' blob:; frame-src 'self' https://www.youtube-nocookie.com https://www.youtube.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; connect-src 'self' https://cdn.jsdelivr.net; frame-ancestors 'none'"
        resp.headers['Content-Security-Policy'] = csp
    # Ensure charset on HTML responses
    if (resp.mimetype or '').startswith('text/html') and 'charset' not in (resp.content_type or '').lower():
        resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if not verify_csrf(request.form.get('_csrf')):
            return render_template("login.html", error="Invalid session. Refresh and try again.", csrf=get_csrf_token()), 400
        username = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if store_login(username, password):
            session["user"] = username
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid credentials", csrf=get_csrf_token())
    return render_template("login.html", csrf=get_csrf_token())


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        if not verify_csrf(request.form.get('_csrf')):
            return render_template("signup.html", error="Invalid session. Refresh and try again.", csrf=get_csrf_token()), 400
        email = request.form.get("email", "").strip()
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "")
        if store_signup(email, password, full_name):
            return redirect(url_for("login"))
        return render_template("signup.html", error="User already exists", csrf=get_csrf_token())
    return render_template("signup.html", csrf=get_csrf_token())


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    auth = require_auth()
    if auth:
        return auth
    recent = list_workouts(session["user"]) or []
    goals = list_goals(session["user"]) or []
    # annotate with due warnings
    import datetime as _dt
    today = _dt.date.today()
    annotated = []
    for i, g in enumerate(goals):
        due = None
        try:
            y, m, d = map(int, (g.get('target_date') or '1970-01-01').split('-'))
            due = _dt.date(y, m, d)
        except Exception:
            pass
        days_left = (due - today).days if due else None
        warn = bool((days_left is not None) and days_left <= 3 and not g.get('completed'))
        annotated.append({
            **g,
            'index': i,
            'days_left': days_left,
            'warn': warn,
        })
    # aggregates by exercise
    totals: Dict[str, Dict[str, int]] = {}
    for w in recent:
        e = w.get('exercise', 'unknown')
        bucket = totals.setdefault(e, { 'reps': 0, 'duration_sec': 0 })
        bucket['reps'] += int(w.get('reps') or 0)
        bucket['duration_sec'] += int(w.get('duration_sec') or 0)
    return render_template("dashboard.html", user=get_user(session["user"]) or {}, recent=recent, goals=annotated, totals=totals, csrf=get_csrf_token())


@app.route("/profile/update", methods=["POST"])
def profile_update():
    auth = require_auth()
    if auth:
        return auth
    if not verify_csrf(request.form.get('_csrf')):
        return redirect(url_for('dashboard'))
    payload = request.form
    updates = {
        "full_name": payload.get("full_name") or None,
        "age": int(payload.get("age")) if payload.get("age") else None,
        "height_cm": int(payload.get("height_cm")) if payload.get("height_cm") else None,
        "weight_kg": int(payload.get("weight_kg")) if payload.get("weight_kg") else None,
        "gender": payload.get("gender") or None,
    }
    update_user(session["user"], updates)
    return redirect(url_for("dashboard"))


@app.route("/goals/create", methods=["POST"])
def goals_create():
    auth = require_auth()
    if auth:
        return auth
    if not verify_csrf(request.form.get('_csrf')):
        return redirect(url_for('dashboard'))
    payload = request.form
    set_goal(session["user"], payload.get("goal_type", ""), payload.get("target_date", ""), payload.get("notes", ""))
    return redirect(url_for("dashboard"))


@app.route("/goals/update", methods=["POST"])
def goals_update():
    auth = require_auth()
    if auth:
        return auth
    if not verify_csrf(request.form.get('_csrf')):
        return redirect(url_for('dashboard'))
    try:
        idx = int(request.form.get('index'))
    except Exception:
        return redirect(url_for('dashboard'))
    progress = request.form.get('progress')
    completed = True if request.form.get('completed') == 'on' else None
    update_goal(session['user'], idx, int(progress) if progress else None, completed)
    return redirect(url_for('dashboard'))


@app.route("/workout")
def workout():
    auth = require_auth()
    if auth:
        return auth
    exercise = request.args.get("exercise", "squat")
    st = get_state()
    st.last_exercise = exercise
    import time as _time
    st.started_at = _time.time()
    tutorial = TUTORIALS.get(exercise)
    return render_template("workout.html", exercise=exercise, tutorial=tutorial, csrf=get_csrf_token())


def _generate_cue(landmarks, exercise: str, status: bool) -> Optional[str]:
    bpa = BodyPartAngle(landmarks)
    if exercise == "squat":
        left_k = bpa.angle_of_the_left_leg()
        right_k = bpa.angle_of_the_right_leg()
        avg_k = (left_k + right_k) / 2
        if avg_k > 170:
            return "Stand tall, lock hips at the top."
        if avg_k > 120 and not status:
            return "Go deeper, push hips back."
        if avg_k < 70 and not status:
            return "Do not collapse, keep chest up."
        return None
    if exercise == "push-up":
        left_a = bpa.angle_of_the_left_arm()
        right_a = bpa.angle_of_the_right_arm()
        avg_a = (left_a + right_a) / 2
        core = bpa.angle_of_the_abdomen()
        if core < 165:
            return "Keep your core tight, avoid sagging."
        if avg_a > 165 and status:
            return "Full lockout at the top."
        if avg_a > 120 and not status:
            return "Lower chest closer to the floor."
        return None
    if exercise == "sit-up":
        abd = bpa.angle_of_the_abdomen()
        if abd > 120 and status:
            return "Engage core and curl up smoothly."
        if abd < 60 and not status:
            return "Control the descent, don't flop."
        return None
    if exercise == "walk":
        neck = bpa.angle_of_the_neck()
        if neck < 170:
            return "Keep your head neutral, eyes forward."
        return None
    return None


def _process_frame(bgr: np.ndarray, exercise: str, st: SessionState, engine: str = "yolo11", session_id: str = "default") -> Tuple[np.ndarray, int, bool, Optional[str]]:
    # downscale slightly to reduce inference latency if necessary
    h, w = bgr.shape[:2]
    scale = 0.6 if max(h, w) > 720 else 1.0
    if scale != 1.0:
        bgr = cv2.resize(bgr, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)

    landmarks = None
    frame = bgr

    # Prefer YOLO11 Pose if selected and available
    if engine == "yolo11" and yolo_detector is not None:
        try:
            with YOLO_LOCK:
                frame, landmarks = yolo_detector.process(bgr)
        except Exception:
            landmarks = None
    else:
        # Fallback to MediaPipe
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        try:
            with POSE_LOCK:
                results = pose.process(rgb)
        except Exception:
            results = type('R', (), {'pose_landmarks': None})()
        rgb.flags.writeable = True
        frame = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    if landmarks:
        try:
            st.counter, st.status = excerciseType(landmarks).calculate_exercise(exercise, st.counter, st.status)
        except Exception:
            pass

    # Dynamic, intelligent personal trainer coaching
    coach = get_trainer_coach(session_id)
    cue = coach.evaluate_form_and_get_cue(landmarks, exercise, st.counter, st.status)

    tag = "YOLO11" if (engine == "yolo11" and yolo_detector is not None) else "MediaPipe"
    cv2.putText(frame, f"{exercise} | reps: {st.counter} ({tag})", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    return frame, st.counter, st.status, cue


@app.route("/api/frame", methods=["POST"])
def api_frame():
    auth = require_auth()
    if auth:
        # For API, return 401 JSON
        return jsonify({"error": "unauthorized"}), 401
    payload = request.get_json(silent=True) or {}
    if not verify_csrf(payload.get('_csrf')):
        return jsonify({"error": "bad_csrf"}), 400
    data_url = payload.get("image")
    exercise = payload.get("exercise", "squat")
    engine = payload.get("engine", "yolo11")
    if not data_url or not data_url.startswith("data:image/"):
        return jsonify({"error": "bad_request"}), 400
    # decode base64
    try:
        header, b64 = data_url.split(",", 1)
        img_bytes = base64.b64decode(b64)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if bgr is None:
            return jsonify({"error": "decode_failed"}), 400
        st = get_state()
        sid = session.get("sid", "default")
        frame, counter, status, cue = _process_frame(bgr, exercise, st, engine=engine, session_id=sid)
        try:
            encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 70]
            _, encoded = cv2.imencode('.jpg', frame, encode_params)
        except Exception:
            _, encoded = cv2.imencode('.jpg', frame)
        out_data_url = "data:image/jpeg;base64," + base64.b64encode(encoded.tobytes()).decode('utf-8')
        return jsonify({"counter": counter, "status": status, "image": out_data_url, "cue": cue, "engine": engine})
    except Exception as e:
        return jsonify({"error": "processing_failed"}), 500


@app.route("/api/workout/finish", methods=["POST"]) 
def api_finish():
    auth = require_auth()
    if auth:
        return jsonify({"error": "unauthorized"}), 401
    st = get_state()
    exercise = request.get_json(silent=True) or {}
    name = exercise.get("exercise", st.last_exercise)
    # naive form score placeholder
    import time as _time
    form_score = 100 if st.counter > 0 else 0
    duration = int(max(0, _time.time() - (st.started_at or _time.time())))
    add_workout(session["user"], name, st.counter, form_score, duration)
    st.counter, st.status = 0, True
    st.started_at = 0.0
    return jsonify({"ok": True})


@app.route('/static/<path:filename>')
def staticfiles(filename):
    return send_from_directory(app.static_folder, filename)


def main():
    # Use threaded server; disable reloader to avoid duplicate processes grabbing camera
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=False, threaded=True, use_reloader=False)


if __name__ == "__main__":
    main()


