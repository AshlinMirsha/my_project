import cv2
import mediapipe as mp
import time

from config import (
    MAX_HANDS,
    DETECTION_CONFIDENCE,
    TRACKING_CONFIDENCE
)

#the hand detector
class HandDetector:

    def __init__(self):

        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path="hand_landmarker.task"
            ),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=MAX_HANDS,
            min_hand_detection_confidence=DETECTION_CONFIDENCE,
            min_hand_presence_confidence=DETECTION_CONFIDENCE,
            min_tracking_confidence=TRACKING_CONFIDENCE
        )

        self.detector = mp.tasks.vision.HandLandmarker.create_from_options(
            options
        )

    def find_hands(self, frame):

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        timestamp = int(time.time() * 1000)

        results = self.detector.detect_for_video(
            mp_image,
            timestamp
        )

        return frame, results

    def get_landmarks(self, frame, results):

        if not results.hand_landmarks:
            return None

        hand = results.hand_landmarks[0]

        h, w, _ = frame.shape

        landmarks = []

        for landmark in hand:

            x = int(landmark.x * w)
            y = int(landmark.y * h)

            landmarks.append((x, y))

        return landmarks
