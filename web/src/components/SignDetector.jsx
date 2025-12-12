import React, { useRef, useEffect, useState } from 'react';
import Webcam from 'react-webcam';
import { Camera } from '@mediapipe/camera_utils';
import { Hands } from '@mediapipe/hands';
import axios from 'axios';

const SignDetector = ({ onPrediction }) => {
  const webcamRef = useRef(null);
  const [cameraActive, setCameraActive] = useState(true);
  const lastPredictionRef = useRef("");
  const predictionHistoryRef = useRef([]);
  const lastApiCallTimeRef = useRef(0);
  
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
