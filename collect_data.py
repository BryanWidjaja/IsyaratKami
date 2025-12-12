import cv2
import numpy as np
import os
import mediapipe as mp

# Path for exported data, numpy arrays
DATA_PATH = os.path.join('MP_Data') 

# Thirty videos worth of data
no_sequences = 30

# Videos are going to be 30 frames in length
sequence_length = 30

def mediapipe_detection(image, model):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) 
    image.flags.writeable = False                  
    results = model.process(image)                 
    image.flags.writeable = True                   
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) 
    return image, results

def draw_styled_landmarks(image, results):
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp.solutions.drawing_utils.draw_landmarks(
                image, 
                hand_landmarks, 
                mp.solutions.hands.HAND_CONNECTIONS,
                mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                mp.solutions.drawing_styles.get_default_hand_connections_style())

def extract_keypoints(results):
    if results.multi_hand_landmarks:
        # We assume 1 hand for now
        # Flatten x, y, z for 21 landmarks -> 63 values
        lm = results.multi_hand_landmarks[0]
        rh = np.array([[res.x, res.y, res.z] for res in lm.landmark]).flatten() 
        return rh
    else:
        return np.zeros(21*3) # Empty array if no hand

def main():
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    action_name = input("Enter the name of the action to record (e.g., J, Z): ").strip().upper()
    if not action_name:
        print("Invalid name. Exiting.")
        return

    # Create folder for action
    action_folder = os.path.join(DATA_PATH, action_name)
    os.makedirs(action_folder, exist_ok=True)
    
    cap = cv2.VideoCapture(0)
    
    for sequence in range(no_sequences):
        sequence_frames = [] # Buffer for this video
        
        for frame_num in range(sequence_length):

            ret, frame = cap.read()
            if not ret:
                break
                
            image, results = mediapipe_detection(frame, hands)
            draw_styled_landmarks(image, results)
            
            if frame_num == 0: 
                cv2.putText(image, 'STARTING COLLECTION', (120,200), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255, 0), 4, cv2.LINE_AA)
                cv2.putText(image, 'Collecting frames for {} Video Number {}'.format(action_name, sequence), (15,12), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                cv2.imshow('OpenCV Feed', image)
                cv2.waitKey(2000) # Wait 2 seconds between sequences
            else: 
                cv2.putText(image, 'Collecting frames for {} Video Number {}'.format(action_name, sequence), (15,12), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                cv2.imshow('OpenCV Feed', image)
            
            keypoints = extract_keypoints(results)
            sequence_frames.append(keypoints)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break
        
        # Save the full sequence after collecting all frames
        # Shape: (30, 63)
        npy_path = os.path.join(action_folder, str(sequence))
        np.save(npy_path, np.array(sequence_frames))
                
    cap.release()
    cv2.destroyAllWindows()
    print(f"Data collection for '{action_name}' completed.")

if __name__ == "__main__":
    main()
