# 🏋️ AI Gym Trainer

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![YOLO11](https://img.shields.io/badge/YOLO11-Ultralytics-00FFFF?style=for-the-badge&logo=yolo&logoColor=black)](https://github.com/ultralytics/ultralytics)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Google-00897B?style=for-the-badge&logo=google&logoColor=white)](https://developers.google.com/mediapipe)
[![Flask](https://img.shields.io/badge/Flask-Web_App-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer_Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)

An intelligent, real-time computer vision workout assistant designed to guide, count, and critique your gym exercises. Powered by **YOLO11 Pose** and **MediaPipe**, featuring a modern **glassmorphic web dashboard**, live form correction, and a **dynamic AI voice trainer** that coaches you through every repetition like a real personal trainer.

---

## ✨ Features

### 🧠 Dual Pose Estimation Engines
- **YOLO11 Pose (`yolo11n-pose.pt`)**: Powered by Ultralytics, delivering high-precision 17-keypoint deep learning pose estimation with PyTorch acceleration and robust occlusion resistance.
- **MediaPipe Pose**: Google's lightweight 33-landmark topological mesh optimized for low-latency CPU and GPU inference.
- **Engine Switching**: Switch seamlessly between YOLO11 and MediaPipe directly from the workout HUD.

### 🎙️ Dynamic AI Personal Voice Trainer
- **Contextual Spoken Coaching**: Doesn't just repeat robotic lines. The coach gives dynamic, exercise-specific guidance based on your actual posture:
  - *Squats*: Depth alerts, chest-proud cues, and heel drive reminders.
  - *Push-ups*: Full lockout checks, core sagging warnings, and chest-to-floor depth cues.
  - *Sit-ups*: Pacing and abdominal contraction cues.
  - *Walk*: Rhythm and posture cues.
- **Trainer Personas**: Choose between **Coach Marcus** (energetic, hype-focused) and **Coach Maya** (technical, precision-focused).
- **Rep Milestones & Form Praise**: Celebrates rep milestones (rep 5, 10, 15, 20+) and praises you in real-time when you correct poor form.

### 💎 Modern Glassmorphic Dashboard
- **Dark-Theme Glassmorphism**: Polished UI with sleek translucent cards, glowing accents, and smooth transitions.
- **Interactive Workout HUD**: Real-time video canvas with pose skeleton overlay, live angle readings, rep counter, form status badge, and immediate corrective advice.
- **Exercise Library**: Built-in support for **Squats**, **Push-ups**, **Pull-ups**, **Sit-ups**, and **Walking**.

### 📊 Progress Tracking & Goals
- **Session History**: Automatically records workout date, exercise type, completed repetitions, session duration, and form score.
- **Fitness Goals**: Set, track, and complete fitness goals (Muscle Building, Weight Loss, Endurance, Flexibility) with interactive progress bars.
- **Personalized Profile**: Manage fitness level (Beginner, Intermediate, Advanced), body stats, and custom targets.

---

## 🚀 Quick Start (1-Click Run)

### Prerequisites
- **Operating System**: Windows 10 / 11, macOS, or Linux
- **Python**: Version 3.10.x recommended
- **Hardware**: Standard webcam or USB camera

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/prajwalnaik2828/AI-Gym-trainer.git
   cd AI-Gym-trainer
   ```

2. **Set up a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: Ultralytics will automatically download the lightweight `yolo11n-pose.pt` model file on its very first launch).*

---

### Running the Application

- **Option A (Windows 1-Click):** Double-click `run.bat` in the project root folder.
- **Option B (Command Line):**
  ```bash
  python main.py
  ```

Once started, the application will automatically open in your default browser at:
```
http://localhost:8000
```

> **Default Demo Account**: You can sign up with your own email, or log in immediately using the pre-configured demo account:
> - **Email**: `demo@aigym.com`
> - **Password**: `demo123` *(or create any new user account via the Sign Up page)*

---

## 🛠️ Command-Line Tools (CLI)

In addition to the interactive web application, standalone CLI scripts are available for testing and video processing:

### 1. YOLO11 Pose Estimation CLI
Run real-time pose tracking on your webcam or a video file:
```bash
# Live webcam:
python src/yolo_main.py -t squat

# Video input & output saving:
python src/yolo_main.py -t push-up -vs path/to/input.mp4 -vo path/to/output.mp4
```
Supported flags:
- `-t`: Exercise type (`squat`, `push-up`, `pull-up`, `sit-up`, or `walk`).
- `-vs`: *(Optional)* Path to source video file (omit for live webcam).
- `-vo`: *(Optional)* Path to save annotated output video.

### 2. MediaPipe Pose Estimation CLI
```bash
python src/main.py -t squat -vs path/to/input.mp4 -vo path/to/output.mp4
```

### 3. Video Synchronization & Similarity
Compare a user workout video against an expert reference video using temporal kernel alignment:
```bash
python src/video_sim.py -v1 path/to/expert_video.mp4 -v2 path/to/user_video.mp4
```

---

## 📐 Exercise Pose Analysis & Angles

| Exercise | Primary Joint Angles Measured | Good Form Criteria |
| :--- | :--- | :--- |
| **Squats** | Hip — Knee — Ankle | Knee bend angle drops below 90° for full depth |
| **Push-ups** | Shoulder — Elbow — Wrist | Elbow flexion below 90° with a straight back |
| **Pull-ups** | Shoulder — Elbow — Wrist | Chin over bar, arms reach full extension at bottom |
| **Sit-ups** | Shoulder — Hip — Knee | Trunk flexes forward to engage core |
| **Walk** | Hip — Knee — Ankle | Consistent cadence and upright spine posture |

---

## 📁 Repository Structure

```text
AI-Gym-Trainer/
├── main.py                     # Primary web application launcher
├── run.bat                     # Windows 1-click startup batch script
├── requirements.txt            # Python dependencies (NumPy <2, Torch, Ultralytics, Flask)
├── README.md                   # Project documentation
├── .gitignore                  # Git ignore rules (weights, caches, personal data)
├── src/
│   ├── yolo_pose.py            # YOLO11 17-keypoint to 33-landmark adapter
│   ├── yolo_main.py            # YOLO11 standalone CLI runner
│   ├── bodyPartAngle.py        # Joint angle trigonometry calculations
│   ├── excerciseType.py        # Exercise state machines & rep counters
│   ├── video_sim.py            # Temporal video alignment & similarity score
│   ├── app/
│   │   ├── trainer_coach.py    # Dynamic AI voice coaching logic & phrase banks
│   │   └── storage.py          # User authentication & workout history JSON store
│   ├── webapp/
│   │   ├── server.py           # Flask web server & streaming endpoints
│   │   ├── static/             # Stylesheets (styles.css), images, assets
│   │   └── templates/          # Modern HTML templates (dashboard, workout, etc.)
│   └── workspace/
│       └── users.json          # Sanitized user database
```

---

## 🛡️ Privacy & Security

- **Local Video Processing**: All camera streams are processed locally on your machine. No video frames or audio recordings are sent to external cloud servers.
- **Sanitized Credentials**: No private email addresses, API tokens, or hardcoded sensitive passwords are stored in this repository.

---

## 🤝 Attribution & Acknowledgments

This project builds upon and significantly extends the foundational research work from the open-source repository [shrishashegde/AI-Gym-Trainer](https://github.com/shrishashegde/AI-Gym-Trainer), originally created by:
- **Shrisha Shridhar Hegde** (`shrisha.hegde@sjsu.edu`)
- **Suruchi Sharma** (`suruchi.sharma@sjsu.edu`)
- **Ankur** (`ankur@sjsu.edu`)

### Key Enhancements Introduced in this Repository:
- **Upgraded from YOLOv7 to YOLO11 Pose**: Integrated Ultralytics YOLO11 with real-time PyTorch acceleration, automated weights management, and full compatibility with existing 33-landmark exercise logic.
- **Dynamic AI Trainer Voice Engine**: Replaced static repetition with an adaptive coaching system offering non-repetitive phrasing, milestone celebrations, and dual coach personas (*Marcus* & *Maya*).
- **Glassmorphic Web App**: Built a responsive dark-theme dashboard featuring real-time HUD overlays, goal setting, session logs, and profile management.
- **Robust Hardware & Camera Support**: Multi-resolution camera fallbacks, cross-browser audio support, and 1-click launch scripts.

### Academic References:
1. Dwibedi, D., et al. *"Counting Out Time: Class Agnostic Video Repetition Counting in the Wild."* CVPR 2020.
2. Jocher, G., et al. *"Ultralytics YOLO11"*, Ultralytics Inc., 2024.
3. Lugaresi, C., et al. *"MediaPipe: A Framework for Building Perception Pipelines."* arXiv:1906.08172, 2019.
4. Hadji, I., et al. *"Learning to Align and Match Videos with Kernelized Temporal Layers (LAMV)."* CVPR 2021.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
