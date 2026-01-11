# Model Configuration
MODEL_PATH = "/Users/rasikdhakal/Desktop/Yolo/my_model_v2/my_model_v2.pt" 
CONFIDENCE_THRESHOLD = 0.5

# Camera Configuration
CAMERA_INDEX = 0  # 0 for default webcam, 1 for external
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
JPEG_QUALITY = 80  # 0-100, higher = better quality but larger size

# Detection Configuration
CONFIRMATION_TIME = 1.0  # seconds - object must be visible this long before announcement
GUIDANCE_COOLDOWN = 1.5  # seconds between guidance messages
OCR_MIN_AREA_RATIO = 0.20  # minimum object size for OCR
OCR_MAX_AREA_RATIO = 0.55  # maximum object size for OCR

# Server Configuration
HOST = "0.0.0.0"
PORT = 8000
CORS_ORIGINS = [
    "http://localhost:3000",  # React default
    "http://localhost:5173",  # Vite default
]

# Bounding Box Colors (BGR format for OpenCV)
BBOX_COLORS = [
    (164, 120, 87),
    (68, 148, 228),
    (93, 97, 209),
    (178, 182, 133),
    (88, 159, 106),
    (96, 202, 231),
    (159, 124, 168),
    (169, 162, 241),
    (98, 118, 150),
    (172, 176, 184)
]