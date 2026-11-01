import os
import sys
import time
from pathlib import Path

# Load OpenCV and MediaPipe C++ runtimes first to prevent DLL conflicts on Windows
import cv2
import mediapipe as mp

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QListWidget, QListWidgetItem, QLabel, QPushButton, QComboBox,
    QFileDialog, QCheckBox, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon

from gui.styles import APP_STYLESHEET
from gui.workout_worker import WorkoutWorker
from gui.similarity_worker import VideoSimilarityWorker
from app.storage import add_workout, list_workouts


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Gym Trainer - Desktop Assistant")
        self.resize(1280, 800)
        self.setMinimumSize(1000, 650)
        self.setStyleSheet(APP_STYLESHEET)

        self.current_user = "athlete"
        self.worker = None
        self.sim_worker = None
        self.is_paused = False
        self.selected_video_path = None
        self.session_timer = QTimer(self)
        self.session_timer.timeout.connect(self._update_timer)
        self.session_start_time = None
        self.latest_reps = 0
        self.latest_duration = 0

        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # 1. Left Navigation Bar
        nav_container = QWidget()
        nav_container.setFixedWidth(220)
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(12)

        # App Brand Header
        brand_label = QLabel("🏋️ AI Gym Trainer")
        brand_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        brand_label.setStyleSheet("color: #38BDF8; padding: 10px 4px 6px 4px;")
        nav_layout.addWidget(brand_label)

        sub_brand = QLabel("Desktop AI Coach")
        sub_brand.setStyleSheet("color: #64748B; font-size: 12px; padding-left: 6px; margin-bottom: 8px;")
        nav_layout.addWidget(sub_brand)

        # Nav List
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("nav_bar")
        self.nav_list.setFocusPolicy(Qt.NoFocus)

        item_workout = QListWidgetItem("  🏋️  Live Trainer")
        item_sim = QListWidgetItem("  📊  Video Alignment")
        item_history = QListWidgetItem("  📜  Workout History")

        self.nav_list.addItem(item_workout)
        self.nav_list.addItem(item_sim)
        self.nav_list.addItem(item_history)
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self._on_tab_changed)
        nav_layout.addWidget(self.nav_list)

        nav_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Bottom System Info
        sys_info = QLabel("Status: Ready\nMediaPipe: Active")
        sys_info.setStyleSheet("color: #475569; font-size: 11px; padding: 8px;")
        nav_layout.addWidget(sys_info)

        main_layout.addWidget(nav_container)

        # 2. Right Stacked Content Pages
        self.pages_stack = QStackedWidget()
        self.pages_stack.addWidget(self._create_trainer_page())
        self.pages_stack.addWidget(self._create_similarity_page())
        self.pages_stack.addWidget(self._create_history_page())

        main_layout.addWidget(self.pages_stack, stretch=1)

    # -------------------------------------------------------------
    # Page 1: Live Workout Coach
    # -------------------------------------------------------------
    def _create_trainer_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Top Control Bar (Card)
        control_card = QFrame()
        control_card.setProperty("class", "card")
        control_layout = QHBoxLayout(control_card)
        control_layout.setContentsMargins(14, 12, 14, 12)
        control_layout.setSpacing(12)

        # Exercise selector
        lbl_ex = QLabel("Exercise:")
        lbl_ex.setStyleSheet("font-weight: 600; color: #CBD5E1;")
        self.combo_exercise = QComboBox()
        self.combo_exercise.addItems(["push-up", "squat", "sit-up", "pull-up", "walk"])
        self.combo_exercise.setFixedWidth(130)

        # Source selector
        lbl_src = QLabel("Input:")
        lbl_src.setStyleSheet("font-weight: 600; color: #CBD5E1;")
        self.combo_source = QComboBox()
        self.combo_source.addItems(["Webcam (Live)", "Video File"])
        self.combo_source.setFixedWidth(140)
        self.combo_source.currentIndexChanged.connect(self._on_source_type_changed)

        self.btn_browse = QPushButton("📁 Select Video")
        self.btn_browse.setObjectName("btn_secondary")
        self.btn_browse.setVisible(False)
        self.btn_browse.clicked.connect(self._browse_video_file)

        # Audio Toggle
        self.chk_voice = QCheckBox("Voice Coaching")
        self.chk_voice.setChecked(True)

        # Loop Toggle
        self.chk_loop = QCheckBox("Loop Video")
        self.chk_loop.setChecked(True)
        self.chk_loop.setVisible(False)

        control_layout.addWidget(lbl_ex)
        control_layout.addWidget(self.combo_exercise)
        control_layout.addWidget(lbl_src)
        control_layout.addWidget(self.combo_source)
        control_layout.addWidget(self.btn_browse)
        control_layout.addWidget(self.chk_voice)
        control_layout.addWidget(self.chk_loop)
        control_layout.addStretch()

        # Action Buttons
        self.btn_start = QPushButton("▶ Start Workout")
        self.btn_start.setObjectName("btn_start")
        self.btn_start.clicked.connect(self._toggle_workout)

        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_pause.setObjectName("btn_secondary")
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self._toggle_pause)

        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_workout)

        self.btn_reset = QPushButton("🔄 Reset")
        self.btn_reset.setObjectName("btn_secondary")
        self.btn_reset.clicked.connect(self._reset_reps)

        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_pause)
        control_layout.addWidget(self.btn_stop)
        control_layout.addWidget(self.btn_reset)

        layout.addWidget(control_card)

        # Center Section: Video Screen & Stats HUD
        center_layout = QHBoxLayout()
        center_layout.setSpacing(14)

        # Video Display Frame
        self.video_label = QLabel()
        self.video_label.setObjectName("video_display")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setMinimumSize(640, 420)
        self._set_video_placeholder()
        center_layout.addWidget(self.video_label, stretch=3)

        # Right HUD Panel (Stats Cards)
        hud_container = QWidget()
        hud_container.setFixedWidth(300)
        hud_layout = QVBoxLayout(hud_container)
        hud_layout.setContentsMargins(0, 0, 0, 0)
        hud_layout.setSpacing(12)

        # 1. Repetitions Card
        rep_card = QFrame()
        rep_card.setProperty("class", "stat-card card")
        rep_layout = QVBoxLayout(rep_card)
        rep_title = QLabel("REPETITIONS")
        rep_title.setProperty("class", "stat-title")
        self.lbl_reps = QLabel("0")
        self.lbl_reps.setProperty("class", "stat-value")
        self.lbl_reps.setAlignment(Qt.AlignCenter)
        rep_layout.addWidget(rep_title)
        rep_layout.addWidget(self.lbl_reps)
        hud_layout.addWidget(rep_card)

        # 2. Stage / Form State Card
        stage_card = QFrame()
        stage_card.setProperty("class", "stat-card card")
        stage_layout = QVBoxLayout(stage_card)
        stage_title = QLabel("CURRENT STAGE")
        stage_title.setProperty("class", "stat-title")
        self.lbl_stage = QLabel("IDLE")
        self.lbl_stage.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.lbl_stage.setStyleSheet("color: #38BDF8;")
        self.lbl_stage.setAlignment(Qt.AlignCenter)
        stage_layout.addWidget(stage_title)
        stage_layout.addWidget(self.lbl_stage)
        hud_layout.addWidget(stage_card)

        # 3. Live Coach Cue Card
        cue_card = QFrame()
        cue_card.setProperty("class", "stat-card card")
        cue_layout = QVBoxLayout(cue_card)
        cue_title = QLabel("FORM GUIDANCE")
        cue_title.setProperty("class", "stat-title")
        self.lbl_cue = QLabel("Select an exercise and click Start")
        self.lbl_cue.setProperty("class", "stat-cue")
        self.lbl_cue.setWordWrap(True)
        self.lbl_cue.setAlignment(Qt.AlignCenter)
        cue_layout.addWidget(cue_title)
        cue_layout.addWidget(self.lbl_cue)
        hud_layout.addWidget(cue_card)

        # 4. Angle & Time Row
        row_card = QFrame()
        row_card.setProperty("class", "stat-card card")
        row_layout = QHBoxLayout(row_card)
        
        angle_col = QVBoxLayout()
        lbl_ang_title = QLabel("JOINT ANGLE")
        lbl_ang_title.setProperty("class", "stat-title")
        self.lbl_angle = QLabel("--°")
        self.lbl_angle.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.lbl_angle.setStyleSheet("color: #F8FAFC;")
        angle_col.addWidget(lbl_ang_title)
        angle_col.addWidget(self.lbl_angle)

        time_col = QVBoxLayout()
        lbl_tim_title = QLabel("TIME")
        lbl_tim_title.setProperty("class", "stat-title")
        self.lbl_time = QLabel("00:00")
        self.lbl_time.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.lbl_time.setStyleSheet("color: #F8FAFC;")
        time_col.addWidget(lbl_tim_title)
        time_col.addWidget(self.lbl_time)

        row_layout.addLayout(angle_col)
        row_layout.addLayout(time_col)
        hud_layout.addWidget(row_card)

        # Save workout button
        self.btn_save_workout = QPushButton("💾 Save Workout Record")
        self.btn_save_workout.setObjectName("btn_secondary")
        self.btn_save_workout.clicked.connect(self._save_current_workout)
        hud_layout.addWidget(self.btn_save_workout)

        hud_layout.addStretch()
        center_layout.addWidget(hud_container)

        layout.addLayout(center_layout)
        return page

    # -------------------------------------------------------------
    # Page 2: Video Alignment & Form Similarity
    # -------------------------------------------------------------
    def _create_similarity_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(16)

        header = QLabel("Video Form Alignment & Similarity")
        header.setProperty("class", "heading")
        sub = QLabel("Compare user exercise execution against an expert reference video using temporal kernel alignment.")
        sub.setProperty("class", "subheading")
        layout.addWidget(header)
        layout.addWidget(sub)

        # Form Card
        form_card = QFrame()
        form_card.setProperty("class", "card")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(14)

        # Expert Video Input
        exp_layout = QHBoxLayout()
        lbl_exp = QLabel("Expert Video:")
        lbl_exp.setFixedWidth(120)
        self.lbl_exp_path = QLabel("data/media_pipe_output/pushup.mp4")
        self.lbl_exp_path.setStyleSheet("color: #38BDF8; font-weight: 500;")
        btn_browse_exp = QPushButton("Browse Expert Video")
        btn_browse_exp.setObjectName("btn_secondary")
        btn_browse_exp.clicked.connect(self._browse_expert_video)
        exp_layout.addWidget(lbl_exp)
        exp_layout.addWidget(self.lbl_exp_path, stretch=1)
        exp_layout.addWidget(btn_browse_exp)
        form_layout.addLayout(exp_layout)

        # User Video Input
        user_layout = QHBoxLayout()
        lbl_user = QLabel("User Video:")
        lbl_user.setFixedWidth(120)
        self.lbl_user_path = QLabel("data/yolo_input_videos/pushup1.mp4")
        self.lbl_user_path.setStyleSheet("color: #38BDF8; font-weight: 500;")
        btn_browse_user = QPushButton("Browse User Video")
        btn_browse_user.setObjectName("btn_secondary")
        btn_browse_user.clicked.connect(self._browse_user_video)
        user_layout.addWidget(lbl_user)
        user_layout.addWidget(self.lbl_user_path, stretch=1)
        user_layout.addWidget(btn_browse_user)
        form_layout.addLayout(user_layout)

        # Run Button
        self.btn_run_sim = QPushButton("⚡ Compare Form & Compute Similarity")
        self.btn_run_sim.clicked.connect(self._run_similarity_analysis)
        form_layout.addWidget(self.btn_run_sim)

        layout.addWidget(form_card)

        # Results Card
        res_card = QFrame()
        res_card.setProperty("class", "card")
        res_layout = QVBoxLayout(res_card)
        res_layout.setContentsMargins(20, 20, 20, 20)

        res_title = QLabel("Alignment Results")
        res_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        self.lbl_sim_status = QLabel("Select both videos and click 'Compare Form' to analyze.")
        self.lbl_sim_status.setStyleSheet("color: #94A3B8; font-size: 14px; margin-top: 8px;")

        self.lbl_sim_score = QLabel("Similarity Score: --")
        self.lbl_sim_score.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.lbl_sim_score.setStyleSheet("color: #38BDF8; margin-top: 10px;")

        res_layout.addWidget(res_title)
        res_layout.addWidget(self.lbl_sim_status)
        res_layout.addWidget(self.lbl_sim_score)
        res_layout.addStretch()

        layout.addWidget(res_card, stretch=1)
        return page

    # -------------------------------------------------------------
    # Page 3: Workout History
    # -------------------------------------------------------------
    def _create_history_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(14)

        top_row = QHBoxLayout()
        header = QLabel("Workout Log & History")
        header.setProperty("class", "heading")
        top_row.addWidget(header)
        top_row.addStretch()

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setObjectName("btn_secondary")
        btn_refresh.clicked.connect(self._load_workout_history)
        top_row.addWidget(btn_refresh)

        layout.addLayout(top_row)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Exercise", "Reps Completed", "Form Score", "Duration", "Athlete"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.verticalHeader().setVisible(False)
        layout.addWidget(self.history_table)

        self._load_workout_history()
        return page

    # -------------------------------------------------------------
    # Trainer Logic & Signals
    # -------------------------------------------------------------
    def _set_video_placeholder(self):
        pixmap = QPixmap(800, 480)
        pixmap.fill(Qt.transparent)
        self.video_label.setText(
            "🏋️ AI GYM TRAINER\n\n"
            "1. Choose an exercise\n"
            "2. Select Webcam or Video File\n"
            "3. Click 'Start Workout' to begin"
        )
        self.video_label.setStyleSheet(
            "color: #64748B; font-size: 16px; font-weight: 600; "
            "background-color: #020617; border: 2px dashed #334155; border-radius: 12px;"
        )

    def _on_source_type_changed(self, index):
        is_file = (index == 1)
        self.btn_browse.setVisible(is_file)
        self.chk_loop.setVisible(is_file)

    def _browse_video_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Exercise Video", "", "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)"
        )
        if file_path:
            self.selected_video_path = file_path
            self.btn_browse.setText(f"📁 {Path(file_path).name[:15]}")

    def _toggle_workout(self):
        if self.worker is not None and self.worker.isRunning():
            return

        exercise = self.combo_exercise.currentText()
        if self.combo_source.currentIndex() == 0:
            source = 0
        else:
            if not self.selected_video_path:
                # Offer a default sample from data directory if exists
                default_sample = "data/media_pipe_output/pushup.mp4"
                if os.path.exists(default_sample):
                    self.selected_video_path = default_sample
                else:
                    self._browse_video_file()
                    if not self.selected_video_path:
                        return
            source = self.selected_video_path

        enable_voice = self.chk_voice.isChecked()
        loop_video = self.chk_loop.isChecked()

        self.worker = WorkoutWorker(
            exercise_type=exercise,
            video_source=source,
            enable_voice=enable_voice,
            loop_video=loop_video
        )
        self.worker.frame_ready.connect(self._on_frame_ready)
        self.worker.stats_updated.connect(self._on_stats_updated)
        self.worker.workout_finished.connect(self._on_workout_finished)
        self.worker.error_occurred.connect(self._on_worker_error)

        self.worker.start()

        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.btn_pause.setText("⏸ Pause")
        self.is_paused = False

        self.session_start_time = time.time()
        self.session_timer.start(1000)
        self.video_label.setStyleSheet("background-color: #020617; border: 2px solid #334155; border-radius: 12px;")

    def _toggle_pause(self):
        if not self.worker or not self.worker.isRunning():
            return
        if not self.is_paused:
            self.worker.pause()
            self.is_paused = True
            self.btn_pause.setText("▶ Resume")
            self.lbl_stage.setText("PAUSED")
        else:
            self.worker.resume()
            self.is_paused = False
            self.btn_pause.setText("⏸ Pause")

    def _stop_workout(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
        self.session_timer.stop()
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self._set_video_placeholder()

    def _reset_reps(self):
        if self.worker:
            self.worker.reset_counter()
        self.lbl_reps.setText("0")
        self.lbl_stage.setText("READY")

    def _on_frame_ready(self, qimage: QImage):
        pixmap = QPixmap.fromImage(qimage)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)

    def _on_stats_updated(self, reps: int, status: bool, angle: float, stage: str, cue: str):
        self.latest_reps = reps
        self.lbl_reps.setText(str(reps))
        self.lbl_stage.setText(stage)
        self.lbl_cue.setText(cue)
        self.lbl_angle.setText(f"{angle:.1f}°" if angle > 0 else "--°")

    def _on_workout_finished(self, total_reps: int, duration_sec: float):
        self.latest_reps = total_reps
        self.latest_duration = int(duration_sec)
        self._stop_workout()
        QMessageBox.information(
            self, "Workout Finished",
            f"Great job! Workout completed.\nTotal Repetitions: {total_reps}\nDuration: {int(duration_sec)} seconds"
        )

    def _on_worker_error(self, message: str):
        self._stop_workout()
        QMessageBox.warning(self, "Camera / Video Error", message)

    def _update_timer(self):
        if self.session_start_time and not self.is_paused:
            elapsed = int(time.time() - self.session_start_time)
            mins = elapsed // 60
            secs = elapsed % 60
            self.lbl_time.setText(f"{mins:02d}:{secs:02d}")
            self.latest_duration = elapsed

    def _save_current_workout(self):
        if self.latest_reps == 0 and self.latest_duration == 0:
            QMessageBox.information(self, "Save Workout", "Complete at least one workout repetition first!")
            return
        exercise = self.combo_exercise.currentText()
        add_workout(self.current_user, exercise, self.latest_reps, form_score=100, duration_sec=self.latest_duration)
        QMessageBox.information(self, "Saved", f"Workout saved to history!\n{exercise}: {self.latest_reps} reps.")
        self._load_workout_history()

    # -------------------------------------------------------------
    # Alignment Page Logic
    # -------------------------------------------------------------
    def _browse_expert_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Expert Video", "", "Video Files (*.mp4 *.avi *.mov)")
        if file_path:
            self.lbl_exp_path.setText(file_path)

    def _browse_user_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select User Video", "", "Video Files (*.mp4 *.avi *.mov)")
        if file_path:
            self.lbl_user_path.setText(file_path)

    def _run_similarity_analysis(self):
        exp = self.lbl_exp_path.text()
        usr = self.lbl_user_path.text()
        self.lbl_sim_status.setText("Processing alignment kernel...")
        self.btn_run_sim.setEnabled(False)

        self.sim_worker = VideoSimilarityWorker(exp, usr)
        self.sim_worker.progress_updated.connect(lambda msg: self.lbl_sim_status.setText(msg))
        self.sim_worker.comparison_completed.connect(self._on_sim_completed)
        self.sim_worker.error_occurred.connect(self._on_sim_error)
        self.sim_worker.start()

    def _on_sim_completed(self, score: float, best_frame: int, output_path: str):
        self.btn_run_sim.setEnabled(True)
        self.lbl_sim_score.setText(f"Similarity Score: {score:.4f}")
        self.lbl_sim_status.setText(f"Aligned successfully at frame index: {best_frame}. Output: {output_path}")

    def _on_sim_error(self, error_msg: str):
        self.btn_run_sim.setEnabled(True)
        self.lbl_sim_status.setText(error_msg)
        QMessageBox.warning(self, "Alignment Notice", error_msg)

    # -------------------------------------------------------------
    # History Page Logic
    # -------------------------------------------------------------
    def _load_workout_history(self):
        rows = list_workouts(self.current_user) or []
        self.history_table.setRowCount(len(rows))
        for i, row in enumerate(reversed(rows)):
            self.history_table.setItem(i, 0, QTableWidgetItem(str(row.get("exercise", "-"))))
            self.history_table.setItem(i, 1, QTableWidgetItem(str(row.get("reps", 0))))
            self.history_table.setItem(i, 2, QTableWidgetItem(f"{row.get('form_score', 0)}%"))
            dur = row.get("duration_sec", 0)
            self.history_table.setItem(i, 3, QTableWidgetItem(f"{dur}s"))
            self.history_table.setItem(i, 4, QTableWidgetItem(self.current_user))

    def _on_tab_changed(self, row: int):
        self.pages_stack.setCurrentIndex(row)
        if row == 2:
            self._load_workout_history()

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
        event.accept()
