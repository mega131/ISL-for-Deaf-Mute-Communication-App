import os
import cv2
import time
import json
import threading
import mediapipe as mp
import numpy as np
import tensorflow as tf
from flask import Flask, render_template, Response, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'isl_secret_key_123'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables for background webcam thread
webcam_thread = None
webcam_running = False
latest_frame_bytes = None
frame_lock = threading.Lock()


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

# Multilingual Translation Engine & Pre-cached Regional Dictionary
OFFLINE_TRANSLATIONS = {
    'HELLO': {'hi': 'नमस्ते', 'ta': 'வணக்கம்', 'te': 'నమస్కారం', 'mr': 'नमस्कार', 'bn': 'নমস্কার', 'gu': 'નમસ્તે', 'kn': 'ನಮಸ್ಕಾರ', 'ml': 'നമസ്കാരം', 'pa': 'ਸਤ ਸ੍ਰੀ ਅਕਾਲ', 'es': 'Hola', 'fr': 'Bonjour', 'de': 'Hallo', 'ar': 'مرحبا'},
    'THANK YOU': {'hi': 'धन्यवाद', 'ta': 'நன்றி', 'te': 'ధన్యవాదాలు', 'mr': 'धन्यवाद', 'bn': 'ধন্যবাদ', 'gu': 'આભાર', 'kn': 'ಧನ್ಯವಾದಗಳು', 'ml': 'നന്ദി', 'pa': 'ਧੰਨਵਾਦ', 'es': 'Gracias', 'fr': 'Merci', 'de': 'Danke', 'ar': 'شكرا'},
    'HELP': {'hi': 'मदद', 'ta': 'உதவி', 'te': 'సహాయం', 'mr': 'मदत', 'bn': 'সাহায্য', 'gu': 'મદદ', 'kn': 'ಸಹಾಯ', 'ml': 'സಹాయം', 'pa': 'ਮਦਦ', 'es': 'Ayuda', 'fr': 'Aide', 'de': 'Hilfe', 'ar': 'مساعدة'},
    'YES': {'hi': 'हाँ', 'ta': 'ஆம்', 'te': 'అవును', 'mr': 'होय', 'bn': 'হ্যাঁ', 'gu': 'હા', 'kn': 'ಹೌದು', 'ml': 'അതെ', 'pa': 'ਹਾਂ', 'es': 'Sí', 'fr': 'Oui', 'de': 'Ja', 'ar': 'نعم'},
    'NO': {'hi': 'नहीं', 'ta': 'இல்லை', 'te': 'కాదు', 'mr': 'नाही', 'bn': 'না', 'gu': 'ના', 'kn': 'ಇಲ್ಲ', 'ml': 'ഇല്ല', 'pa': 'ਨਹੀਂ', 'es': 'No', 'fr': 'Non', 'de': 'Nein', 'ar': 'لا'},
    'GOODBYE': {'hi': 'अलविदा', 'ta': 'பிரியாவிடை', 'te': 'వీడ్కోలు', 'mr': 'निरोप', 'bn': 'বিদায়', 'gu': 'આવજો', 'kn': 'ವಿದಾಯ', 'ml': 'വിട', 'pa': 'ਅਲਵਿਦਾ', 'es': 'Adiós', 'fr': 'Au revoir', 'de': 'Auf Wiedersehen', 'ar': 'وداعا'},
    'PLEASE': {'hi': 'कृपया', 'ta': 'தயவுசெய்து', 'te': 'దయచేసి', 'mr': 'कृपया', 'bn': 'দয়া করে', 'gu': 'કૃપા કરીને', 'kn': 'ದಯವಿಟ್ಟು', 'ml': 'ദയവായി', 'pa': 'ਕਿਰਪਾ ਕਰਕੇ', 'es': 'Por favor', 'fr': 'S\'il vous plaît', 'de': 'Bitte', 'ar': 'من فضلك'},
}

def translate_text(text, target_lang='en', source_lang='auto'):
    """Translates text seamlessly between English and Indian/Global languages."""
    if not text or not str(text).strip():
        return text
    
    text = str(text).strip()
    if target_lang == source_lang:
        return text
    if target_lang == 'en' and all(ord(c) < 128 for c in text):
        return text

    upper_key = text.upper()
    if upper_key in OFFLINE_TRANSLATIONS and target_lang in OFFLINE_TRANSLATIONS[upper_key]:
        return OFFLINE_TRANSLATIONS[upper_key][target_lang]

    if target_lang == 'en':
        for en_word, lang_dict in OFFLINE_TRANSLATIONS.items():
            if any(text == trans or text.lower() == trans.lower() for trans in lang_dict.values()):
                return en_word

    try:
        import urllib.request
        import urllib.parse
        encoded_q = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source_lang}&tl={target_lang}&dt=t&q={encoded_q}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=3.5) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            if res_data and isinstance(res_data, list) and len(res_data) > 0 and isinstance(res_data[0], list):
                translated = "".join([segment[0] for segment in res_data[0] if segment and segment[0]])
                if translated:
                    return translated
    except Exception as e:
        print(f"[INFO] Translate fallback for '{text}': {e}")

    return text

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
        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
        if ret:
            frame_bytes = buffer.tobytes()
            with frame_lock:
                latest_frame_bytes = frame_bytes
                
            # Broadcast live sign camera frames directly via WebSocket to both Laptop & Mobile in real-time
            try:
                import base64
                b64_frame = "data:image/jpeg;base64," + base64.b64encode(frame_bytes).decode('utf-8')
                socketio.emit('receive_deaf_frame', {'frame': b64_frame})
            except Exception:
                pass
        
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

@app.route('/translate', methods=['POST'])
def handle_translate():
    data = request.json or {}
    text = data.get('text', '')
    target_lang = data.get('target_lang', 'en')
    source_lang = data.get('source_lang', 'auto')
    
    if not text:
        return jsonify({"original": "", "translated": "", "target_lang": target_lang})
        
    translated = translate_text(text, target_lang=target_lang, source_lang=source_lang)
    return jsonify({
        "original": text,
        "translated": translated,
        "source_lang": source_lang,
        "target_lang": target_lang
    })

@app.route('/text_to_sign', methods=['POST'])
def text_to_sign():
    data = request.json or {}
    raw_text = data.get('text', '').strip()
    
    # Multilingual: Translate regional language text to English for ISL signs
    has_non_ascii = any(ord(c) > 127 for c in raw_text)
    if has_non_ascii:
        translated_en = translate_text(raw_text, target_lang='en', source_lang='auto')
        text = translated_en.upper().strip()
    else:
        text = raw_text.upper().strip()
    
    signs_dir = os.path.join(PROJECT_ROOT, 'isl_signs')
    allowed_extensions = ['.mp4', '.gif', '.jpg', '.jpeg', '.png']
    playlist = []
    
    words = [w.strip() for w in text.split() if w.strip()]
    for word in words:
        found_file = None
        for ext in allowed_extensions:
            filename = f"{word}{ext}"
            filepath = os.path.join(signs_dir, filename)
            if os.path.exists(filepath):
                found_file = filename
                break
        
        if found_file:
            playlist.append({
                "type": "word",
                "label": word,
                "file": found_file
            })
        else:
            # Fallback to character fingerspelling for this word
            for char in word:
                if char.isalnum():
                    playlist.append({
                        "type": "char",
                        "label": char,
                        "file": f"{char}.jpg"
                    })
                    
    return jsonify({"playlist": playlist})

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
    target_lang = data.get('target_lang', 'en')
    
    if text:
        translated_text = ""
        if target_lang and target_lang != 'en':
            translated_text = translate_text(text, target_lang=target_lang)
            
        msg = {
            'text': text,
            'translated_text': translated_text,
            'target_lang': target_lang,
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

if __name__ == '__main__':
    # Listen on all interfaces (0.0.0.0) so mobiles on local network can connect
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
