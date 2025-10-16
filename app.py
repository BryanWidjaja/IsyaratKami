import os
import cv2
import mediapipe as mp
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QMenu, QAction
from PyQt5.QtCore import Qt, QPoint, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QPainter
import sys
from train import extractLandmarks

datasetPath = "./SIBI"
modelPath = "sibi_model.pkl"

if not os.path.exists(modelPath):
    print("Training new model...")
    
    mpHands = mp.solutions.hands
    hands = mpHands.Hands(static_image_mode=True, max_num_hands=1)
    
    x = []
    y = []

    for label in os.listdir(datasetPath):
        labelDirectory = os.path.join(datasetPath, label)
        
        if not os.path.isdir(labelDirectory):
            continue
        
        images = os.listdir(labelDirectory)
        totalImages = len(images)
        
        print(f"Processing {totalImages} images for class '{label}'...")

        for index, imgName in enumerate(images):
            imagePath = os.path.join(labelDirectory, imgName)
            
            img = cv2.imread(imagePath)
            
            if img is None:
                continue
            
            landmarks = extractLandmarks(img, hands)
            
            if landmarks:
                x.append(landmarks)
                y.append(label)
            
            # test
            if (index + 1) % 50 == 0 or (index + 1) == totalImages:
                print(f"{index + 1} / {totalImages} images processed")

    x = np.array(x)
    y = np.array(y)
    
    print(f"Extracted {x.shape[0]} samples in total.")

    classifier = RandomForestClassifier(n_estimators=200)
    classifier.fit(x, y)
    
    joblib.dump(classifier, modelPath)
    
    print(f"Model saved as {modelPath}.")
else:
    classifier = joblib.load(modelPath)


class SideResizeGrip(QWidget):
    def __init__(self, parent, position):
        super().__init__(parent)
        self.position = position
        self.setMouseTracking(True)
        self.setCursor(Qt.SizeHorCursor if position=='right' else Qt.SizeVerCursor)
        self.pressing = False
        self.mouse_start = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressing = True
            self.mouse_start = event.globalPos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.pressing:
            delta = event.globalPos() - self.mouse_start
            win = self.window()
            geo = win.geometry()
            if self.position == 'right':
                win.resize(max(win.minimumWidth(), geo.width() + delta.x()), geo.height())
            elif self.position == 'bottom':
                win.resize(geo.width(), max(win.minimumHeight(), geo.height() + delta.y()))
            self.mouse_start = event.globalPos()
            event.accept()

    def mouseReleaseEvent(self, event):
        self.pressing = False

class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.click_through = False
        self.letter = ""

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout()
        
        self.label = QLabel("")
        
        self.label.setStyleSheet("""
            color: white;
            font-size: 80px;
            background: transparent;
        """)
        
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label, alignment=Qt.AlignCenter)
        self.setLayout(layout)

        self.resize_margin = 10
        self.right_grip = SideResizeGrip(self, 'right')
        self.bottom_grip = SideResizeGrip(self, 'bottom')
        self.right_grip.setVisible(True)
        self.bottom_grip.setVisible(True)
        
        self.setMinimumSize(200, 100)
        
    def update_text(self, letter):
        self.letter = letter
        self.label.setText(letter)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        pen = QColor(255, 255, 0, 128)
        painter.setPen(pen)
        painter.drawRect(0, 0, self.width()-1, self.height()-1)

    def resizeEvent(self, event):
        self.right_grip.setGeometry(self.width()-self.resize_margin, 0, self.resize_margin, self.height())
        self.bottom_grip.setGeometry(0, self.height()-self.resize_margin, self.width(), self.resize_margin)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        toggle_click_action = QAction("Click-through overlay", self)
        toggle_click_action.setCheckable(True)
        toggle_click_action.setChecked(self.click_through)
        toggle_click_action.triggered.connect(self.toggle_click_through)
        menu.addAction(toggle_click_action)

        close_action = QAction("Close Overlay", self)
        close_action.triggered.connect(self.close_and_exit)
        menu.addAction(close_action)

        menu.exec_(event.globalPos())

    def toggle_click_through(self):
        self.click_through = not self.click_through
        flags = self.windowFlags()
        if self.click_through:
            self.setWindowFlags(flags | Qt.WindowTransparentForInput)
        else:
            self.setWindowFlags(flags & ~Qt.WindowTransparentForInput)
        self.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Alt:
            self.toggle_click_through()
        elif event.key() == Qt.Key_Escape:
            self.close_and_exit()

    def close_and_exit(self):
        self.close()
        QApplication.instance().quit()

class HandSignThread(QThread):
    update_signal = pyqtSignal(str)

    def __init__(self, classifier):
        super().__init__()
        self.classifier = classifier
        self.running = True
        self.hands = mp.solutions.hands.Hands(max_num_hands=1)

    def run(self):
        cap = cv2.VideoCapture(0)
        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue
            landmarks = extractLandmarks(frame, self.hands)
            if landmarks:
                pred = self.classifier.predict([landmarks])
                self.update_signal.emit(pred[0])
        cap.release()

    def stop(self):
        self.running = False
        self.wait()

if __name__ == "__main__":
    choice = input("Choose mode ('cam' or 'screen'): ").strip().lower()
    
    if choice == "screen":
        print("Belom Jadi")
        sys.exit(0)
    elif choice != "cam":
        print("Invalid choice. Exiting...")
        sys.exit(0)

    app = QApplication(sys.argv)
    
    screen_rect = app.desktop().screenGeometry()
    
    overlay = OverlayWindow()
    overlay.resize(screen_rect.width(), screen_rect.height())
    overlay.move(0,0)
    overlay.show()

    thread = HandSignThread(classifier)
    thread.update_signal.connect(lambda letter: overlay.update_text(letter))
    thread.start()

    sys.exit(app.exec_())
