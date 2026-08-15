import cv2
import numpy as np

from config import (
    DEFAULT_BRUSH_SIZE,
    ERASER_SIZE,
    COLORS
)


class DrawingManager:

    def __init__(self, width, height):

        self.canvas = np.zeros(
            (height, width, 3),
            dtype=np.uint8
        )

        self.color = COLORS["blue"]

        self.brush_size = DEFAULT_BRUSH_SIZE

        self.previous_point = None

        self.history = []

    def draw(self, point):

        if point is None:
            self.previous_point = None
            return

        x, y = point

        if self.previous_point is not None:

            px, py = self.previous_point

            cv2.line(
                self.canvas,
                (px, py),
                (x, y),
                self.color,
                self.brush_size,
                cv2.LINE_AA
            )

        self.previous_point = (x, y)

    def erase(self, point):

        if point is None:
            self.previous_point = None
            return

        x, y = point

        cv2.circle(
            self.canvas,
            (x, y),
            ERASER_SIZE,
            (0, 0, 0),
            -1
        )

        self.previous_point = None

    def save_state(self):

        self.history.append(
            self.canvas.copy()
        )

        # Keep only last 20 states
        if len(self.history) > 20:
            self.history.pop(0)

    def undo(self):

        if self.history:

            self.canvas = self.history.pop()

    def clear(self):

        self.canvas = np.zeros_like(self.canvas)

        self.previous_point = None

    def set_color(self, color_name):

        if color_name in COLORS:

            self.color = COLORS[color_name]

    def set_brush_size(self, size):

        self.brush_size = size

    def get_canvas(self):

        return self.canvas

    def save_image(self, filename):

        cv2.imwrite(
            filename,
            self.canvas
        )