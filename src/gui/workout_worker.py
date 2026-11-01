import time
import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
import mediapipe as mp

from excerciseType import excerciseType
from bodyPartAngle import BodyPartAngle
from app.voice import speak


class WorkoutWorker(QThread):
    frame_ready = pyqtSignal(QImage)
    stats_updated = pyqtSignal(int, bool, float, str, str)  # reps, status, angle, stage, cue
    workout_finished = pyqtSignal(int, float)  # total_reps, duration_seconds
    error_occurred = pyqtSignal(str)

    def __init__(self, exercise_type="push-up", video_source=0, enable_voice=True, loop_video=False):
        super().__init__()
        self.exercise_type = exercise_type
        self.video_source = video_source  # 0 or file path string
        self.enable_voice = enable_voice
        self.loop_video = loop_video

        self._is_running = False
        self._is_paused = False
        self.counter = 0
        self.status = True
        self.start_time = 0.0
        self.last_voice_cue_time = 0.0

    def run(self):
        self._is_running = True
        self._is_paused = False
        self.counter = 0
        self.status = True
        self.start_time = time.time()
        self.last_voice_cue_time = 0.0

        if self.enable_voice:
            speak(f"Starting {self.exercise_type} workout.")

        # Initialize VideoCapture
        cap = cv2.VideoCapture(self.video_source)
        if not cap.isOpened():
            self.error_occurred.emit(f"Could not open video source: {self.video_source}")
            self._is_running = False
            return

        mp_drawing = mp.solutions.drawing_utils
        mp_pose = mp.solutions.pose

        with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
            prev_status = self.status
            prev_counter = self.counter

            while self._is_running:
                if self._is_paused:
                    time.sleep(0.05)
                    continue

                ret, frame = cap.read()
                if not ret or frame is None:
                    if isinstance(self.video_source, str) and self.loop_video:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        break

                # Standard display resolution
                frame = cv2.resize(frame, (800, 480), interpolation=cv2.INTER_AREA)

                # Process pose detection
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                results = pose.process(rgb)
                rgb.flags.writeable = True

                current_angle = 0.0
                cue = "Keep going"
                stage = "READY"

                if results.pose_landmarks:
                    landmarks = results.pose_landmarks.landmark
                    bpa = BodyPartAngle(landmarks)

                    # Update exercise repetition logic
                    try:
                        self.counter, self.status = excerciseType(landmarks).calculate_exercise(
                            self.exercise_type, self.counter, self.status
                        )
                    except Exception:
                        pass

                    # Form analysis & cues
                    if self.exercise_type == "push-up":
                        current_angle = (bpa.angle_of_the_left_arm() + bpa.angle_of_the_right_arm()) / 2.0
                        stage = "UP" if self.status else "DOWN"
                        if self.status:
                            cue = "Lower chest down" if current_angle > 150 else "Push all the way up"
                        else:
                            cue = "Good depth! Now push up" if current_angle < 110 else "Lower your chest more"

                    elif self.exercise_type == "squat":
                        current_angle = (bpa.angle_of_the_left_leg() + bpa.angle_of_the_right_leg()) / 2.0
                        stage = "STANDING" if self.status else "SQUATTING"
                        if self.status:
                            cue = "Squat down, hips back" if current_angle > 150 else "Drive up through heels"
                        else:
                            cue = "Great depth! Stand tall" if current_angle < 100 else "Sink your hips lower"

                    elif self.exercise_type == "sit-up":
                        current_angle = bpa.angle_of_the_abdomen()
                        stage = "DOWN" if self.status else "UP"
                        if self.status:
                            cue = "Engage core and sit up" if current_angle > 90 else "Hold and squeeze"
                        else:
                            cue = "Lower down with control"

                    elif self.exercise_type == "pull-up":
                        stage = "HANGING" if self.status else "TOP"
                        cue = "Pull chin above hands" if self.status else "Lower fully to dead hang"

                    elif self.exercise_type == "walk":
                        stage = "STRIDE"
                        cue = "Maintain steady pace"

                    # Trigger voice cues on state changes
                    if self.enable_voice:
                        now = time.time()
                        if self.counter > prev_counter:
                            prev_counter = self.counter
                            speak(f"{self.counter}")
                            self.last_voice_cue_time = now
                        elif self.status != prev_status and (now - self.last_voice_cue_time > 3.0):
                            prev_status = self.status
                            if cue:
                                speak(cue)
                            self.last_voice_cue_time = now

                    # Draw MediaPipe skeleton
                    mp_drawing.draw_landmarks(
                        frame,
                        results.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2),
                        mp_drawing.DrawingSpec(color=(40, 200, 250), thickness=2, circle_radius=2),
                    )

                # Emit stats signal
                self.stats_updated.emit(self.counter, self.status, float(current_angle), stage, cue)

                # Convert frame for PyQt5 QImage
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_rgb.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
                self.frame_ready.emit(qt_image)

                # Control FPS (e.g. ~30 FPS)
                time.sleep(0.02)

        cap.release()
        total_duration = time.time() - self.start_time
        self.workout_finished.emit(self.counter, total_duration)

    def pause(self):
        self._is_paused = True

    def resume(self):
        self._is_paused = False

    def stop(self):
        self._is_running = False
        self.wait(2000)

    def reset_counter(self):
        self.counter = 0
        self.status = True
