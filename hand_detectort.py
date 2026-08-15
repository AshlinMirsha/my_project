import cv2
import mediapipe as mp

from config import (
    MAX_HANDS,
    DETECTION_CONFIDENCE,
    TRACKING_CONFIDENCE
)


class HandDetector:

    def __init__(self):

        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=MAX_HANDS,
            min_detection_confidence=DETECTION_CONFIDENCE,
            min_tracking_confidence=TRACKING_CONFIDENCE
        )

    def find_hands(self, frame):

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = self.hands.process(rgb)

        if results.multi_hand_landmarks:

            for hand_landmarks in results.multi_hand_landmarks:

                self.mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS
                )

        return frame, results

    def get_landmarks(self, frame, results):

        if not results.multi_hand_landmarks:
            return None

        hand = results.multi_hand_landmarks[0]

        h, w, _ = frame.shape

        landmarks = []

        for landmark in hand.landmark:

            x = int(landmark.x * w)
            y = int(landmark.y * h)

            landmarks.append((x, y))

        return landmarks