import os
import sys
from pathlib import Path
import cv2
import argparse
import numpy as np

# Ensure src in sys.path
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils import score_table
from excerciseType import excerciseType
from yolo_pose import YOLOPoseDetector


def main():
    ap = argparse.ArgumentParser(description="AI Gym Trainer - YOLO11 Pose Real-time Exercise Rep Counter")
    ap.add_argument("-t", "--exercise_type", type=str, required=True,
                    help="Type of activity to do: push-up, pull-up, squat, sit-up, walk")
    ap.add_argument("-vs", "--video_source", type=str, required=False, default=None,
                    help="Path to input video file (omit to use live webcam)")
    ap.add_argument("-vo", "--video_output", type=str, required=False, default=None,
                    help="Path to save annotated output video")
    ap.add_argument("-m", "--model", type=str, required=False, default=None,
                    help="Path or name of YOLO11 pose model (default: yolo11n-pose.pt)")
    ap.add_argument("--conf", type=float, required=False, default=0.35,
                    help="Confidence threshold for YOLO11 keypoints (default: 0.35)")

    args = vars(ap.parse_args())

    exercise_type = args["exercise_type"]
    print("=" * 60)
    print("       AI Gym Trainer - YOLO11 Pose Detection Engine")
    print("=" * 60)
    print(f"  Exercise       : {exercise_type}")
    print(f"  Source         : {args['video_source'] if args['video_source'] else 'Live Webcam (0)'}")
    print(f"  Output         : {args['video_output'] if args['video_output'] else 'Display Only'}")
    print("  Model          : YOLO11 Pose (yolo11n-pose.pt)")
    print("  Controls       : Press 'q' in video window to exit.")
    print("=" * 60)

    # Initialize YOLO11 Pose Detector
    detector = YOLOPoseDetector(model_path=args["model"])

    # Video Capture
    if args["video_source"] is not None:
        cap = cv2.VideoCapture(args["video_source"])
    else:
        cap = cv2.VideoCapture(0)  # webcam

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    if fps <= 0 or fps > 120:
        fps = 30

    out = None
    if args["video_output"]:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(args["video_output"], fourcc, fps, (800, 480))

    counter = 0
    status = True

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or frame is None or not np.any(frame):
                break

            frame = cv2.resize(frame, (800, 480), interpolation=cv2.INTER_AREA)

            # YOLO11 Pose Inference
            annotated_frame, landmarks = detector.process(frame, conf=args["conf"])

            if landmarks is not None:
                try:
                    counter, status = excerciseType(landmarks).calculate_exercise(
                        exercise_type, counter, status
                    )
                except Exception as e:
                    pass

            # Overlay repetition score HUD
            display_frame = score_table(exercise_type, annotated_frame, counter, status)

            # Add YOLO11 Badge overlay
            cv2.putText(display_frame, "Engine: YOLO11 Pose", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 100, 0), 2, cv2.LINE_AA)

            if out is not None:
                out.write(display_frame)

            cv2.imshow("AI Gym Trainer - YOLO11 Pose", display_frame)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        if out is not None:
            out.release()
        cv2.destroyAllWindows()
        print(f"\nSession finished! Total {exercise_type} reps counted: {counter}")


if __name__ == "__main__":
    main()
