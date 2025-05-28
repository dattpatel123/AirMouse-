import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import threading

move_lock = threading.Lock()
def smooth_move(x, y, duration=0.3):
    # Try to acquire the lock without blocking
    if move_lock.acquire(blocking=False):
        try:
            pyautogui.moveTo(x, y, duration=duration)
        finally:
            move_lock.release()
    else:
        # Another move is in progress, skip this move or handle as needed
        pass
def move_cursor_thread(x, y, duration=0.3):
    threading.Thread(target=smooth_move, args=(x, y, duration), daemon=True).start()

from WebcamStream import WebcamStream

stream = WebcamStream(1)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils
# Initialize previous position
prev_x, prev_y = 0, 0
smoothing_factor = 0.8  # Adjust between 0 (max smoothing) and 1 (no smoothing)

pinch_threshold = 50  # Distance threshold for pinch detection
# Get screen size
screen_w, screen_h = pyautogui.size()

cap = cv2.VideoCapture(1)

# Setting a box for finger
# Define the smaller "active" box inside your camera frame, width=700, height=400
box_left = 50
box_top = 100
box_width = 1100
box_height = 400

canvas = None

while True:
    
    frame = stream.read()
    frame = cv2.flip(frame, 1)
    
    
    
    w,h,c = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            # Index finger tip is landmark #8
            h, w, c = frame.shape
            
            thumb_tip = hand_landmarks.landmark[4]
            index_tip = hand_landmarks.landmark[8]
            
            thumb_x, thumb_y = int(thumb_tip.x * w), int(thumb_tip.y * h)
            index_x, index_y = int(index_tip.x * w), int(index_tip.y * h)
            
            distance_bw_thumb_index = np.hypot(index_x - thumb_x, index_y - thumb_y)
            
            # Move only within the defined box
            
            if box_left <= index_x <= box_left + box_width and box_top <= index_y <= box_top + box_height:
                norm_x = (index_x - box_left) / box_width
                norm_y = (index_y - box_top) / box_height
                screen_x = norm_x * screen_w
                screen_y = norm_y * screen_h
                # Move mouse to the mapped coordinates
                move_cursor_thread(screen_x, screen_y, duration=0.12)

            else:
                # If finger is outside the box, do not move the mouse
                pass
            
            if distance_bw_thumb_index < pinch_threshold:
                pyautogui.click()
            if distance_bw_thumb_index > pinch_threshold:
                pyautogui
            

            #mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            cv2.putText(frame, f'Dist: {int(distance_bw_thumb_index)}', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            
    
    
    cv2.rectangle(frame, (box_left, box_top), (box_left + box_width, box_top + box_height), (0, 255, 0), 2)
    cv2.imshow('Finger Drawing Blocks', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

stream.stop()
cv2.destroyAllWindows()
