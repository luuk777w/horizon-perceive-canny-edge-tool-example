import numpy as np
import cv2, base64

def detect_edges(image_data, min_threshold, max_threshold):
    
    try:
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception:
        raise Exception("Invalid image data provided")

    edges = cv2.Canny(image, min_threshold, max_threshold)
    _, buffer = cv2.imencode(".jpg", edges)
    encoded_image = base64.b64encode(buffer).decode("utf-8")

    return encoded_image
