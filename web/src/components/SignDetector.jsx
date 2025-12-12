import React, { useRef, useEffect, useState } from 'react';
import Webcam from 'react-webcam';
import { Camera } from '@mediapipe/camera_utils';
import { Hands } from '@mediapipe/hands';
import axios from 'axios';

const SignDetector = ({ onPrediction, onGesture }) => {
  const webcamRef = useRef(null);
  const [cameraActive, setCameraActive] = useState(true);
  const lastPredictionRef = useRef("");
  const predictionHistoryRef = useRef([]);
  const lastApiCallTimeRef = useRef(0);
  
  // Gesture Recognition State
  const gestureHistoryRef = useRef([]); // Stores recent x-coordinates of wrist
  const lastGestureTimeRef = useRef(0);
  const GESTURE_COOLDOWN = 1000; // ms
  const SWIPE_THRESHOLD = 0.3; // Distance moved (0-1 scale)
  const HISTORY_SIZE = 10; // Number of frames to track
  
  // Resizable state handled by parent or wrapper, here we just fill container
  // But wait, the video need to respect aspect ratio.

  useEffect(() => {
    const hands = new Hands({
      locateFile: (file) => {
        return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
      },
    });

    hands.setOptions({
      maxNumHands: 1,
      modelComplexity: 1,
      minDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5,
    });

    hands.onResults(onResults);

    if (
      typeof webcamRef.current !== "undefined" &&
      webcamRef.current !== null
    ) {
      const camera = new Camera(webcamRef.current.video, {
        onFrame: async () => {
             if (webcamRef.current && webcamRef.current.video) {
                await hands.send({ image: webcamRef.current.video });
             }
        },
        width: 640,
        height: 480,
      });
      camera.start();
    }
  }, []);

  const onResults = async (results) => {
    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
      const landmarks = results.multiHandLandmarks[0];
      
      // Flatten landmarks: [x, y, z, x, y, z, ...]
      const flattened = [];
      for (const lm of landmarks) {
        flattened.push(lm.x, lm.y, lm.z);
      }

      // Detect Gestures (locally)
      checkGestures(landmarks);

      // Throttle API calls (e.g., every 200ms)
      // Throttle API calls (e.g., every 200ms)
      const now = Date.now();
      if (now - lastApiCallTimeRef.current > 200) {
          lastApiCallTimeRef.current = now;
          try {
            const response = await axios.post('http://localhost:8000/predict', {
               landmarks: flattened
            });
            
            const pred = response.data.prediction;
            handleDebounce(pred);
          } catch (error) {
            console.error("Prediction error:", error);
          }
      }
    } else {
        // No hand detected
        handleDebounce(null);
        gestureHistoryRef.current = []; // Reset gesture history
    }
  };

  // Simple Swipe Detection
  const checkGestures = (landmarks) => {
      const now = Date.now();
      if (now - lastGestureTimeRef.current < GESTURE_COOLDOWN) return;

      // Wrist is landmark 0
      const wristX = landmarks[0].x; // 0.0 (left) to 1.0 (right)
      
      const history = gestureHistoryRef.current;
      history.push({ x: wristX, time: now });
      
      // Keep only recent frames (e.g., last 500ms)
      while (history.length > 0 && now - history[0].time > 500) {
          history.shift();
      }

      if (history.length < 5) return; // Need some data

      const start = history[0];
      const end = history[history.length - 1];
      const dx = end.x - start.x; // Positive = Right, Negative = Left
      
      // Check for significant movement
      if (Math.abs(dx) > SWIPE_THRESHOLD) {
          // Confirm it's a consistent unidirectional movement (monotonic check) to avoid noise
          // (Simplified: just check end vs start for now)
          
          if (dx > 0) {
              console.log("Gesture: Swipe Right");
              if (onGesture) onGesture('right');
          } else {
              console.log("Gesture: Swipe Left");
              if (onGesture) onGesture('left');
          }
          
          lastGestureTimeRef.current = now;
          gestureHistoryRef.current = []; // Reset after trigger
      }
  };

  const handleDebounce = (pred) => {
      // Add to history
      const history = predictionHistoryRef.current;
      history.push(pred);
      if (history.length > 3) history.shift(); // Keep last 3

      // Check if all in history are the same
      if (history.length === 3 && history.every(v => v === pred)) {
          if (lastPredictionRef.current !== pred) {
              lastPredictionRef.current = pred;
              onPrediction(pred);
          }
      }
  };

  return (
    <div className="sign-detector-container" style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden', borderRadius: '0.5rem' }}>
       <Webcam
         ref={webcamRef}
         style={{
            position: 'absolute',
            left: 0,
            right: 0,
            textAlign: 'center',
            width: '100%',
            height: '100%',
            objectFit: 'cover'
         }}
         mirrored={true}
       />
    </div>
  );
};

export default SignDetector;
