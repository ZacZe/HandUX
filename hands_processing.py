import mediapipe as mp

# mediapipe setup
mpHands = mp.solutions.hands
Draw = mp.solutions.drawing_utils

def init_hands(num_hands): 
    return mpHands.Hands(
        static_image_mode=False,
        model_complexity=0,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
        max_num_hands=num_hands
    )

def process_hands(frame, results, display_skeleton): 
    hands_data = []
    if results.multi_hand_landmarks and results.multi_handedness:
        for handlm, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            h, w, _ = frame.shape
            lm_list = []
            for _id, lm in enumerate(handlm.landmark):
                x, y = int(lm.x * w), int(lm.y * h)
                lm_list.append([_id, x, y])

            # assign left or right hand
            hands_data.append({
                "label": handedness.classification[0].label, # "Left" or "Right"
                "landmarks": lm_list
            })

            if display_skeleton:
                Draw.draw_landmarks(frame, handlm, mpHands.HAND_CONNECTIONS)

    return hands_data