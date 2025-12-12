import { useState, useEffect } from 'react'
import SignDetector from './components/SignDetector'
import { ResizableBox } from 'react-resizable'
import './App.css'
import 'react-resizable/css/styles.css'
import axios from 'axios'

function App() {
  const [prediction, setPrediction] = useState("Waiting...")
  const [isConnected, setIsConnected] = useState(false);
  
  // Initial sizes
  const [inputSize, setInputSize] = useState({ width: 640, height: 480 });
  const [outputSize, setOutputSize] = useState({ width: 400, height: 500 }); // Increased height

  // Word formation state
  const [sentence, setSentence] = useState("");
  const [currentWord, setCurrentWord] = useState(""); // BUFFER: Holds the word being formed
  const [lastChar, setLastChar] = useState(null); 
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    const checkConnection = async () => {
      try {
        await axios.get('http://localhost:8000/');
        setIsConnected(true);
      } catch (e) {
        setIsConnected(false);
      }
    };
    
    checkConnection();
    const interval = setInterval(checkConnection, 5000);
    return () => clearInterval(interval);
  }, []);

  // Fetch suggestions when currentWord DOES NOT EXIST (to predict next word based on sentence)
  // OR when currentWord EXISTS (to autocomplete current word)
  useEffect(() => {
      const fetchSuggestions = async () => {
          const context = currentWord ? (sentence + " " + currentWord) : sentence;
          if (!context.trim()) {
              setSuggestions([]);
              return;
          }
          try {
              const res = await axios.post('http://localhost:8000/suggest', { context: context });
              if (res.data.suggestions) {
                  setSuggestions(res.data.suggestions);
              }
          } catch (e) {
              console.error("Suggestion error", e);
          }
      };

      const timeoutId = setTimeout(fetchSuggestions, 800); // slightly faster debounce
      return () => clearTimeout(timeoutId);
  }, [sentence, currentWord]);

  useEffect(() => {
    if (prediction && prediction !== "Waiting..." && prediction !== lastChar) {
        // Append to CURRENT WORD buffer, not sentence
        setCurrentWord(prev => prev + prediction);
        setLastChar(prediction);
    } else if (prediction === null) {
        setLastChar(null);
        setPrediction("Waiting...");
    }
  }, [prediction]);

  const handleSpace = () => {
      if (currentWord) {
          // Confirm current word
          setSentence(prev => prev + (prev ? " " : "") + currentWord);
          setCurrentWord("");
      } else {
          // Just add a space if no word currently
          setSentence(prev => prev + " ");
      }
  };

  const handleBackspace = () => {
      if (currentWord.length > 0) {
          setCurrentWord(prev => prev.slice(0, -1));
      } else {
          setSentence(prev => prev.slice(0, -1));
      }
  };

  const handleClear = () => { 
      setCurrentWord("");
      setSentence(""); 
      setSuggestions([]); 
  };
  
  const applySuggestion = (text) => {
      // If we have a current word partially typed, replace it with suggestion
      // If we don't, append suggestion to sentence
      if (currentWord) {
          setSentence(prev => prev + (prev ? " " : "") + text + " ");
          setCurrentWord("");
      } else {
          setSentence(prev => prev + (prev ? " " : "") + text + " ");
      }
  };

  return (
    <div className="app-container">
      <header>
        <h1>IsyaratKami</h1>
      </header>
      <main>
        <div className="panels">
           <div className="input-panel-wrapper">
             <h2>Live Input</h2>
             <ResizableBox 
                width={inputSize.width} 
                height={inputSize.height}
                minConstraints={[320, 240]} 
                maxConstraints={[1280, 720]}
                onResize={(e, data) => setInputSize({width: data.size.width, height: data.size.height})}
                className="custom-resizable"
             >
                <div style={{width: '100%', height: '100%'}} className="input-panel-inner">
                    <SignDetector 
                        onPrediction={setPrediction} 
                        onGesture={(type) => {
                            if (type === 'left') handleBackspace();
                            if (type === 'right') handleSpace();
                        }}
                    />
                </div>
             </ResizableBox>
           </div>
           
           <div className="output-panel-wrapper">
              <h2>Translation</h2>
              <ResizableBox 
                width={outputSize.width} 
                height={outputSize.height}
                minConstraints={[300, 400]} // Enforce minimum size to fit controls
                maxConstraints={[800, 800]}
                onResize={(e, data) => setOutputSize({width: data.size.width, height: data.size.height})}
                className="custom-resizable"
              >
                <div style={{width: '100%', height: '100%'}} className="output-panel-inner column">
                    <div className="top-section">
                        <div className={`prediction-box ${prediction === 'Waiting...' ? 'waiting' : ''}`}>
                            {prediction === 'Waiting...' ? '...' : prediction}
                        </div>
                        
                        {/* Current Word Buffer Display */}
                        <div className={`current-word-box ${!currentWord ? 'empty' : ''}`}>
                            <span className="label">Current buffer:</span>
                            <span className="value">{currentWord || "(signing...)"}</span>
                        </div>
                    </div>
                    
                    <div className="sentence-box">
                        <p>{sentence}<span className="cursor">|</span></p>
                    </div>

                    <div className="bottom-section">
                        <div className="suggestions-container">
                            {suggestions.map((s, i) => (
                                <button key={i} className="suggestion-chip" onClick={() => applySuggestion(s)}>
                                    {s}
                                </button>
                            ))}
                        </div>

                        <div className="controls">
                            <button onClick={handleSpace} className="primary-action">
                                {currentWord ? "CONFIRM WORD" : "SPACE"}
                            </button>
                            <button onClick={handleBackspace}>⌫</button>
                            <button onClick={handleClear} className="danger">Clear</button>
                        </div>
                    </div>
                </div>
              </ResizableBox>
           </div>
        </div>
        <div className="connection-status">
            <div className={`status-dot ${isConnected ? 'connected' : ''}`}></div>
            {isConnected ? "System Online" : "Backend Offline"}
        </div>
      </main>
    </div>
  )
}

export default App
