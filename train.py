import cv2

datasetPath = "./SIBI"
modelPath = "sibi_model.pkl"

def extractLandmarks(img, handModel):
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = handModel.process(rgb)
    
    if results.multi_hand_landmarks:
        for handLandmarks in results.multi_hand_landmarks:
            landmarks = []
            for landmark in handLandmarks.landmark:
                landmarks.extend([landmark.x, landmark.y, landmark.z])
            return landmarks
        
    return None