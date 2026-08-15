def fingers_up(landmarks):

    if landmarks is None:
        return []

    fingers = []

    # Index finger
    if landmarks[8][1] < landmarks[6][1]:
        fingers.append(1)
    else:
        fingers.append(0)

    # Middle finger
    if landmarks[12][1] < landmarks[10][1]:
        fingers.append(1)
    else:
        fingers.append(0)

    # Ring finger
    if landmarks[16][1] < landmarks[14][1]:
        fingers.append(1)
    else:
        fingers.append(0)

    # Pinky
    if landmarks[20][1] < landmarks[18][1]:
        fingers.append(1)
    else:
        fingers.append(0)

    return fingers


def get_gesture(landmarks):

    fingers = fingers_up(landmarks)

    if not fingers:
        return "none"

    # Index only
    if fingers == [1, 0, 0, 0]:
        return "draw"

    # Index + middle
    if fingers == [1, 1, 0, 0]:
        return "select"

    # All fingers
    if fingers == [1, 1, 1, 1]:
        return "clear"

    # No fingers
    if fingers == [0, 0, 0, 0]:
        return "erase"

    return "none"