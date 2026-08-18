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


FINGER_COLOR_MAP = {
    1: "blue",
    2: "green",
    3: "red",
    4: "yellow",
    5: "white",
}


def count_extended_fingers(landmarks):

    if not landmarks:
        return 0

    count = 0

    # Thumb: the camera is mirrored, so x-position is the most stable signal.
    if landmarks[4][0] < landmarks[3][0]:
        count += 1

    if landmarks[8][1] < landmarks[6][1]:
        count += 1
    if landmarks[12][1] < landmarks[10][1]:
        count += 1
    if landmarks[16][1] < landmarks[14][1]:
        count += 1
    if landmarks[20][1] < landmarks[18][1]:
        count += 1

    return count


def draw_pill(frame, x, y, text, border_color, fill_color=(32, 36, 46), text_color=(245, 247, 250)):

    text_size = cv2.getTextSize(
        text,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        1
    )[0]
    pad_x = 12
    pad_y = 8
    box_w = text_size[0] + pad_x * 2
    box_h = text_size[1] + pad_y * 2

    cv2.rectangle(frame, (x, y), (x + box_w, y + box_h), fill_color, -1)
    cv2.rectangle(frame, (x, y), (x + box_w, y + box_h), border_color, 1)
    cv2.putText(
        frame,
        text,
        (x + pad_x, y + box_h - 9),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        text_color,
        1,
        cv2.LINE_AA
    )


def draw_toolbar(frame, selected_color, finger_count, gesture):

    toolbar_height = 132
    width = frame.shape[1]
    accent = COLORS[selected_color]

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (width, toolbar_height), (16, 18, 24), -1)
    cv2.addWeighted(overlay, 0.9, frame, 0.1, 0, frame)
    cv2.line(frame, (0, toolbar_height), (width, toolbar_height), (84, 92, 106), 1, cv2.LINE_AA)

    cv2.putText(
        frame,
        "AIR CANVAS",
        (22, 38),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (245, 247, 250),
        2,
        cv2.LINE_AA
    )
    cv2.putText(
        frame,
        "Show 1 to 5 fingers to switch color instantly.",
        (22, 62),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.56,
        (196, 204, 214),
        1,
        cv2.LINE_AA
    )

    draw_pill(frame, 22, 76, f"Fingers: {finger_count}", accent, fill_color=(26, 30, 40))
    draw_pill(frame, 152, 76, f"Mode: {gesture.upper()}", accent, fill_color=(26, 30, 40))
    draw_pill(frame, 284, 76, "Index = Draw", (84, 255, 166), fill_color=(26, 30, 40))
    draw_pill(frame, 412, 76, "Fist = Erase", (255, 138, 138), fill_color=(26, 30, 40))
    draw_pill(frame, 536, 76, "Palm = Clear", (255, 220, 120), fill_color=(26, 30, 40))

    palette = [("blue", 682), ("green", 754), ("red", 826), ("yellow", 898), ("white", 970)]

    for name, x in palette:
        color = COLORS[name]
        active = name == selected_color
        outer_color = (245, 247, 250) if active else (82, 88, 100)
        cv2.circle(frame, (x, 102), 25 if active else 21, outer_color, -1)
        cv2.circle(frame, (x, 102), 15 if active else 13, color, -1)
        if active:
            cv2.circle(frame, (x, 102), 29, accent, 2, cv2.LINE_AA)


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
    finger_count = 0

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
    print("1-5 fingers   -> Color selection")
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
        finger_count = count_extended_fingers(landmarks)

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

            picked_color = FINGER_COLOR_MAP.get(finger_count)

            if picked_color and picked_color != selected_color:

                selected_color = picked_color
                drawing.set_color(picked_color)
                print(f"Selected color: {picked_color} ({finger_count} fingers)")

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
            selected_color,
            finger_count,
            gesture
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
            f"Gesture: {gesture} | Fingers: {finger_count}",
            (20, CAMERA_HEIGHT - 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (90, 240, 160),
            2
        )

        cv2.putText(
            output,
            "Tip: show 1-5 fingers to change the active color",
            (20, CAMERA_HEIGHT - 52),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (220, 225, 235),
            1,
            cv2.LINE_AA
        )

        cv2.rectangle(output, (frame_width - 240, CAMERA_HEIGHT - 92), (frame_width - 20, CAMERA_HEIGHT - 24), (20, 24, 30), -1)
        cv2.rectangle(output, (frame_width - 240, CAMERA_HEIGHT - 92), (frame_width - 20, CAMERA_HEIGHT - 24), COLORS[selected_color], 1)
        cv2.putText(output, "ACTIVE COLOR", (frame_width - 222, CAMERA_HEIGHT - 64), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (210, 218, 228), 1, cv2.LINE_AA)
        cv2.putText(output, selected_color.upper(), (frame_width - 222, CAMERA_HEIGHT - 39), cv2.FONT_HERSHEY_SIMPLEX, 0.78, COLORS[selected_color], 2, cv2.LINE_AA)

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
