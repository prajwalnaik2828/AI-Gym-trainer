import json
from pathlib import Path
from typing import Optional, Dict, Any


_DB_PATH = Path(__file__).resolve().parents[1] / "workspace" / "users.json"


def _ensure_db() -> Dict[str, Any]:
    if not _DB_PATH.exists():
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {"users": [], "workouts": {}, "goals": {}}
        _DB_PATH.write_text(json.dumps(data, indent=2))
        return data
    try:
        return json.loads(_DB_PATH.read_text() or '{}') or {"users": [], "workouts": {}, "goals": {}}
    except Exception:
        return {"users": [], "workouts": {}, "goals": {}}


def _save_db(data: Dict[str, Any]) -> None:
    _DB_PATH.write_text(json.dumps(data, indent=2))


def _hash_password(password: str) -> str:
    try:
        import bcrypt
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    except Exception:
        # Fallback: store plain text (NOT SECURE). Kept to avoid runtime crashes if bcrypt missing.
        return password


def _verify_password(password: str, hashed: str) -> bool:
    try:
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return password == hashed


def signup(username: str, password: str, full_name: str = "") -> bool:
    data = _ensure_db()
    if any(u.get("username") == username for u in data.get("users", [])):
        return False
    user = {
        "username": username,
        "password": _hash_password(password),
        "full_name": full_name,
        "level": "Beginner",
        "age": None,
        "height_cm": None,
        "weight_kg": None,
    }
    data.setdefault("users", []).append(user)
    _save_db(data)
    return True


def login(username: str, password: str) -> bool:
    data = _ensure_db()
    for u in data.get("users", []):
        if u.get("username") == username:
            return _verify_password(password, u.get("password", ""))
    return False


def get_user(username: str) -> Optional[Dict[str, Any]]:
    data = _ensure_db()
    for u in data.get("users", []):
        if u.get("username") == username:
            return u
    return None


def update_user(username: str, updates: Dict[str, Any]) -> bool:
    data = _ensure_db()
    updated = False
    for u in data.get("users", []):
        if u.get("username") == username:
            u.update({k: v for k, v in updates.items() if k != "password"})
            updated = True
            break
    if updated:
        _save_db(data)
    return updated


def add_workout(username: str, exercise: str, reps: int, form_score: int, duration_sec: int = 0) -> None:
    data = _ensure_db()
    data.setdefault("workouts", {})
    data["workouts"].setdefault(username, [])
    data["workouts"][username].append({
        "exercise": exercise,
        "reps": reps,
        "form_score": form_score,
        "duration_sec": duration_sec,
    })
    _save_db(data)


def list_workouts(username: str) -> list:
    data = _ensure_db()
    return data.get("workouts", {}).get(username, [])


# Goals storage
def set_goal(username: str, goal_type: str, target_date: str, notes: str = "") -> None:
    data = _ensure_db()
    data.setdefault("goals", {})
    data["goals"].setdefault(username, [])
    data["goals"][username].append({
        "type": goal_type,
        "target_date": target_date,
        "notes": notes,
        "progress": 0,
        "completed": False,
    })
    _save_db(data)


def list_goals(username: str) -> list:
    data = _ensure_db()
    return data.get("goals", {}).get(username, [])


def update_goal(username: str, idx: int, progress: int | None = None, completed: bool | None = None) -> bool:
    data = _ensure_db()
    goals = data.get("goals", {}).get(username, [])
    if idx < 0 or idx >= len(goals):
        return False
    if progress is not None:
        goals[idx]["progress"] = max(0, min(100, int(progress)))
    if completed is not None:
        goals[idx]["completed"] = bool(completed)
    _save_db(data)
    return True


