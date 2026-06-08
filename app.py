import sys
import subprocess
import os
import threading

# 1. Check and Auto-Install Dependencies
def install_requirements():
    required_libs = {
        'flask': 'Flask==3.0.0',
        'flask_socketio': 'flask-socketio==5.6.1',
        'socketio': 'python-socketio==5.16.2',
        'cv2': 'opencv-python==4.8.1.78',
        'mediapipe': 'mediapipe==0.10.7',
        'numpy': 'numpy==1.24.3',
        'tensorflow': 'tensorflow==2.13.0',
        'pyttsx3': 'pyttsx3==2.90',
        'pandas': 'pandas==2.0.3',
        'sklearn': 'scikit-learn==1.3.0',
        'matplotlib': 'matplotlib==3.7.2',
        'speech_recognition': 'SpeechRecognition==3.10.0',
        'PIL': 'Pillow==10.0.0',
        'tqdm': 'tqdm==4.66.1'
    }
    
    missing_libs = []
    for lib_import, pip_name in required_libs.items():
        try:
            __import__(lib_import)
        except ImportError:
            missing_libs.append(pip_name)
            
    if missing_libs:
        print(f"[INFO] Missing dependencies detected: {missing_libs}")
        print("[INFO] Attempting to install them automatically...", flush=True)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_libs])
            print("[INFO] Dependencies installed successfully!", flush=True)
        except Exception as e:
            print(f"[ERROR] Auto-installation failed: {e}")
            print("[ERROR] Please run 'pip install -r requirements.txt' manually.", flush=True)

install_requirements()

# Now we can safely import everything else
import cv2
import time
import json
import mediapipe as mp
import numpy as np
import tensorflow as tf
from flask import Flask, render_template, Response, request, jsonify
from flask_socketio import SocketIO, emit

# Initialize Flask App with custom paths since assets are in the frontend/ directory
app = Flask(__name__, template_folder='frontend/templates', static_folder='frontend/static')
app.config['SECRET_KEY'] = 'isl_secret_key_123'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables for background webcam thread
webcam_thread = None
webcam_running = False
latest_frame_bytes = None
frame_lock = threading.Lock()

# Constants and Global State (relies on root directory structure)
MODEL_DIR = "model"
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

def webcam_capture_loop():
    global latest_frame_bytes, webcam_running
    global current_prediction, confidence_score, current_word
    global last_prediction, prediction_stable_since, last_appended_prediction
    
    print("[INFO] Starting global webcam capture thread...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Global Thread: Could not open webcam.")
        webcam_running = False
        return

    # Set camera resolution to standard 640x480
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while webcam_running:
        success, frame = cap.read()
        if not success:
            time.sleep(0.01)
            continue
            
        frame = cv2.flip(frame, 1)
        
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
        if ret:
            with frame_lock:
                latest_frame_bytes = buffer.tobytes()
        
        time.sleep(0.03)  # Yield CPU thread, control framerate

    cap.release()
    print("[INFO] Global webcam capture thread stopped.")

def start_webcam_thread():
    global webcam_thread, webcam_running
    with frame_lock:
        if webcam_thread is None or not webcam_thread.is_alive():
            webcam_running = True
            webcam_thread = threading.Thread(target=webcam_capture_loop, daemon=True)
            webcam_thread.start()

def generate_frames():
    global latest_frame_bytes
    start_webcam_thread()
    
    while True:
        with frame_lock:
            frame_bytes = latest_frame_bytes
            
        if frame_bytes is None:
            time.sleep(0.1)
            continue
            
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.04)

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
    import re
    data = request.json
    text = data.get('text', '').upper().strip()
    
    signs_dir = os.path.join(os.getcwd(), 'isl_signs')
    allowed_extensions = ['.mp4', '.gif', '.jpg', '.jpeg', '.png']
    
    # 1. Get all available files in signs_dir to know what signs/phrases are supported
    available_signs = {}
    if os.path.exists(signs_dir):
        for filename in os.listdir(signs_dir):
            base, ext = os.path.splitext(filename)
            base_upper = base.upper()
            if ext.lower() in allowed_extensions:
                available_signs[base_upper] = filename

    playlist = []
    
    # We want to match phrases (multi-word gestures) first.
    # Sort keys by number of words descending, then by length descending.
    sorted_phrases = sorted(available_signs.keys(), key=lambda x: (len(x.split()), len(x)), reverse=True)
    
    # Clean input text punctuation but preserve spaces
    # Replace punctuation with spaces to avoid joining words incorrectly, then clean extra spaces
    cleaned_text = re.sub(r'[^\w\s]', ' ', text)
    cleaned_text = ' '.join(cleaned_text.split())
    
    remaining_text = cleaned_text
    
    # Match phrases greedily
    while remaining_text:
        matched = False
        for phrase in sorted_phrases:
            # We want to match whole words/phrases. Use regex word boundaries.
            pattern = rf"\b{re.escape(phrase)}\b"
            match = re.search(pattern, remaining_text)
            if match and match.start() == 0:
                # Matches at the start of remaining_text!
                playlist.append({
                    "type": "word",
                    "label": phrase,
                    "file": available_signs[phrase]
                })
                remaining_text = remaining_text[match.end():].strip()
                matched = True
                break
                
        if not matched:
            # No phrase matched at the start. Extract the first word.
            words = remaining_text.split()
            if not words:
                break
            first_word = words[0]
            
            # Since first_word did not match any available sign (otherwise it would have matched in the phrase loop),
            # we fingerspell it letter by letter.
            for char in first_word:
                if char.isalnum():
                    char_file = f"{char}.jpg"
                    if char in available_signs:
                        char_file = available_signs[char]
                    playlist.append({
                        "type": "char",
                        "label": char,
                        "file": char_file
                    })
            
            # Remove the first word from remaining_text
            remaining_text = remaining_text[len(first_word):].strip()
            
    return jsonify({"playlist": playlist})

@app.route('/signs/<filename>')
def get_sign(filename):
    from flask import send_from_directory
    signs_dir = os.path.join(os.getcwd(), 'isl_signs')
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

@socketio.on('hearing_frame')
def handle_hearing_frame(data):
    emit('receive_hearing_frame', data, broadcast=True, include_self=False)

@socketio.on('clear_chat')
def handle_clear_chat():
    global chat_history
    chat_history = []
    emit('chat_cleared', broadcast=True)

# 2. Open browser automatically when the server runs
def open_browser():
    import time
    import webbrowser
    time.sleep(2.0)
    print("\n[INFO] Opening application in your web browser...", flush=True)
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == '__main__':
    # Start browser opener in a separate thread so it doesn't block the server
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Listen on all interfaces (0.0.0.0) so devices on the local network can connect
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
