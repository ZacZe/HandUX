import cv2

def nothing(x): 
    pass

def draw_text(frame, text, is_error=False):
    color = (0, 0, 255) if is_error else (0, 255, 0)
    cv2.putText(frame, text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)