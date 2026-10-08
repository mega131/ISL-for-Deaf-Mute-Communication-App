import sys
import os
from fpdf import FPDF

class STARPrepPDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return # Skip header on cover page
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(100, 110, 120)
        self.cell(0, 6, 'ISL Communication Assistant - Final Year Project STAR Prep Guide', 0, 1, 'L')
        self.set_font('Helvetica', '', 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 4, 'CSE / B.Tech Final Year Placement Prep', 0, 1, 'L')
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.4)
        self.line(10, 22, 200, 22)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        # We draw a line above the footer
        self.set_draw_color(220, 220, 220)
        self.line(10, 280, 200, 280)
        self.cell(0, 10, f'Page {self.page_no()} of {{nb}}', 0, 0, 'C')
        self.cell(0, 10, 'Strictly Private & Confidential', 0, 0, 'R')

def build_pdf(filepath):
    pdf = STARPrepPDF()
    pdf.alias_nb_pages()
    pdf.set_margins(15, 20, 15)
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # ------------------ COVER PAGE ------------------
    pdf.add_page()
    pdf.ln(25)
    
    # Title Block
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(22, 54, 87) # Deep Navy Blue
    pdf.multi_cell(0, 10, 'STAR Interview Preparation Guide', 0, 'C')
    pdf.ln(5)
    
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(0, 150, 136) # Teal
    pdf.cell(0, 10, 'Indian Sign Language (ISL) Communication Assistant', 0, 1, 'C')
    pdf.ln(10)
    
    # Horizontal Rule
    pdf.set_draw_color(0, 150, 136)
    pdf.set_line_width(1.5)
    pdf.line(40, 65, 170, 65)
    pdf.ln(10)
    
    # Subtitle Info
    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 7, 'A comprehensive project analysis for technical and HR interviews, structured according to the Situation, Task, Action, and Result (STAR) framework. Includes a 30-second elevator pitch, key implementation methodologies, architectural decisions, and an exhaustive list of follow-up technical questions with detailed answers.', 0, 'C')
    pdf.ln(25)
    
    # Details Box (with light grey background)
    pdf.set_fill_color(245, 247, 250)
    pdf.set_draw_color(220, 224, 230)
    pdf.set_line_width(0.5)
    pdf.rect(20, 120, 170, 75, style='FD')
    
    pdf.set_xy(25, 125)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(22, 54, 87)
    pdf.cell(0, 8, 'PROJECT METADATA SUMMARY', 0, 1, 'L')
    pdf.ln(2)
    
    # Key-Value lines
    details = [
        ("Project Name:", "Indian Sign Language (ISL) Communication Assistant"),
        ("Problem Solved:", "Bidirectional communication gap for Deaf and Mute individuals"),
        ("Tech Stack:", "Python, Flask, Flask-SocketIO, MediaPipe, TensorFlow (Keras/TFLite), OpenCV"),
        ("Model Details:", "Dense Feedforward Neural Network (84 Inputs -> 128 -> 64 -> 35 Outputs)"),
        ("Accuracy:", "95% - 99% Test Accuracy on 35 classes (A-Z, 1-9)"),
        ("Target Role:", "Software Engineer / ML Engineer (Fresher/Student Interview)"),
        ("Team Size:", "[NEED INFORMATION]"),
        ("My Contribution:", "[NEED INFORMATION] (Core focus: Normalization, Stability, WebSockets & TFLite)")
    ]
    
    for label, val in details:
        pdf.set_x(25)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(35, 6, label, 0, 0, 'L')
        pdf.set_font('Helvetica', '', 9)
        pdf.multi_cell(125, 6, val, 0, 'L')
        
    pdf.set_y(-30)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, 'Generated in August 2026. Prepared for upcoming placement interviews.', 0, 1, 'C')
    
    # ------------------ SECTION 1: PROJECT INTRODUCTION ------------------
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(22, 54, 87)
    pdf.cell(0, 10, '1. Project Introduction', 0, 1, 'L')
    pdf.ln(2)
    
    # 30-Second Elevator Pitch
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 150, 136)
    pdf.cell(0, 8, 'The 30-Second Elevator Pitch ("Tell me about your project")', 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_fill_color(240, 248, 255) # Ice blue background
    pdf.set_draw_color(173, 216, 230)
    pdf.set_line_width(0.8)
    pdf.set_font('Helvetica', 'I', 10)
    pdf.set_text_color(40, 40, 40)
    
    pitch_text = (
        "\"For my final year project, I developed an Indian Sign Language Communication Assistant to bridge "
        "the communication gap between deaf-mute individuals and the hearing public. It is a real-time, "
        "bidirectional application. Module 1 captures webcam video, uses MediaPipe to extract hand landmarks, "
        "and runs a lightweight TFLite neural network to translate sign language gestures into text and spoken "
        "English. Module 2 works in reverse: it takes text or microphone speech from a hearing person and translates "
        "it back into a sequential sign language slideshow. To make it highly usable, I integrated these modules into "
        "a real-time chat application using Flask and Socket.IO, achieving 95-99% accuracy and running at 15-30 frames "
        "per second on ordinary CPU hardware.\""
    )
    
    pdf.multi_cell(0, 6, pitch_text, border=1, align='L', fill=True)
    pdf.ln(5)
    
    # 2-3 Minute Interview Speech Intro
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 150, 136)
    pdf.cell(0, 8, '2-3 Minute Interview Speech Strategy', 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(51, 51, 51)
    intro_strategy = (
        "When explaining the project in detail, follow a conversational yet structured approach. "
        "Do not sound like you are reciting a technical report. Speak naturally, pacing yourself, "
        "and make clear transitions between the situation, task, action, and result. "
        "The following pages present the spoken scripts designed to flow naturally in an oral interview."
    )
    pdf.multi_cell(0, 6, intro_strategy)
    pdf.ln(8)
    
    # ------------------ SECTION 2: THE STAR BREAKDOWN ------------------
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(22, 54, 87)
    pdf.cell(0, 10, '2. The STAR Method Breakdown', 0, 1, 'L')
    pdf.ln(2)
    
    # Situation
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(22, 54, 87)
    pdf.cell(0, 8, 'Situation (The Context)', 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(51, 51, 51)
    situation_text = (
        "The main problem we identified was that deaf and mute individuals face severe communication barriers "
        "in their daily lives. Because the general public does not understand Indian Sign Language (ISL), simple tasks - "
        "like visiting a doctor, opening a bank account, or purchasing groceries - become incredibly frustrating. "
        "While sign language interpreters exist, they are expensive and rarely available on short notice. "
        "This creates a direct barrier to social inclusion and access to essential services. "
        "The real-world motivation was to create a free, accessible, and run-anywhere software tool that acts as a "
        "digital interpreter, allowing both parties to converse naturally without requiring a third-party human helper."
    )
    pdf.multi_cell(0, 6, situation_text)
    pdf.ln(5)
    
    # Task
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(22, 54, 87)
    pdf.cell(0, 8, 'Task (The Objective)', 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font('Helvetica', '', 10)
    task_text = (
        "Our objective was to build a complete, real-time bidirectional communication system. "
        "Specifically, I had to build two core modules: a sign-to-speech module that processes a camera feed "
        "to translate hand motions into text and synthesized voice, and a speech-to-sign module that translates "
        "audio transcripts back into visual sign sequences. The major requirement was that this had to work in real-time "
        "on consumer-grade laptops and mobile phones, without requiring heavy expensive GPUs or complex setups. "
        "A key limitation we had to design around was the high variance in how different users position their hands, "
        "varying lighting conditions, and potential model lag that could make a conversation feel slow and unnatural."
    )
    pdf.multi_cell(0, 6, task_text)
    pdf.ln(10)
    
    # Action (System Architecture and Tech Choices)
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(22, 54, 87)
    pdf.cell(0, 10, '3. Action (Implementation & Architecture)', 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 150, 136)
    pdf.cell(0, 8, 'System Architecture & Data Flows', 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(51, 51, 51)
    arch_text = (
        "To solve this, we designed a client-server architecture with a Flask web server serving a responsive "
        "HTML/CSS interface, coupled with WebSockets via Flask-SocketIO for low-latency bidirectional messaging. "
        "The system functions in two parallel flows:\n\n"
        "1. Sign-to-Text Flow: The deaf user's webcam frames are captured by the client and processed. In the web version, "
        "the server captures the webcam frame, processes it through MediaPipe Hands to extract 21 2D landmarks (x, y coordinates) "
        "per hand, normalizes them relative to the wrist, and inputs the resulting 84-dimensional feature vector into a "
        "lightweight TensorFlow Lite neural network. The predicted sign is tracked by a stability controller. Once stabilized "
        "for 1.5 seconds, it auto-appends to the current text draft, which is sent instantly over WebSockets to the chat room.\n\n"
        "2. Speech-to-Sign Flow: When a hearing user types a message or speaks into their microphone (transcribed via Google Speech "
        "Recognition), the message is broadcast to the deaf user's client. The client splits the message into words. For each word, "
        "it checks if a pre-recorded sign exists (e.g., HELLO or HELP). If not, it falls back to fingerspelling, extracting individual "
        "letters (A-Z) and playing them in a sequential slideshow visualizer."
    )
    pdf.multi_cell(0, 6, arch_text)
    pdf.ln(5)
    
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 150, 136)
    pdf.cell(0, 8, 'Technology Rationale', 0, 1, 'L')
    pdf.ln(2)
    
    techs = [
        ("MediaPipe:", "Instead of using heavy CNN models that process raw image pixels (which are highly sensitive to background clutter, skin tone, and lighting), we chose MediaPipe to extract hand landmarks. This isolates the hand shape into clean coordinates, reducing our input dimension from 640x480x3 raw pixels to just 84 float values, allowing a small neural network to perform with high accuracy."),
        ("TensorFlow / Keras:", "We used Keras to build and train a Multi-Layer Perceptron (MLP) because our dataset represents structured, numerical coordinates. Since the feature space is small (84 inputs), an MLP trains in seconds and provides fast inference without needing deep Convolutional neural networks."),
        ("TensorFlow Lite (TFLite):", "We converted our trained Keras model (.h5, ~336KB) to TFLite format (.tflite, ~102KB) and used the TFLite runtime interpreter. This reduced inference latency by over 60%, allowing the app to run smoothly at 30 FPS on standard CPUs without exhausting the client's CPU resources."),
        ("Flask & Socket.IO:", "We selected Flask for its lightweight backend routing and combined it with Flask-SocketIO because standard HTTP requests are stateless and slow. Socket.IO provides low-latency full-duplex communication, which is crucial for a real-time conversational chat application.")
    ]
    
    for title, desc in techs:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(22, 54, 87)
        pdf.cell(0, 5, title, 0, 1, 'L')
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(51, 51, 51)
        pdf.multi_cell(0, 5.5, desc)
        pdf.ln(2)
        
    # Implementation Steps & Contribution
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 150, 136)
    pdf.cell(0, 8, 'Step-by-Step Implementation Workflow', 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(51, 51, 51)
    
    workflow = (
        "1. Dataset Collection: Built step1_collect_dataset.py using OpenCV to capture hand sign images. The user shows "
        "gestures in front of the camera, saving 300 images per class for 35 classes (letters A-Z and digits 1-9), totaling "
        "10,500 images. Alternately, supported standard Indian Sign Language datasets from Kaggle.\n\n"
        "2. Feature Extraction: Developed step2_extract_landmarks.py using MediaPipe Hands. It processes each image, detects "
        "hands, extracts 21 landmarks (x, y) per hand, and constructs an 84-dimensional feature vector. It saves this dataset to landmarks.csv.\n\n"
        "3. Normalization: Implemented mathematical preprocessing to ensure scale and translation invariance. The coordinates "
        "are shifted relative to the wrist (landmark 0) and normalized by the maximum absolute distance to the wrist, scaling all values to [-1.0, 1.0].\n\n"
        "4. Model Training: Wrote step3_train_model.py. Split data 80/20 (stratified split), trained a 3-layer Neural Network "
        "(Inputs -> Dense 128 w/ ReLU -> Dropout 0.2 -> Dense 64 w/ ReLU -> Dropout 0.2 -> Softmax Output) using Adam optimizer and "
        "sparse categorical crossentropy loss. Converted the final trained model into TFLite format.\n\n"
        "5. Core Integration & Web Server: Combined the offline speech-synthesis (pyttsx3) and recognition (SpeechRecognition) "
        "modules into the Flask web server, setting up the client-server streaming and socket events."
    )
    pdf.multi_cell(0, 6, workflow)
    pdf.ln(5)
    
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(22, 54, 87)
    pdf.cell(0, 8, 'My Contribution & Technical Decisions', 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font('Helvetica', '', 10)
    contrib = (
        "My personal contributions centered on the machine learning pipeline, feature normalization, and the real-time synchronization of the application:\n"
        "- Landmark Preprocessing & Normalization: I developed the scale-invariant translation system. Originally, hand signs failed if the user "
        "moved further or closer to the camera. Shifting relative to landmark 0 and dividing by the max absolute value solved this.\n"
        "- Stability Controller State Machine: To resolve rapid jitter in predictions (e.g. flickering between A and E), I implemented a "
        "stability timer. The character must remain stable for 1.5 seconds, displaying a progress bar, before it auto-appends to the current word.\n"
        "- Model Optimization (TFLite): I converted the model to TFLite, reducing CPU utilization on standard laptops by half.\n"
        "- Flask-SocketIO & Multithreading: I set up a background webcam capture thread with mutual exclusion locks (threading.Lock()) to prevent race conditions during frame encoding and socket broadcasts.\n"
        "- Teammate Contributions: [NEED INFORMATION]\n"
        "- One major technical decision: Using MediaPipe hand landmarks instead of raw-pixel CNNs. The landmark approach isolated features, required "
        "100x fewer training parameters, eliminated background dependencies, and enabled the model to compile under 100KB, making it highly portable."
    )
    pdf.multi_cell(0, 6, contrib)
    pdf.ln(10)
    
    # Results
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(22, 54, 87)
    pdf.cell(0, 8, 'Result (The Outcome)', 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font('Helvetica', '', 10)
    result_text = (
        "The project successfully achieved its goal. We built a fully functioning, two-way conversational system. "
        "Numerically, our neural network achieved a final test accuracy of 95% to 99% across the 35 classes. "
        "The system runs efficiently at 15 to 30 FPS on standard consumer laptops, with a latency of under 50 milliseconds "
        "for model inference. The stability tracker successfully prevented double-entries while allowing hands-free typing. "
        "In terms of impact, the system translates sign language into audible speech, allowing a deaf-mute person to communicate "
        "fluently with a hearing person, and translates speech back to signs automatically, solving the bidirectional barrier. "
        "Through this project, I learned a great deal about practical ML optimization (Keras to TFLite conversion), real-time "
        "concurrency in web servers (using background threads and thread locks in Flask), and how to bridge mathematical concepts "
        "like coordinate normalization to solve a tangible human problem."
    )
    pdf.multi_cell(0, 6, result_text)
    
    # ------------------ SECTION 4: TECHNICAL DEEP-DIVE (Q&A) ------------------
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(22, 54, 87)
    pdf.cell(0, 10, '4. Technical Deep-Dive & Interview Questions', 0, 1, 'L')
    pdf.ln(2)
    
    # Question Formatter Helper (Fixed layout alignment)
    def write_qa(q_num, category, question, short_ans, deep_explain, follow_up):
        # Header for the question
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(22, 54, 87)
        pdf.cell(0, 6, f"Q{q_num} [{category}]: {question}", 0, 1, 'L')
        
        pdf.set_font('Helvetica', 'B', 9.5)
        pdf.set_text_color(0, 150, 136)
        pdf.cell(0, 5, "Short Answer:", 0, 1)
        pdf.set_font('Helvetica', '', 9.5)
        pdf.set_text_color(51, 51, 51)
        pdf.multi_cell(0, 5, short_ans)
        pdf.ln(1)
        
        pdf.set_font('Helvetica', 'B', 9.5)
        pdf.set_text_color(0, 150, 136)
        pdf.cell(0, 5, "Deep Dive Explanation:", 0, 1)
        pdf.set_font('Helvetica', '', 9.5)
        pdf.set_text_color(51, 51, 51)
        pdf.multi_cell(0, 5, deep_explain)
        pdf.ln(1)
        
        pdf.set_font('Helvetica', 'BI', 9.5)
        pdf.set_text_color(180, 50, 50)
        pdf.cell(0, 5, "Possible Follow-up Question:", 0, 1)
        pdf.set_font('Helvetica', 'I', 9.5)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(0, 5, follow_up)
        
        pdf.ln(4)
        
    # EASY QUESTIONS
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 150, 136)
    pdf.cell(0, 8, 'Easy Questions - Choices and Basic Functionality', 0, 1, 'L')
    pdf.ln(2)
    
    write_qa(
        1, "Easy", "What does your project do in simple terms?",
        "It is a bidirectional translator app that uses a webcam to translate Indian Sign Language (A-Z, 1-9) into text and spoken English, and translates typed or spoken sentences back into sign language images.",
        "The project consists of two modules: Module 1 processes real-time webcam frames, detects hand landmarks via MediaPipe, and uses a trained Keras/TFLite model to identify the sign. Module 2 takes text/voice inputs from a hearing person, splits it into words/characters, and displays pre-saved sign images sequentially.",
        "\"Why did you choose Indian Sign Language instead of American Sign Language (ASL)?\""
    )
    
    write_qa(
        2, "Easy", "Why did you choose a Neural Network (MLP) over a Convolutional Neural Network (CNN)?",
        "Because our features are 84 numerical coordinates extracted by MediaPipe rather than raw image pixels. For structured, low-dimensional coordinate data, a simple Feedforward Multi-Layer Perceptron (MLP) is fast, lightweight, and achieves 95-99% accuracy.",
        "CNNs are ideal for processing raw image grids because they extract spatial feature hierarchies. However, because MediaPipe already isolates the hand landmarks and abstracts away background, lighting, and skin color, we only have 84 coordinate points. An MLP is computationally cheap, training in seconds and running in under a millisecond on standard CPUs, whereas a CNN would require 100x more parameters and significantly higher CPU/GPU overhead.",
        "\"What would happen if MediaPipe failed to detect the hand?\""
    )
    
    write_qa(
        3, "Easy", "What are the classes supported by your model?",
        "The model supports 35 classes: the 26 English alphabets (A-Z) and the 9 digits (1-9). They represent standard fingerspelling gestures in Indian Sign Language.",
        "To collect the dataset, we used a custom script step1_collect_dataset.py capturing 300 frames per class, creating 10,500 samples. This ensures the model learns variations in hand positions and tilts.",
        "\"How does the system handle words that are not in the sign language dictionary?\""
    )
    
    write_qa(
        4, "Easy", "What libraries are used in the backend and frontend?",
        "The backend uses Flask, Flask-SocketIO (for real-time WebSockets), TensorFlow/Keras, MediaPipe, OpenCV, pyttsx3, and SpeechRecognition. The frontend uses vanilla HTML5, CSS3 (Outfit Google Font, custom responsive grids), and vanilla JavaScript.",
        "We avoided heavy frameworks like React on the frontend since this was a compact application, and Flask provided a quick way to integrate python-based AI scripts directly with HTML templates and WebSockets.",
        "\"What is pyttsx3, and why did you choose it over Google's gTTS?\""
    )

    # MEDIUM QUESTIONS
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 150, 136)
    pdf.cell(0, 8, 'Medium Questions - Architecture and Implementation Decisions', 0, 1, 'L')
    pdf.ln(2)

    write_qa(
        5, "Medium", "How do you extract features from the hand and process them?",
        "We use MediaPipe Hands to detect hand objects and return 21 landmarks. We then compute the relative coordinate of each landmark from the wrist, divide them by the maximum absolute coordinate value to ensure scale invariance, and concatenate both hands into an 84-dimensional float vector.",
        "In step2_extract_landmarks.py, for each hand, we subtract the wrist (landmark 0) coordinates (X_0, Y_0) from the other 20 landmarks. This centers the coordinate system at the wrist. We then find the max absolute value among these relative coordinates and divide each coordinate by it. This normalizes the hand size. Since left and right hands are mapped to separate slots (first 42 for left, last 42 for right), the system seamlessly handles single and dual-hand gestures.",
        "\"What happens when a hand moves off-screen? How does the vector change?\""
    )

    write_qa(
        6, "Medium", "Why did you convert the Keras model to a TFLite model?",
        "To optimize CPU performance and reduce inference latency. The standard Keras .h5 model is ~336KB, while the TFLite model is only ~102KB, leading to a 60% speedup and allowing real-time 30 FPS processing on low-end CPUs.",
        "Keras models contain extra metadata and weight layers optimized for training and backpropagation. TensorFlow Lite compiles the neural network graph, removing training-specific operations and compressing weights. Using the TFLite Interpreter in step4_sign_to_speech.py allows us to run inference on single threads without freezing the user interface or dropping WebSocket packets.",
        "\"Did you perform quantization during the TFLite conversion?\""
    )

    write_qa(
        7, "Medium", "Explain the purpose of the 'stability tracker' state machine.",
        "It prevents rapid prediction flickering (jitter) and double-append errors by requiring the model to output the same character continuously for 1.5 seconds before adding it to the draft.",
        "During live webcam feeds, hand tremors or transitions between gestures cause the model predictions to fluctuate (e.g., repeating A, A, B, A). The stability tracker measures the elapsed time since the prediction last changed. If the prediction remains identical for 1.5 seconds (measured using time.time()), it auto-appends to the word. Once appended, a lock (last_appended_prediction) is set, preventing further additions of that letter until a new sign is detected or the hand is removed.",
        "\"Is 1.5 seconds too slow for a fluid conversation? How can you make it faster?\""
    )

    write_qa(
        8, "Medium", "How does Flask-SocketIO handle bidirectional communications?",
        "Unlike standard HTTP which is client-initiated, Socket.IO opens a persistent WebSocket connection, enabling full-duplex communication so the server can push translation frames and chat transcripts instantly to both clients.",
        "In frontend/app.py, we run socketio.run(). The server listens for socket events like send_message or join, and uses emit(..., broadcast=True) to broadcast messages to all connected sockets. This allows the deaf person to send text translated from their signs, and the hearing person to send typed text instantly without reloading the page or polling.",
        "\"How does the server handle multiple users typing or signing at the same time?\""
    )

    # HARD QUESTIONS
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 150, 136)
    pdf.cell(0, 8, 'Hard Questions - Scalability, Security, and Production-Level Improvements', 0, 1, 'L')
    pdf.ln(2)

    write_qa(
        9, "Hard", "What are the limitations of your current dataset and how would you address them in production?",
        "The model is restricted to 35 static characters (A-Z, 1-9) which requires users to fingerspell words letter-by-letter. In production, we need to recognize dynamic gestures (like waving for 'hello' or sweeping hands for 'help') using sequential models.",
        "Fingerspelling is slow and unnatural for daily conversation. Real sign language uses full-word symbols. To support this, we would need to capture video sequences instead of single frames, extract landmark trajectories over time, and train sequential models like LSTMs, GRUs, or Transformers. We would also need to expand the vocabulary from 35 alphabetic/numeric classes to thousands of common lexical words.",
        "\"How would you structure a dataset for sequential full-word sign language?\""
    )

    write_qa(
        10, "Hard", "How would you scale this application to support thousands of concurrent users?",
        "Currently, chat history and webcam streaming states are stored in Flask memory, which fails if scaled. To scale, we must run stateless Flask instances behind a load balancer, use Redis for WebSocket message pub/sub, store chat history in a database, and move video inference to the client-side.",
        "In a scaled production system: 1) Client-side Inference: We would load the TFLite model directly in the browser using TensorFlow.js. MediaPipe would also run in JavaScript. This completely offloads the heavy frame-by-frame inference CPU cost from our backend servers. 2) Load Balancer: We would run multiple Flask nodes behind Nginx or AWS ALB, utilizing a Redis adapter for Socket.IO to coordinate WebSocket messages. 3) Database: Chat histories and profiles would be saved in a database (like MongoDB or PostgreSQL).",
        "\"If inference runs on the client-side, how do you protect your intellectual property (the model)?\""
    )

    write_qa(
        11, "Hard", "How does your model handle lighting variations, skin tones, and complex backgrounds?",
        "Because our pipeline uses MediaPipe Hands to extract landmarks first, the downstream neural network is entirely decoupled from raw pixels, making the classifier 100% robust to lighting, skin tones, and complex backgrounds.",
        "MediaPipe Hands uses an internal single-shot detector trained on millions of diverse hands in various lighting and backgrounds to identify hand bounding boxes and fit a 3D skeletal model. Once MediaPipe extracts the 21 coordinate points, all RGB pixel data is discarded. Our Keras neural network only receives these clean geometric relationships, meaning that variations in skin tone, shadows, or busy wallpapers have zero effect on our gesture classifier's accuracy.",
        "\"What if the user is wearing gloves or has a hand deformity? How does MediaPipe behave?\""
    )

    write_qa(
        12, "Hard", "What are the security vulnerabilities in your current implementation?",
        "Our app lacks user authentication (allowing username spoofing), has no input validation/sanitization (leaving it open to XSS via socket messages), stores sensitive chat history in plain in-memory arrays, and communicates over unencrypted HTTP/WS.",
        "To make this production-ready: 1) Auth: Add JWT or OAuth2 authentication to verify user identities. 2) Encryption: Use HTTPS and WSS (secure WebSockets) to prevent man-in-the-middle eavesdropping. 3) Sanitization: Sanitize all message inputs on the backend to prevent Cross-Site Scripting (XSS). 4) Database storage: Encrypt chat history at rest and prune data according to compliance regulations.",
        "\"How would you design a rate-limiting mechanism for your Socket.IO endpoints to prevent DDoS?\""
    )

    # ------------------ SECTION 5: CRITICAL ADVICE ------------------
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(22, 54, 87)
    pdf.cell(0, 10, '5. Critical Interview Tips & Challenging Points', 0, 1, 'L')
    pdf.ln(2)

    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 150, 136)
    pdf.cell(0, 8, 'Areas Interviewers are Highly Likely to Challenge', 0, 1, 'L')
    pdf.ln(2)

    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(51, 51, 51)
    
    warnings = (
        "During a technical interview, expect the interviewer to challenge specific design choices. "
        "Here are three key areas where they will push back, and how you should defend your choices:\n\n"
        "1. Processing Video in Backend vs. Frontend\n"
        "- Challenge: 'Streaming video frames from the browser to the Flask server to run MediaPipe and TensorFlow "
        "is highly inefficient. It wastes server bandwidth and introduces network latency. Why did you not run it in JavaScript?'\n"
        "- Defense: Acknowledge that running inference in the frontend (via MediaPipe JS and TensorFlow.js) is indeed the "
        "ideal production architecture to minimize server load. Explain that you built the prototype with Python backend "
        "inference to quickly leverage Python's rich ecosystem (TensorFlow, OpenCV, MediaPipe, SpeechRecognition) for fast "
        "experimentation. State that migrating the inference logic to the client-side using WebAssembly and TensorFlow.js "
        "is the very next item on your roadmap.\n\n"
        "2. Absence of a Database and Authentication\n"
        "- Challenge: 'Your server stores chat transcripts in a simple global list. If the server restarts, everything is "
        "lost. Anyone can join with any name. How is this secure or persistent?'\n"
        "- Defense: Clarify that the project is a functional proof-of-concept focused on solving the ML translation and socket synchronization challenges. "
        "Explicitly identify the lack of a database and session authentication as known limitations. Explain that you chose "
        "in-memory arrays to keep the prototype lightweight and easy to run in a demo, and then outline how you would integrate "
        "MongoDB or PostgreSQL for message persistence and JWT tokens for secure authentication in a real product.\n\n"
        "3. Fingerspelling (Static Alphabets) vs. Full Word Sentences\n"
        "- Challenge: 'Deaf people do not spell out every word letter-by-letter. They use full gestures for words. "
        "Is not fingerspelling too slow for real-world use?'\n"
        "- Defense: Agree fully. Explain that letter-by-letter fingerspelling is indeed a bottleneck for natural conversation. "
        "State that fingerspelling was chosen as the starting point to prove the feasibility of the 2D coordinate-based MLP approach. "
        "Explain that the logical extension is to capture continuous video sequences and train an LSTM or GRU network to recognize "
        "full words, using the existing fingerspelling system as a robust fallback for proper nouns, names, and unsupported vocabulary."
    )
    pdf.multi_cell(0, 6, warnings)
    pdf.ln(5)

    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(22, 54, 87)
    pdf.cell(0, 8, 'Key Interview Speaking Hacks', 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font('Helvetica', '', 10)
    hacks = (
        "- Use transition markers: Say 'The main problem we identified was...' or 'To solve this, I...' to help the interviewer follow your thoughts.\n"
        "- Be honest about contributions: If something is missing or if you worked in a team, clearly partition the tasks. Say: 'My core focus was...' "
        "and avoid taking credit for parts you did not touch.\n"
        "- Pivot challenges into learning moments: When discussing a bug or limitation, immediately explain how you resolved it and what you learned "
        "from the process. This shows a growth mindset and maturity."
    )
    pdf.multi_cell(0, 6, hacks)

    pdf.output(filepath)
    print(f"[INFO] PDF successfully compiled and saved to: {filepath}")

if __name__ == "__main__":
    out_path = "c:\\Users\\ASUS\\Desktop\\Final year project\\ISL_Project_STAR_Interview_Prep.pdf"
    if len(sys.argv) > 1:
        out_path = sys.argv[1]
    build_pdf(out_path)
