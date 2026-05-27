import argparse
import os

import cv2
import dlib
import numpy as np

DLIB_MODEL    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shape_predictor_68_face_landmarks.dat")
EAR_THRESHOLD = 0.2


def _dist(a, b):
    return np.linalg.norm(np.array(a, dtype=float) - np.array(b, dtype=float))


def eye_aspect_ratio(eye):
    return (_dist(eye[1], eye[5]) + _dist(eye[2], eye[4])) / (2.0 * _dist(eye[0], eye[3]))


def nose_center_ratio(lm):
    """코 끝(30번) x가 양쪽 눈 중심 x 사이에서 얼마나 가운데인지. 0.5 = 정중앙."""
    left_cx  = sum(lm[i][0] for i in range(36, 42)) / 6.0
    right_cx = sum(lm[i][0] for i in range(42, 48)) / 6.0
    if right_cx == left_cx:
        return 0.5
    return (lm[30][0] - left_cx) / (right_cx - left_cx)


def main(args):
    if not os.path.isfile(DLIB_MODEL):
        raise FileNotFoundError(f"dlib model not found: {DLIB_MODEL}")

    detector        = dlib.get_frontal_face_detector()
    shape_predictor = dlib.shape_predictor(DLIB_MODEL)
    print("[INFO] Models loaded. Press 'q' to quit.")

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera (ID={args.camera})")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        h, w = frame.shape[:2]
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray, 1)

        if faces:
            rect  = faces[0]
            shape = shape_predictor(gray, rect)
            lm    = [(shape.part(i).x, shape.part(i).y) for i in range(68)]

            ear   = (eye_aspect_ratio(lm[36:42]) + eye_aspect_ratio(lm[42:48])) / 2.0
            ratio = nose_center_ratio(lm)

            x1 = max(0, rect.left());  y1 = max(0, rect.top())
            x2 = min(w, rect.right()); y2 = min(h, rect.bottom())
            box_color = (0, 200, 60) if (ear > EAR_THRESHOLD and 0.4 <= ratio <= 0.6) else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)

            for (lx, ly) in lm:
                cv2.circle(frame, (lx, ly), 1, (0, 200, 255), -1)

            cv2.putText(frame, f"EAR: {ear:.3f}  NoseRatio: {ratio:.3f}", (10, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (220, 220, 220), 2, cv2.LINE_AA)

            if ear < EAR_THRESHOLD:
                cv2.putText(frame, "Closed Eyes", (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
        else:
            cv2.putText(frame, "No face detected", (10, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (80, 80, 255), 2, cv2.LINE_AA)

        cv2.imshow("EAR Monitor", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--width",  type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    main(parser.parse_args())
