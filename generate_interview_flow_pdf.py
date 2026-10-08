import sys
import os
from fpdf import FPDF

class InterviewFlowPDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return # Skip header on cover page
        self.set_font('Arial', 'B', 8)
        self.set_text_color(100, 110, 120)
        self.cell(0, 6, 'Indian Sign Language (ISL) Communication Assistant - Interview Prep Guide', 0, 1, 'L')
        self.set_font('Arial', '', 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 4, 'Prepared for CSE / B.Tech Technical & HR Interviews', 0, 1, 'L')
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.3)
        self.line(15, 20, 195, 20)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.set_draw_color(220, 220, 220)
        self.line(15, 280, 195, 280)
        self.cell(0, 10, f'Page {self.page_no()} of {{nb}}', 0, 0, 'C')
        self.cell(0, 10, 'Strictly for Interview Preparation', 0, 0, 'R')

def add_section_header(pdf, title):
    pdf.set_font('Arial', 'B', 13)
    pdf.set_text_color(22, 54, 87) # Deep Navy Blue
    pdf.cell(0, 8, title, 0, 1, 'L')
    pdf.set_draw_color(0, 150, 136) # Teal underline
    pdf.set_line_width(0.5)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 40, pdf.get_y())
    pdf.ln(4)

def add_body_text(pdf, text):
    pdf.set_font('Arial', '', 9.5)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5.5, text)
    pdf.ln(3)

def add_bullet_point(pdf, title, text):
    pdf.set_font('Arial', 'B', 9.5)
    pdf.set_text_color(22, 54, 87)
    pdf.cell(5, 5.5, chr(149), 0, 0)
    pdf.cell(40, 5.5, title + " ", 0, 0)
    pdf.set_font('Arial', '', 9.5)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5.5, text)
    pdf.ln(1.5)

def build_pdf(filepath):
    pdf = InterviewFlowPDF()
    pdf.alias_nb_pages()
    pdf.set_margins(15, 20, 15)
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # ------------------ COVER PAGE ------------------
    pdf.add_page()
    pdf.ln(25)
    
    # Title Block
    pdf.set_font('Arial', 'B', 22)
    pdf.set_text_color(22, 54, 87) # Deep Navy Blue
    pdf.multi_cell(0, 10, 'PROJECT PREPARATION GUIDE', 0, 'C')
    pdf.ln(2)
    
    pdf.set_font('Arial', 'B', 13)
    pdf.set_text_color(0, 150, 136) # Teal
    pdf.cell(0, 10, 'ISL Assistant for Deaf & Mute Communication', 0, 1, 'C')
    pdf.ln(8)
    
    # Horizontal Line
    pdf.set_draw_color(0, 150, 136)
    pdf.set_line_width(1.2)
    pdf.line(40, 62, 170, 62)
    pdf.ln(12)
    
    # Description
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(80, 80, 80)
    desc_text = (
        "This preparation guide has been structured specifically for placements, technical viva-voce, "
        "and HR interviews. It details the complete workflow of the Indian Sign Language (ISL) communication "
        "system, analyzing the design choices, architectural pipelines, mathematical models, implementation "
        "challenges, and outcomes. Use this guide to deliver a comprehensive, structured response to interviewers."
    )
    pdf.multi_cell(0, 6, desc_text, 0, 'C')
    pdf.ln(20)
    
    # Highlights / Meta-data Box
    pdf.set_fill_color(245, 247, 250)
    pdf.set_draw_color(220, 224, 230)
    pdf.set_line_width(0.5)
    pdf.rect(20, 120, 170, 70, style='FD')
    
    pdf.set_xy(25, 124)
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(22, 54, 87)
    pdf.cell(0, 8, 'PROJECT QUICK REFERENCE', 0, 1, 'L')
    pdf.ln(1.5)
    
    metadata = [
        ("Project Type:", "AI-ML Application / Web App Integration"),
        ("Sign Input:", "Real-time Webcam Hand Landmarks (2D Coordinates)"),
        ("Model Classifier:", "Dense Multi-Layer Perceptron (MLP) Neural Network"),
        ("Model Optimization:", "TensorFlow Lite (TFLite) Converter"),
        ("Bidirectional Stream:", "WebSockets (Flask-SocketIO) full-duplex communication"),
        ("Speech Modules:", "pyttsx3 (Text-to-Speech) & SpeechRecognition (Speech-to-Text)"),
        ("Test Accuracy:", "95% - 99% validation accuracy over 35 classes (A-Z, 1-9)"),
    ]
    
    for label, val in metadata:
        pdf.set_x(25)
        pdf.set_font('Arial', 'B', 8.5)
        pdf.cell(35, 5.5, label, 0, 0, 'L')
        pdf.set_font('Arial', '', 8.5)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 5.5, val, 0, 1, 'L')
        
    pdf.set_y(-30)
    pdf.set_font('Arial', 'I', 8.5)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, 'Structured Preparation Flow: Situation -> Architecture -> Code Implementation -> Results', 0, 1, 'C')
    
    # ------------------ CONTENT PAGES ------------------
    pdf.add_page()
    
    # 1. Problem
    add_section_header(pdf, "1. Problem")
    problem_text = (
        "Deaf and mute individuals (numbering over 70 million globally and roughly 18 million in India) "
        "rely heavily on Sign Language (such as Indian Sign Language - ISL) to communicate. However, the vast majority "
        "of the hearing and speaking public does not understand Sign Language. This creates a severe communication "
        "barrier in essential daily environments, including clinics, banks, government offices, schools, and shops. "
        "Consequently, deaf-mute individuals face systemic isolation, lack of independence, and diminished career "
        "prospects because they cannot easily converse with people outside their immediate community."
    )
    add_body_text(pdf, problem_text)
    
    # 2. Motivation
    add_section_header(pdf, "2. Motivation")
    motivation_text = (
        "The motivation behind this project is to create an affordable, highly accessible, and run-anywhere digital "
        "interpreter that bridges this bidirectional communication gap. By embedding AI-powered gesture translation "
        "into a lightweight web-based interface, we can empower deaf-mute users to live independently and interact "
        "naturally with hearing individuals. Instead of forcing them to buy expensive hardware sensors or struggle to "
        "find scarce, costly human sign language interpreters, they can simply use a standard laptop or mobile web browser "
        "to translate their signs to speech, and vice-versa."
    )
    add_body_text(pdf, motivation_text)
    
    # 3. Existing Solutions
    add_section_header(pdf, "3. Existing Solutions")
    existing_text = (
        "Historically, three primary methods have been employed to address the deaf-mute communication barrier:"
    )
    add_body_text(pdf, existing_text)
    add_bullet_point(pdf, "Human Interpreters:", "Professional translators who facilitate the conversation. They are rare, expensive, and cannot offer 24/7 coverage.")
    add_bullet_point(pdf, "Sensor-based Smart Gloves:", "Gloves embedded with flex sensors, accelerometers, and gyroscopes to physically track hand bend angles and motion. They transmit data via Bluetooth to a smartphone.")
    add_bullet_point(pdf, "Pure Vision CNNs:", "Applying Convolutional Neural Networks (CNNs) directly on raw camera frames (RGB grids) to classify signs.")
    pdf.ln(3)

    # 4. Their Limitations
    add_section_header(pdf, "4. Their Limitations")
    add_bullet_point(pdf, "Smart Gloves Cost & Comfort:", "They are fragile, highly expensive to manufacture, require constant calibration, and are socially obtrusive to wear in daily life.")
    add_bullet_point(pdf, "CNN Environmental Sensitivity:", "Models trained directly on raw images are highly sensitive to variations in lighting, background textures, skin tones, and camera quality. A model trained in a well-lit lab often fails in a dimly lit room or against a busy background.")
    add_bullet_point(pdf, "High Computational Cost:", "CNN architectures processing raw video streams are heavy. They require graphics processing units (GPUs) to run in real-time, which quickly drains mobile batteries and causes CPU thermal throttling on standard consumer laptops.")
    add_bullet_point(pdf, "Unidirectional Translation:", "Most existing prototypes only translate from sign-to-text. They ignore the reverse flow, meaning the deaf user has no easy way to understand the hearing user's verbal or typed response.")
    
    # ------------------ NEW PAGE ------------------
    pdf.add_page()
    
    # 5. Our Proposed Solution
    add_section_header(pdf, "5. Our Proposed Solution")
    solution_text = (
        "Our project implements a bidirectional, real-time, lightweight Indian Sign Language Communication Assistant "
        "embedded in a web-based chat-room interface. The application contains two distinct, integrated flows:\n\n"
        "Module 1 (Sign to Text & Speech): Captures the deaf user's webcam feed, extracts the geometrical coordinates of hand "
        "landmarks using MediaPipe (removing background and lighting variables), and runs the coordinates through a lightweight "
        "Multi-Layer Perceptron (MLP) classifier. The recognized letters or numbers are auto-appended to a draft and synthesized "
        "into spoken English via pyttsx3.\n\n"
        "Module 2 (Speech/Text to Sign): Captures the hearing user's speech via a microphone, transcribes it to text via Google "
        "Speech Recognition, splits the words, and plays the corresponding sign language images sequentially. If a full word "
        "is not in the dictionary, the system automatically falls back to letter-by-letter fingerspelling.\n\n"
        "Communication Bridge: Both modules are synchronized in a real-time web chat room powered by Flask-SocketIO, enabling "
        "instant, full-duplex conversations."
    )
    add_body_text(pdf, solution_text)
    
    # 6. Technologies Used
    add_section_header(pdf, "6. Technologies Used")
    add_bullet_point(pdf, "Python 3.9/3.10:", "Core programming language for system scripts and model building.")
    add_bullet_point(pdf, "MediaPipe Hands:", "Google's framework for extracting 21 2D landmarks (coordinates) per hand. This abstracts away pixels, making the model robust to lighting, background, and skin color.")
    add_bullet_point(pdf, "TensorFlow & Keras:", "Used to design, train, and test the Multi-Layer Perceptron (MLP) model.")
    add_bullet_point(pdf, "TensorFlow Lite (TFLite):", "Used to convert the trained Keras model (.h5) into an optimized format (.tflite), lowering CPU utilization and boosting inference speed.")
    add_bullet_point(pdf, "OpenCV (Python-cv2):", "Used to handle camera frame capture, rendering, and landmarks visualization.")
    add_bullet_point(pdf, "Flask & Flask-SocketIO:", "Server backend, providing HTTP routes and persistent WebSockets for instant messaging.")
    add_bullet_point(pdf, "SpeechRecognition & pyttsx3:", "Speech-to-Text translation and Text-to-Speech speech synthesis.")
    add_bullet_point(pdf, "Web Frontend:", "HTML5, CSS3 (Outfit typeface, responsive layout), and Vanilla JavaScript.")
    
    # ------------------ NEW PAGE ------------------
    pdf.add_page()
    
    # 7. System Architecture
    add_section_header(pdf, "7. System Architecture")
    arch_intro = (
        "The project follows a client-server architecture with a continuous pipeline processing live frames:"
    )
    add_body_text(pdf, arch_intro)
    
    add_bullet_point(pdf, "Webcam Stream Capture:", "JavaScript client captures webcam frames and Flask coordinates the backend threading. OpenCV grabs frames at 30 FPS.")
    add_bullet_point(pdf, "Landmark Detection:", "MediaPipe Hands processes the image, locating hand points. It returns 21 nodes per hand, represented by x and y coordinates (total 42 coordinates per hand).")
    add_bullet_point(pdf, "Mathematical Preprocessing:", "To ensure translation and scale invariance, landmarks are normalized. 1) Wrist Centering: The coordinates of the wrist (landmark 0) are subtracted from all other 20 points, placing the wrist at origin (0,0). 2) Max-Value Scaling: The relative coordinates are divided by the hand's maximum absolute coordinate value, bounding all coordinates to [-1.0, 1.0].")
    add_bullet_point(pdf, "Model Inference:", "The normalized values are concatenated into an 84-dimensional flat vector (42 for left, 42 for right). If a hand is missing, its 42 values default to 0. The TFLite interpreter runs inference on this vector, returning probabilities for all 35 classes.")
    add_bullet_point(pdf, "Stability & WebSocket Broadcast:", "A stability controller appends the sign if it is stable for 1.5 seconds, which is sent over WebSocket (Flask-SocketIO) to the chat channel.")
    pdf.ln(2)
    
    # 8. Working Process
    add_section_header(pdf, "8. Working Process")
    working_steps = (
        "The project lifecycle is divided into 5 distinct pipeline steps:\n\n"
        "1. Dataset Collection (step1_collect_dataset.py): Uses OpenCV to capture webcam images. Saves 300 frames per class "
        "into folders (dataset/A, dataset/B, etc.) for 35 classes, forming a dataset of 10,500 images.\n"
        "2. Landmarks Extraction (step2_extract_landmarks.py): Reads all images, extracts normalized hand coordinate vectors, "
        "and saves the data in landmarks.csv along with their class labels.\n"
        "3. Model Training (step3_train_model.py): Splitting the csv data 80/20. Trains a Keras MLP (Dense 128 -> Dropout 0.2 -> "
        "Dense 64 -> Dropout 0.2 -> Softmax Output). Achieves 95-99% accuracy. Exports to model/isl_model.h5 and converts to model/isl_model.tflite.\n"
        "4. Live Chat Integration (app.py): Sets up the Flask-SocketIO app. Runs a background loop that processes video frames, "
        "predicts classes, monitors stability, updates the current draft word, and handles text/speech conversion."
    )
    add_body_text(pdf, working_steps)
    
    # ------------------ NEW PAGE ------------------
    pdf.add_page()
    
    # 9. Challenges
    add_section_header(pdf, "9. Challenges & Technical Solutions")
    add_bullet_point(pdf, "Hand Position and Camera Distance Jitter:", "Initially, users had to keep their hand at the exact distance and location as the training set. We solved this by implementing translation-invariance (wrist subtraction) and scale-invariance (dividing by the maximum absolute coordinate value).")
    add_bullet_point(pdf, "Flickering and Tremors:", "Live webcam feeds suffer from coordinate jitter, causing predictions to flicker rapidly (e.g. A->E->A). We solved this by developing a stability-state-machine: a letter is only typed if the predicted class remains constant for 1.5 seconds.")
    add_bullet_point(pdf, "CPU Bottleneck and Thread Blocking:", "Running video capture and model inference inside the Flask HTTP stream blocked the WS server and caused massive lag. We solved this by offloading webcam polling and model prediction to a dedicated background Python thread, using python's threading.Lock() to safely sync data with Flask SocketIO.")
    add_bullet_point(pdf, "Model Size on Standard Systems:", "Deep neural networks are massive. We solved this by extracting landmarks to reduce the model input space. Since our input vector is only 84 numbers (instead of 640x480x3 pixels), we trained a tiny MLP and exported to TFLite, reducing model size to just 102KB, permitting high FPS inference on low-end CPUs.")
    pdf.ln(3)

    # 10. Results
    add_section_header(pdf, "10. Results")
    results_text = (
        "The project successfully demonstrated a fully functioning real-time bidirectional communication system:\n"
        "- Model Accuracy: Achieved 95% - 99% test accuracy across 35 classes (A-Z, 1-9).\n"
        "- Real-Time Performance: The system delivers stable predictions at 15 to 30 FPS on a standard laptop CPU, "
        "with inference latency under 5ms.\n"
        "- Stability: The stability tracker completely eliminates double-entry mistakes due to hand transitions.\n"
        "- Bidirectionality: Deaf users successfully output text and speech through signs, and hearing users broadcasted "
        "their voice inputs, which rendered as sequential sign slideshows instantly."
    )
    add_body_text(pdf, results_text)
    
    # 11. Future Improvements
    add_section_header(pdf, "11. Future Improvements")
    add_bullet_point(pdf, "Client-Side Inference (TensorFlow.js):", "Migrating hand landmark extraction (MediaPipe JS) and classification (TF.js) to the browser. This eliminates the server-side CPU bottleneck and network bandwidth costs, allowing the server to handle millions of users.")
    add_bullet_point(pdf, "Sequential Word Recognition (LSTMs/Transformers):", "Fingerspelling is slow. To support natural Indian Sign Language grammar, the system must recognize dynamic hand sequences (e.g. waving to mean 'hello'). We plan to extract landmarks across sequences of frames and train Recurrent Neural Networks (LSTM/GRU) or Transformers.")
    add_bullet_point(pdf, "Database Persistence & Authentication:", "Integrating a database (PostgreSQL/MongoDB) to store secure chat logs, and introducing user profiles with OAuth2/JWT authentication.")
    add_bullet_point(pdf, "Lexicon Extension:", "Expanding the dictionary from 35 alphabetic/numeric static characters to thousands of standard ISL vocabulary words to make conversations fluid.")

    pdf.output(filepath)
    print(f"[INFO] PDF successfully compiled and saved to: {filepath}")

if __name__ == "__main__":
    out_path = "c:\\Users\\ASUS\\Desktop\\Final year project\\ISL_Interview_Preparation_Guide.pdf"
    if len(sys.argv) > 1:
        out_path = sys.argv[1]
    build_pdf(out_path)
