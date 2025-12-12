from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import TensorBoard
import numpy as np
import os

DATA_PATH = os.path.join('MP_Data') 

def main():
    if not os.path.exists(DATA_PATH):
        print(f"Data directory '{DATA_PATH}' not found. Please run collect_data.py first.")
        return

    actions = np.array([f for f in os.listdir(DATA_PATH) if os.path.isdir(os.path.join(DATA_PATH, f))])
    
    if len(actions) == 0:
         print(f"No actions found in '{DATA_PATH}'. Please collect data first.")
         return

    print(f"Found actions: {actions}")

    label_map = {label:num for num, label in enumerate(actions)}

    sequences, labels = [], []
    
    # 30 videos per action
    no_sequences = 30

    for action in actions:
        action_path = os.path.join(DATA_PATH, action)
        for sequence in range(no_sequences):
            try:
                # Load the sequence file directly
                res = np.load(os.path.join(action_path, "{}.npy".format(sequence)))
                
                # Check shape
                if res.shape == (30, 63):
                    sequences.append(res)
                    labels.append(label_map[action])
                else:
                    print(f"Skipping {action} sequence {sequence}: Invalid shape {res.shape}")
            except Exception as e:
                print(f"Error loading {action} sequence {sequence}: {e}")

    X = np.array(sequences)
    y = to_categorical(labels).astype(int)

    if len(X) == 0:
        print("No valid data loaded. Exiting.")
        return

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.05)
    
    model = Sequential()
    # 30 frames, 63 features
    model.add(LSTM(64, return_sequences=True, activation='relu', input_shape=(30,63)))
    model.add(LSTM(128, return_sequences=True, activation='relu'))
    model.add(LSTM(64, return_sequences=False, activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(len(actions), activation='softmax'))

    model.compile(optimizer='Adam', loss='categorical_crossentropy', metrics=['categorical_accuracy'])
    
    print("Starting training...")
    model.fit(X_train, y_train, epochs=500, callbacks=[TensorBoard(log_dir='logs')]) # Lower epochs if needed
    
    model.summary()
    
    model.save('sibi_lstm.h5')
    print("Model saved as sibi_lstm.h5")

if __name__ == "__main__":
    main()
