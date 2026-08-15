import cv2
import os
import time

from hand_detector import HandDetector
from drawing import DrawingManager
from gestures import get_gesture

from config import (
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    COLORS
)


def draw_toolbar(frame, selected_color):

    toolbar_height = 80

    cv2.rectangle(
        frame,
        (0, 0),
        (frame.shape[1], toolbar_height),
        (40, 40, 40),
        -1
    )

    # Title
    cv2.putText(
        frame,
        "AIR CANVAS",
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    # Instructions
    cv2.putText(
        frame,
        "1F: Draw | 2F: Select | Palm: Clear | Fist: Erase",
        (250, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (220, 220, 220),
        1
    )

    # Colors
    color_positions = {
        "blue": 600,
        "green": 670,
        "red": 740,
        "yellow": 810,
        "white": 880
    }

    for name, x in color_positions.items():

        color = COLORS[name]

        cv2.circle(
            frame,
            (x, 45),
            18,
            color,
            -1
        )

        if name == selected_color:

            cv2.circle(
                frame,
                (x, 45),
                23,
                (255, 255, 255),
                2
            )


def main():

    # -----------------------------
    # Camera
    # -----------------------------

    cap = cv2.VideoCapture(0)

    cap.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        CAMERA_WIDTH
    )

    cap.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        CAMERA_HEIGHT
    )

    if not cap.isOpened():

        print("ERROR: Camera could not be opened.")

        return

    # -----------------------------
    # Initialize
    # -----------------------------

    detector = HandDetector()

    drawing = DrawingManager(
        CAMERA_WIDTH,
        CAMERA_HEIGHT
    )

    selected_color = "blue"

    previous_gesture = "none"

    os.makedirs(
        "drawings/saved",
        exist_ok=True
    )

    print()
    print("================================")
    print("        AIR CANVAS")
    print("================================")
    print()
    print("Controls:")
    print("Index finger  -> Draw")
    print("Two fingers   -> Color selection")
    print("Open palm     -> Clear")
    print("Fist          -> Eraser")
    print("U             -> Undo")
    print("S             -> Save")
    print("C             -> Clear")
    print("Q             -> Quit")
    print()

    # -----------------------------
    # Main Loop
    # -----------------------------

    while True:

        success, frame = cap.read()

        if not success:
            print("Could not read camera frame.")
            break

        # Mirror camera
        frame = cv2.flip(frame, 1)

        # Detect hand
        frame, results = detector.find_hands(frame)

        # Get landmarks
        landmarks = detector.get_landmarks(
            frame,
            results
        )

        # Detect gesture
        gesture = get_gesture(landmarks)

        # Finger position
        point = None

        if landmarks:

            # Index fingertip
            point = landmarks[8]

            # Draw pointer
            cv2.circle(
                frame,
                point,
                10,
                (0, 255, 0),
                -1
            )

        # -----------------------------
        # Gesture Handling
        # -----------------------------

        if gesture == "draw":

            drawing.draw(point)

        elif gesture == "erase":

            drawing.erase(point)

        elif gesture == "clear":

            if previous_gesture != "clear":

                drawing.save_state()

                drawing.clear()

        elif gesture == "select":

            # Use index fingertip for color selection
            if point:

                x, y = point

                # Color areas
                if 580 < x < 640:

                    selected_color = "blue"

                    drawing.set_color("blue")

                elif 640 < x < 710:

                    selected_color = "green"

                    drawing.set_color("green")

                elif 710 < x < 780:

                    selected_color = "red"

                    drawing.set_color("red")

                elif 780 < x < 850:

                    selected_color = "yellow"

                    drawing.set_color("yellow")

                elif 850 < x < 920:

                    selected_color = "white"

                    drawing.set_color("white")

            drawing.previous_point = None

        else:

            drawing.previous_point = None

        previous_gesture = gesture

        # -----------------------------
        # Toolbar
        # -----------------------------

        draw_toolbar(
            frame,
            selected_color
        )

        # -----------------------------
        # Combine camera and canvas
        # -----------------------------

        canvas = drawing.get_canvas()

        output = cv2.add(
            frame,
            canvas
        )

        # -----------------------------
        # Status
        # -----------------------------

        cv2.putText(
            output,
            f"Gesture: {gesture}",
            (20, CAMERA_HEIGHT - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        # -----------------------------
        # Display
        # -----------------------------

        cv2.imshow(
            "AirCanvas - OpenCV",
            output
        )

        # -----------------------------
        # Keyboard
        # -----------------------------

        key = cv2.waitKey(1) & 0xFF

        # Quit
        if key == ord("q"):

            break

        # Clear
        elif key == ord("c"):

            drawing.save_state()

            drawing.clear()

        # Undo
        elif key == ord("u"):

            drawing.undo()

        # Save
        elif key == ord("s"):

            filename = (
                "drawings/saved/"
                f"drawing_{int(time.time())}.png"
            )

            drawing.save_image(
                filename
            )

            print(
                f"Drawing saved: {filename}"
            )

        # Brush sizes
        elif key == ord("1"):

            drawing.set_brush_size(5)

        elif key == ord("2"):

            drawing.set_brush_size(10)

        elif key == ord("3"):

            drawing.set_brush_size(20)

    # -----------------------------
    # Cleanup
    # -----------------------------

    cap.release()

    cv2.destroyAllWindows()


if __name__ == "__main__":

    main()