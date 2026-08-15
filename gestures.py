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

    index_up = fingers[0] == 1
    middle_up = fingers[1] == 1
    ring_up = fingers[2] == 1
    pinky_up = fingers[3] == 1

    # Fist
    if fingers == [0, 0, 0, 0]:
        return "erase"

    # Open palm
    if fingers == [1, 1, 1, 1]:
        return "clear"

    # Index only
    if index_up and not middle_up and not ring_up and not pinky_up:
        return "draw"

    # Index + middle, allow other fingers to vary a bit
    if index_up and middle_up:
        return "select"

    return "none"
