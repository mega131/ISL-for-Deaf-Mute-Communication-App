"""
STEP 4 - Real-Time ISL Detection (Sign -> Text -> Speech)
==========================================================
Uses webcam to detect hand gestures in real-time.
Predicts the ISL character using the trained Keras model.
Allows building words and speaking them out loud using TTS.

Controls:
  SPACE      - Add detected letter to current word
  ENTER      - Speak the word aloud
  BACKSPACE  - Delete last letter
  C          - Clear current word
  Q          - Quit
"""

import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
import pyttsx3
import os

import time

MODEL_DIR = "model"
MODEL_TFLITE = os.path.join(MODEL_DIR, "isl_model.tflite")
LABEL_ENCODER = os.path.join(MODEL_DIR, "label_encoder.npy")

# Initialize TTS
engine = pyttsx3.init()
engine.setProperty('rate', 140)

def speak(text):
    if text.strip():
        engine.say(text)
        engine.runAndWait()

def extract_hand_features(results):
    # Initialize 84 coordinates (42 for Left hand, 42 for Right hand)
    coords = [0.0] * 84
    
    if not results.multi_hand_landmarks:
        return coords

    for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
        # MediaPipe classification labels: 'Left' or 'Right'
        hand_label = results.multi_handedness[i].classification[0].label
        
        # Extract relative coordinates relative to wrist (landmark 0)
        base_x, base_y = hand_landmarks.landmark[0].x, hand_landmarks.landmark[0].y
        rel_coords = []
        for landmark in hand_landmarks.landmark:
            rel_coords.append([landmark.x - base_x, landmark.y - base_y])
        
        # Normalize by max distance to make scale invariant
        flat_coords = [abs(val) for pair in rel_coords for val in pair]
        max_val = max(flat_coords) if max(flat_coords) > 0 else 1.0
        
        normalized = []
        for pair in rel_coords:
            normalized.extend([pair[0] / max_val, pair[1] / max_val])
            
        # Put into correct slot
        if hand_label == 'Left':
            coords[0:42] = normalized
        else:
            coords[42:84] = normalized
            
    return coords

def main():
    if not os.path.exists(MODEL_TFLITE) or not os.path.exists(LABEL_ENCODER):
        print(f"[ERROR] Trained TFLite model not found in '{MODEL_DIR}/'.")
        print("Please run step 1, 2, and 3 first to train the model.")
        return

    print("=" * 50)
    print("  Real-Time ISL Sign -> Text & Speech (Optimized)")
    print("=" * 50)

    # Load TFLite Model & Labels
    print("[INFO] Loading TFLite Model...")
    interpreter = tf.lite.Interpreter(model_path=MODEL_TFLITE)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    class_names = np.load(LABEL_ENCODER, allow_pickle=True)

    # Initialize MediaPipe
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.5)

    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("[ERROR] Could not open webcam.")
        return

    current_word = ""
    current_prediction = ""
    confidence = 0.0

    # Stability tracker state
    last_prediction = "?"
    prediction_stable_since = 0.0
    last_appended_prediction = ""
    STABILITY_THRESHOLD = 1.5  # seconds

    print("[INFO] Webcam active. Press 'Q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, c = frame.shape
        
        # Process Hand Landmarks
        prediction_this_frame = "?"
        confidence_this_frame = 0.0

        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Extract combined 84-dimensional coordinates for both hands
            features = extract_hand_features(results)
            features = np.array([features], dtype=np.float32)
            
            # Predict using TFLite (much faster)
            try:
                interpreter.set_tensor(input_details[0]['index'], features)
                interpreter.invoke()
                preds = interpreter.get_tensor(output_details[0]['index'])[0]
                class_idx = np.argmax(preds)
                confidence_this_frame = float(preds[class_idx])
                
                if confidence_this_frame > 0.6:  # Threshold
                    prediction_this_frame = str(class_names[class_idx])
            except Exception as e:
                print(f"Prediction Error: {e}")

        current_prediction = prediction_this_frame
        confidence = confidence_this_frame

        # Stability Tracker and Auto-Append
        progress = 0.0
        auto_appended = False

        if current_prediction != "?":
            if current_prediction != last_prediction:
                last_prediction = current_prediction
                prediction_stable_since = time.time()
            else:
                elapsed = time.time() - prediction_stable_since
                progress = min(1.0, elapsed / STABILITY_THRESHOLD)
                
                if elapsed >= STABILITY_THRESHOLD and current_prediction != last_appended_prediction:
                    # Auto-append the prediction
                    if len(current_prediction) == 1:
                        current_word += current_prediction
                    else:
                        formatted_word = current_prediction.replace('_', ' ')
                        if current_word and not current_word.endswith(' '):
                            current_word += " "
                        current_word += formatted_word + " "
                    
                    last_appended_prediction = current_prediction
                    auto_appended = True
        else:
            last_prediction = "?"
            last_appended_prediction = ""  # Reset lock when hand is removed

        # Overlay GUI elements
        # Top banner for current word
        cv2.rectangle(frame, (0, 0), (w, 60), (0, 0, 0), -1)
        cv2.putText(frame, f"Word: {current_word}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Bottom left for current prediction
        cv2.rectangle(frame, (0, h - 90), (320, h), (0, 0, 0), -1)
        cv2.putText(frame, f"Sign: {current_prediction} ({confidence*100:.1f}%)", (20, h - 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Draw visual progress bar for hands-free auto-append
        if current_prediction != "?":
            bar_color = (0, 255, 0) if progress < 1.0 else (0, 255, 255)
            # Outline
            cv2.rectangle(frame, (20, h - 35), (280, h - 25), (100, 100, 100), 1)
            # Progress fill
            cv2.rectangle(frame, (20, h - 35), (20 + int(260 * progress), h - 25), bar_color, -1)
            if auto_appended or current_prediction == last_appended_prediction:
                cv2.putText(frame, "LOCKED", (120, h - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
            else:
                cv2.putText(frame, f"Hold still... {progress*100:.0f}%", (20, h - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        # Bottom right for controls info
        cv2.putText(frame, "SPACE:Add | ENTER:Speak | C:Clear | Q:Quit", (10, h - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

        cv2.imshow("Sign to Speech", frame)

        # Handle Keyboard Controls
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q'):
            break
        elif key == 32: # SPACE
            if current_prediction and current_prediction != "?":
                if len(current_prediction) == 1:
                    current_word += current_prediction
                else:
                    formatted_word = current_prediction.replace('_', ' ')
                    if current_word and not current_word.endswith(' '):
                        current_word += " "
                    current_word += formatted_word + " "
                print(f"[INFO] Added -> {current_word}")
        elif key == 13: # ENTER
            if current_word:
                print(f"[INFO] Speaking: {current_word}")
                speak(current_word)
                current_word = "" # Clear after speaking
        elif key == 8: # BACKSPACE
            if len(current_word) > 0:
                current_word = current_word[:-1]
        elif key == ord('c') or key == ord('C'):
            current_word = ""
            print("[INFO] Cleared word.")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
