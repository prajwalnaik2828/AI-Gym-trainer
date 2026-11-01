import os
from PyQt5.QtCore import QThread, pyqtSignal


class VideoSimilarityWorker(QThread):
    progress_updated = pyqtSignal(str)
    comparison_completed = pyqtSignal(float, int, str)  # score, best_frame, output_video_path
    error_occurred = pyqtSignal(str)

    def __init__(self, expert_video_path: str, user_video_path: str):
        super().__init__()
        self.expert_video_path = expert_video_path
        self.user_video_path = user_video_path

    def run(self):
        try:
            import torch
        except ImportError:
            self.error_occurred.emit(
                "PyTorch is not installed in the current environment.\n"
                "To enable video similarity comparison, run: pip install torch"
            )
            return

        if not os.path.exists(self.expert_video_path):
            self.error_occurred.emit(f"Expert video not found: {self.expert_video_path}")
            return
        if not os.path.exists(self.user_video_path):
            self.error_occurred.emit(f"User video not found: {self.user_video_path}")
            return

        try:
            self.progress_updated.emit("Loading video alignment model...")
            from video_sim import data_prepare, Score_

            self.progress_updated.emit("Extracting features from Expert video...")
            frame_features_a, n_frames_a = data_prepare(self.expert_video_path)
            timestamps_a = torch.arange(n_frames_a).float().reshape(1, n_frames_a)

            self.progress_updated.emit("Extracting features from User video...")
            frame_features_b, n_frames_b = data_prepare(self.user_video_path)
            timestamps_b = torch.arange(n_frames_b).float().reshape(1, n_frames_b)

            self.progress_updated.emit("Computing temporal alignment score...")
            s11, s12, s13 = Score_(
                (frame_features_a, timestamps_a, n_frames_a),
                (frame_features_b, timestamps_b, n_frames_b)
            )

            max_score = float(s12.item() if hasattr(s12, 'item') else s12)
            best_frame = int(s13.item() if hasattr(s13, 'item') else s13)

            output_aligned = "result_align.avi"
            self.comparison_completed.emit(max_score, best_frame, output_aligned)
            self.progress_updated.emit(f"Comparison complete! Similarity score: {max_score:.4f}")

        except Exception as e:
            self.error_occurred.emit(f"Error during video comparison: {str(e)}")
