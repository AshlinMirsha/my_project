import os
import time

try:
    import cv2
    from hand_detector import HandDetector
    from drawing import DrawingManager
    from gestures import get_gesture

    from config import (
        CAMERA_WIDTH,
        CAMERA_HEIGHT,
        COLORS
    )
except ModuleNotFoundError as error:
    missing = error.name or "a required dependency"
    print(f"ERROR: Missing dependency: {missing}")
    print("Run the app with the project virtualenv:")
    print("  source venv/bin/activate")
    print("  python main.py")
    raise SystemExit(1)


def open_camera():

    camera_index = int(os.environ.get("CAMERA_INDEX", "0"))
    max_index = int(os.environ.get("CAMERA_INDEX_MAX", "4"))

    for index in range(camera_index, max_index):

        cap = cv2.VideoCapture(index)

        if cap.isOpened():
            print(f"Using camera index: {index}")
            return cap

        cap.release()

    print("ERROR: No camera could be opened.")
    print("Try setting CAMERA_INDEX to a different device number.")
    print("Example:")
    print("  CAMERA_INDEX=1 python main.py")
    return None


def draw_toolbar(frame, selected_color):

    toolbar_height = 142
    width = frame.shape[1]

    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (0, 0),
        (width, toolbar_height),
        (18, 20, 26),
        -1
    )

    cv2.rectangle(
        overlay,
        (0, 0),
        (width, toolbar_height),
        (255, 255, 255),
        1
    )

    cv2.addWeighted(overlay, 0.88, frame, 0.12, 0, frame)

    cv2.line(
        frame,
        (0, toolbar_height),
        (width, toolbar_height),
        (88, 96, 110),
        1,
        cv2.LINE_AA
    )

    # Title
    cv2.putText(
        frame,
        "AIR CANVAS",
        (22, 36),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    # Instructions
    cv2.putText(
        frame,
        "Draw with one finger. Hover in the top bar to pick a color.",
        (22, 61),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.56,
        (205, 212, 223),
        1,
        cv2.LINE_AA
    )

    # Quick help badges
    badges = [
        ("1F Draw", (84, 255, 166)),
        ("2F Pick", (127, 200, 255)),
        ("Palm Clear", (255, 220, 120)),
        ("Fist Erase", (255, 138, 138)),
    ]

    badge_x = 22
    for label, color in badges:
        text_size = cv2.getTextSize(
            label,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            1
        )[0]
        pad_x = 12
        pad_y = 8
        box_w = text_size[0] + pad_x * 2
        box_h = text_size[1] + pad_y * 2

        cv2.rectangle(frame, (badge_x, 72), (badge_x + box_w, 72 + box_h), (34, 39, 50), -1)
        cv2.rectangle(
            frame,
            (badge_x, 72),
            (badge_x + box_w, 72 + box_h),
            color,
            1
        )
        cv2.putText(
            frame,
            label,
            (badge_x + pad_x, 72 + box_h - 9),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.46,
            (245, 247, 250),
            1,
            cv2.LINE_AA
        )
        badge_x += box_w + 10

    color_positions = {
        "blue": 610,
        "green": 690,
        "red": 770,
        "yellow": 850,
        "white": 930
    }

    for name, x in color_positions.items():
        color = COLORS[name]
        ring_color = (255, 255, 255) if name == selected_color else (78, 84, 96)
        center_radius = 23 if name == selected_color else 19
        ring_radius = 33 if name == selected_color else 28

        cv2.circle(frame, (x, 104), ring_radius, ring_color, -1)
        cv2.circle(frame, (x, 104), center_radius, color, -1)

        if name == selected_color:
            cv2.circle(frame, (x, 104), 34, COLORS[name], 2, cv2.LINE_AA)
            cv2.putText(
                frame,
                name.upper(),
                (x - 28, 132),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                COLORS[name],
                1,
                cv2.LINE_AA
            )

    cv2.putText(
        frame,
        f"Selected: {selected_color.upper()}",
        (width - 220, 36),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.72,
        COLORS[selected_color],
        2,
        cv2.LINE_AA
    )

    cv2.putText(
        frame,
        "1-5 color keys",
        (width - 150, 62),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (205, 212, 223),
        1,
        cv2.LINE_AA
    )


def select_color_from_x(x):

    color_positions = {
        "blue": 610,
        "green": 690,
        "red": 770,
        "yellow": 850,
        "white": 930
    }

    closest_color = None
    closest_distance = None

    for name, center_x in color_positions.items():

        distance = abs(x - center_x)

        if closest_distance is None or distance < closest_distance:

            closest_color = name
            closest_distance = distance

    return closest_color


def main():

    # -----------------------------
    # Camera
    # -----------------------------

    cap = open_camera()

    if cap is None:
        return

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

            # Top bar color picker: use fingertip position directly.
            if point[1] <= 190:

                picked_color = select_color_from_x(point[0])

                if picked_color != selected_color:

                    selected_color = picked_color

                    drawing.set_color(picked_color)

                    print(f"Selected color: {picked_color}")

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
            # Keep the gesture state, but color selection is handled above
            # by fingertip position in the top toolbar.
            pass

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
        canvas = cv2.resize(
            canvas,
            (frame.shape[1], frame.shape[0]),
            interpolation=cv2.INTER_NEAREST
        )

        output = cv2.add(
            frame,
            canvas
        )

        # -----------------------------
        # Status
        # -----------------------------

        frame_width = output.shape[1]

        cv2.putText(
            output,
            f"Gesture: {gesture}",
            (20, CAMERA_HEIGHT - 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (90, 240, 160),
            2
        )

        cv2.putText(
            output,
            "Tip: hover over the top colors to switch ink",
            (20, CAMERA_HEIGHT - 52),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (220, 225, 235),
            1,
            cv2.LINE_AA
        )

        cv2.rectangle(
            output,
            (frame_width - 220, CAMERA_HEIGHT - 82),
            (frame_width - 20, CAMERA_HEIGHT - 24),
            (20, 24, 30),
            -1
        )
        cv2.rectangle(
            output,
            (frame_width - 220, CAMERA_HEIGHT - 82),
            (frame_width - 20, CAMERA_HEIGHT - 24),
            COLORS[selected_color],
            1
        )
        cv2.putText(
            output,
            "ACTIVE COLOR",
            (frame_width - 202, CAMERA_HEIGHT - 56),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (210, 218, 228),
            1,
            cv2.LINE_AA
        )
        cv2.putText(
            output,
            selected_color.upper(),
            (frame_width - 202, CAMERA_HEIGHT - 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            COLORS[selected_color],
            2,
            cv2.LINE_AA
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

            selected_color = "blue"
            drawing.set_color("blue")
            print("Selected color: blue")

        elif key == ord("2"):

            selected_color = "green"
            drawing.set_color("green")
            print("Selected color: green")

        elif key == ord("3"):

            selected_color = "red"
            drawing.set_color("red")
            print("Selected color: red")

        elif key == ord("4"):

            selected_color = "yellow"
            drawing.set_color("yellow")
            print("Selected color: yellow")

        elif key == ord("5"):

            selected_color = "white"
            drawing.set_color("white")
            print("Selected color: white")

    # -----------------------------
    # Cleanup
    # -----------------------------

    cap.release()

    cv2.destroyAllWindows()


if __name__ == "__main__":

    main()
