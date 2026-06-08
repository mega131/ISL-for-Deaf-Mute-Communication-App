import os
import cv2
import time
import json
import mediapipe as mp
import numpy as np
import tensorflow as tf
from flask import Flask, render_template, Response, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'isl_secret_key_123'
socketio = SocketIO(app, cors_allowed_origins="*")

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

# Chat history storage
chat_history = []

# Load TFLite Model
print("[INFO] Loading TFLite Model for Chat Server...")
try:
    interpreter = tf.lite.Interpreter(model_path=MODEL_TFLITE)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    class_names = np.load(LABEL_ENCODER, allow_pickle=True)
    model_loaded = True
    print(f"[INFO] TFLite model loaded successfully with {len(class_names)} classes.")
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
    coords = [0.0] * 84
    if not results.multi_hand_landmarks:
        return coords

    for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
        hand_label = results.multi_handedness[i].classification[0].label
        base_x, base_y = hand_landmarks.landmark[0].x, hand_landmarks.landmark[0].y
        rel_coords = []
        for landmark in hand_landmarks.landmark:
            rel_coords.append([landmark.x - base_x, landmark.y - base_y])
        
        flat_coords = [abs(val) for pair in rel_coords for val in pair]
        max_val = max(flat_coords) if max(flat_coords) > 0 else 1.0
        
        normalized = []
        for pair in rel_coords:
            normalized.extend([pair[0] / max_val, pair[1] / max_val])
            
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
                
                features = extract_hand_features(results)
                features = np.array([features], dtype=np.float32)
                
                try:
                    interpreter.set_tensor(input_details[0]['index'], features)
                    interpreter.invoke()
                    preds = interpreter.get_tensor(output_details[0]['index'])[0]
                    class_idx = np.argmax(preds)
                    confidence_this_frame = float(preds[class_idx])
                    
                    if confidence_this_frame > 0.6:
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
            last_appended_prediction = ""

        # Encode frame to JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.03)  # Yield CPU thread to prevent Socket.IO and route blocking

    cap.release()

@app.route('/')
def index():
    return render_template('chat.html')

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
        
    return jsonify({"status": "success", "current_word": current_word})

@app.route('/text_to_sign', methods=['POST'])
def text_to_sign():
    data = request.json
    text = data.get('text', '').upper().strip()
    chars = [c for c in text if c.isalnum()]
    return jsonify({"chars": chars})

@app.route('/signs/<filename>')
def get_sign(filename):
    from flask import send_from_directory
    signs_dir = os.path.join(PROJECT_ROOT, 'isl_signs')
    if not os.path.exists(signs_dir):
        os.makedirs(signs_dir)
    return send_from_directory(signs_dir, filename)

# WebSocket Event Handlers
@socketio.on('connect')
def handle_connect():
    print(f"[SOCKET] Client connected: {request.sid}")
    # Send existing history to the newly connected user
    emit('history', chat_history)

@socketio.on('join')
def handle_join(data):
    username = data.get('username', 'Anonymous')
    role = data.get('role', 'hearing')
    print(f"[SOCKET] {username} ({role}) joined the chat.")
    emit('user_joined', {'username': username, 'role': role}, broadcast=True)

@socketio.on('send_message')
def handle_message(data):
    text = data.get('text', '').strip()
    sender = data.get('sender', 'Anonymous')
    role = data.get('role', 'hearing')
    
    if text:
        msg = {
            'text': text,
            'sender': sender,
            'role': role,
            'time': time.strftime("%H:%M")
        }
        chat_history.append(msg)
        emit('receive_message', msg, broadcast=True)

@socketio.on('clear_chat')
def handle_clear_chat():
    global chat_history
    chat_history = []
    emit('chat_cleared', broadcast=True)

if __name__ == '__main__':
    # Listen on all interfaces (0.0.0.0) so mobiles on local network can connect
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
