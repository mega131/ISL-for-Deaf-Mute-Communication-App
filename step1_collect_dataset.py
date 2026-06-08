"""
STEP 1 - Collect ISL Dataset
=================================
Use your webcam to capture images of your hand for each sign.
Press 'S' to start capturing 300 images for the current class.
Press 'Q' to quit early.
"""

import cv2
import os

# Configuration
DATASET_DIR = "dataset"
NUM_CLASSES = 35  # A-Z (26) + 1-9 (9)
SAMPLES_PER_CLASS = 300

# Define classes (A-Z, 1-9)
CLASSES = [chr(i) for i in range(ord('A'), ord('Z')+1)] + [str(i) for i in range(1, 10)]

def main():
    if not os.path.exists(DATASET_DIR):
        os.makedirs(DATASET_DIR)

    print("=" * 50)
    print("  ISL Dataset Collection Tool")
    print("=" * 50)
    print("Choose collection mode:")
    print("  1 - Standard Alphabet & Digits (A-Z, 1-9)")
    print("  2 - Custom Word / Gesture (e.g., THANK_YOU, HELLO)")
    
    choice = input("Enter choice (1/2): ").strip()
    
    if choice == "2":
        custom_word = input("Enter the custom word/gesture name (use uppercase and underscores, e.g., THANK_YOU): ").strip().upper()
        if not custom_word:
            print("[ERROR] Custom word name cannot be empty.")
            return
        classes_to_collect = [custom_word]
    else:
        classes_to_collect = CLASSES

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not open webcam.")
        return

    for class_name in classes_to_collect:
        class_dir = os.path.join(DATASET_DIR, class_name)
        if not os.path.exists(class_dir):
            os.makedirs(class_dir)

        print(f"\n[INFO] Getting ready to collect data for class: '{class_name}'")
        print("Press 'S' when you are ready to start capturing.")
        
        # Wait for the user to press 'S'
        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            cv2.putText(frame, f"Ready? Press 'S' to start class: {class_name}", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow("Dataset Collection", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('s') or key == ord('S'):
                break
            if key == ord('q') or key == ord('Q'):
                print("\n[INFO] Exiting program.")
                cap.release()
                cv2.destroyAllWindows()
                return

        print(f"[INFO] Capturing images for '{class_name}'...")
        count = 0
        while count < SAMPLES_PER_CLASS:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            
            # Draw ROI box (Optional, helps guide the user)
            height, width, _ = frame.shape
            cv2.rectangle(frame, (width//2 - 150, height//2 - 150), (width//2 + 150, height//2 + 150), (255, 0, 0), 2)
            
            cv2.putText(frame, f"Collecting: {class_name} [{count+1}/{SAMPLES_PER_CLASS}]", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.imshow("Dataset Collection", frame)

            # Save the frame
            img_path = os.path.join(class_dir, f"{count}.jpg")
            cv2.imwrite(img_path, frame)
            count += 1

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n[INFO] Exiting program.")
                cap.release()
                cv2.destroyAllWindows()
                return

    print("\n[DONE] Dataset collection complete!")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
