import os
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO


class LandmarkPoint:
    """Lightweight Landmark object matching MediaPipe's interface (.x, .y, .visibility)."""
    def __init__(self, x=0.0, y=0.0, visibility=0.0):
        self.x = float(x)
        self.y = float(y)
        self.visibility = float(visibility)

    def __repr__(self):
        return f"Landmark(x={self.x:.3f}, y={self.y:.3f}, vis={self.visibility:.2f})"


# COCO-17 to MediaPipe-33 Mapping
COCO_TO_MEDIAPIPE = {
    0: 0,   # NOSE
    1: 2,   # LEFT_EYE
    2: 5,   # RIGHT_EYE
    3: 7,   # LEFT_EAR
    4: 8,   # RIGHT_EAR
    5: 11,  # LEFT_SHOULDER
    6: 12,  # RIGHT_SHOULDER
    7: 13,  # LEFT_ELBOW
    8: 14,  # RIGHT_ELBOW
    9: 15,  # LEFT_WRIST
    10: 16, # RIGHT_WRIST
    11: 23, # LEFT_HIP
    12: 24, # RIGHT_HIP
    13: 25, # LEFT_KNEE
    14: 26, # RIGHT_KNEE
    15: 27, # LEFT_ANKLE
    16: 28, # RIGHT_ANKLE
}


class YOLOPoseDetector:
    """YOLO11 Pose Estimation Detector replacing YOLOv7 with higher accuracy and real-time inference."""
    def __init__(self, model_path=None):
        if model_path is None:
            # Check local root or fallback to yolo11n-pose
            root_weight = Path(__file__).resolve().parents[1] / "yolo11n-pose.pt"
            if root_weight.exists():
                model_path = str(root_weight)
            else:
                model_path = "yolo11n-pose.pt"
        self.model = YOLO(model_path)

    def process(self, frame_bgr, conf=0.3):
        """
        Runs YOLO11 pose estimation on a BGR frame.
        
        Returns:
            annotated_frame (np.ndarray): Frame with YOLO11 keypoints and skeleton overlay.
            landmarks (list[LandmarkPoint] | None): 33 landmarks compatible with excerciseType.
        """
        h, w = frame_bgr.shape[:2]
        results = self.model(frame_bgr, conf=conf, verbose=False)

        if not results or len(results) == 0:
            return frame_bgr, None

        res = results[0]
        if res.keypoints is None or len(res.keypoints) == 0 or res.keypoints.data.shape[0] == 0:
            return frame_bgr, None

        # Select primary detected person
        kpts = res.keypoints.data[0].cpu().numpy()  # shape (17, 3) [x, y, conf]

        # Construct MediaPipe-compatible 33 landmark structure
        landmarks = [LandmarkPoint(0.0, 0.0, 0.0) for _ in range(33)]

        for coco_idx, mp_idx in COCO_TO_MEDIAPIPE.items():
            px, py, c = kpts[coco_idx]
            norm_x = float(px / w) if w > 0 else 0.0
            norm_y = float(py / h) if h > 0 else 0.0
            landmarks[mp_idx] = LandmarkPoint(x=norm_x, y=norm_y, visibility=float(c))

        # Approximate mouth keypoints from nose and shoulders for neck angle
        nose = landmarks[0]
        l_sh = landmarks[11]
        r_sh = landmarks[12]
        mouth_y = (nose.y * 2.0 + (l_sh.y + r_sh.y) / 2.0) / 3.0
        landmarks[9] = LandmarkPoint(x=nose.x, y=mouth_y, visibility=nose.visibility)
        landmarks[10] = LandmarkPoint(x=nose.x, y=mouth_y, visibility=nose.visibility)

        # Plot YOLO11 native high-accuracy skeleton & keypoint overlay
        try:
            annotated_frame = res.plot(labels=False, boxes=False)
        except Exception:
            annotated_frame = frame_bgr

        return annotated_frame, landmarks

