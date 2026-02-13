import cv2
import numpy as np
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True
)

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]


def calculate_ear(landmarks, eye_indices):
    p1 = np.array(landmarks[eye_indices[1]])
    p2 = np.array(landmarks[eye_indices[5]])
    p3 = np.array(landmarks[eye_indices[2]])
    p4 = np.array(landmarks[eye_indices[4]])
    p0 = np.array(landmarks[eye_indices[0]])
    p3h = np.array(landmarks[eye_indices[3]])

    vertical1 = np.linalg.norm(p1 - p2)
    vertical2 = np.linalg.norm(p3 - p4)
    horizontal = np.linalg.norm(p0 - p3h)

    if horizontal == 0:
        return 0

    return (vertical1 + vertical2) / (2.0 * horizontal)


def verify_action(frame_paths, action):

    blink_detected = False
    head_left = False
    head_right = False
    nose_positions = []

    for path in frame_paths:
        img = cv2.imread(path)
        if img is None:
            continue

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            continue

        landmarks = results.multi_face_landmarks[0].landmark
        h, w, _ = img.shape
        coords = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

        # ---- Blink Detection ----
        left_ear = calculate_ear(coords, LEFT_EYE)
        right_ear = calculate_ear(coords, RIGHT_EYE)
        ear = (left_ear + right_ear) / 2

        if ear < 0.20:
            blink_detected = True

        # ---- Head Movement Tracking ----
        nose_positions.append(coords[1][0])

    # ---- Head Turn Detection ----
    if len(nose_positions) > 1:
        movement = max(nose_positions) - min(nose_positions)

        if movement > 25:
            if nose_positions[-1] < nose_positions[0]:
                head_left = True
            if nose_positions[-1] > nose_positions[0]:
                head_right = True

    if action == "blink":
        return {"success": blink_detected}

    if action == "left":
        return {"success": head_left}

    if action == "right":
        return {"success": head_right}

    return {"success": False}
