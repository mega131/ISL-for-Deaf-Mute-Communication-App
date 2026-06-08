import os
import cv2
import time
import json
import mediapipe as mp
import numpy as np
import tensorflow as tf
from flask import Flask, render_template, Response, request, jsonify

app = Flask(__name__)

# Constants and Global State
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
MODEL_DIR = os.path.join(PROJECT_ROOT, "model")
MODEL_TFLITE = os.path.join(MODEL_DIR, "isl_model.tflite")
LABEL_ENCODER = os.path.join(MODEL_DIR, "label_encoder.npy")

current_word = ""
current_prediction = "?"
confidence_score = 0.0

# Stability tracker state
last_prediction = "?"
prediction_stable_since = 0.0
last_appended_prediction = ""
STABILITY_THRESHOLD = 1.5  # seconds

# Load TFLite Model
print("[INFO] Loading TFLite Model...")
try:
    interpreter = tf.lite.Interpreter(model_path=MODEL_TFLITE)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    class_names = np.load(LABEL_ENCODER, allow_pickle=True)
    model_loaded = True
except Exception as e:
    print(f"[ERROR] Could not load TFLite model: {e}")
    model_loaded = False
    interpreter = None
    class_names = []

# Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.5)

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

def generate_frames():
    global current_prediction, confidence_score, current_word
    global last_prediction, prediction_stable_since, last_appended_prediction
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    if not cap.isOpened():
        print("[ERROR] Could not open webcam.")
        return

    while True:
        success, frame = cap.read()
        if not success:
            break
            
        frame = cv2.flip(frame, 1)
        h, w, c = frame.shape
        
        # Process Hand Landmarks
        prediction_this_frame = "?"
        confidence_this_frame = 0.0

        if model_loaded:
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
        confidence_score = confidence_this_frame

        # Stability Tracker and Auto-Append
        if current_prediction != "?":
            if current_prediction != last_prediction:
                last_prediction = current_prediction
                prediction_stable_since = time.time()
            else:
                elapsed = time.time() - prediction_stable_since
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
        else:
            last_prediction = "?"
            last_appended_prediction = ""  # Reset lock when hand is removed

        # Encode frame to JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        # Yield as multipart
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/state')
def get_state():
    global current_word, current_prediction, confidence_score
    return jsonify({
        "current_word": current_word,
        "current_prediction": current_prediction,
        "confidence": confidence_score
    })

@app.route('/action', methods=['POST'])
def handle_action():
    global current_word, current_prediction
    data = request.json
    action = data.get('action')
    
    if action == 'add':
        if current_prediction and current_prediction != "?":
            if len(current_prediction) == 1:
                current_word += current_prediction
            else:
                formatted_word = current_prediction.replace('_', ' ')
                if current_word and not current_word.endswith(' '):
                    current_word += " "
                current_word += formatted_word + " "
    elif action == 'backspace':
        if len(current_word) > 0:
            current_word = current_word[:-1]
    elif action == 'clear':
        current_word = ""
    elif action == 'speak':
        # We will return the current word and clear it, allowing frontend to speak
        word_to_speak = current_word
        current_word = ""
        return jsonify({"status": "success", "word": word_to_speak})
        
    return jsonify({"status": "success", "current_word": current_word})

@app.route('/text_to_sign', methods=['POST'])
def text_to_sign():
    data = request.json
    text = data.get('text', '').upper().strip()
    
    # Extract alphanumeric chars
    chars = [c for c in text if c.isalnum()]
    
    # We will return a list of character strings, frontend will map them to images or placeholders
    return jsonify({"chars": chars})

@app.route('/signs/<filename>')
def get_sign(filename):
    import os
    from flask import send_from_directory
    signs_dir = os.path.join(PROJECT_ROOT, 'isl_signs')
    if not os.path.exists(signs_dir):
        os.makedirs(signs_dir)
    return send_from_directory(signs_dir, filename)

if __name__ == '__main__':

    app.run(debug=True, threaded=True)

# Trigger reload
