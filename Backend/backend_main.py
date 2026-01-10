import asyncio
import base64
import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import json
import time
from threading import Thread, Lock
from queue import Queue
import pytesseract
from typing import Optional, Dict, List

app = FastAPI()

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class AppState:
    def __init__(self):
        self.model: Optional[YOLO] = None
        self.labels: Dict[int, str] = {}
        self.current_mode = "SCAN"  # SCAN or GUIDE
        self.active_object: Optional[str] = None
        self.active_bbox: Optional[List[int]] = None
        self.frame_queue = Queue(maxsize=2)
        self.running = False
        self.lock = Lock()
        self.spoken_objects = set()
        self.detection_start_time = {}
        self.last_guidance_time = {}
        
        # Config
        self.conf_thresh = 0.5
        self.camera_index = 0
        self.confirmation_time = 1.0
        self.guidance_cooldown = 1.5
        
state = AppState()

# YOLO Detection Thread
class VideoProcessor(Thread):
    def __init__(self, state: AppState):
        super().__init__(daemon=True)
        self.state = state
        self.cap = None
        
    def run(self):
        self.cap = cv2.VideoCapture(self.state.camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        print("Video processor started")
        
        while self.state.running:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to read frame")
                time.sleep(0.1)
                continue
            
            # Running YOLO inference
            results = self.state.model(frame, verbose=False)
            detections = results[0].boxes
            
            # Processing the detections
            detection_data = []
            current_objects = set()
            
            for det in detections:
                conf = det.conf.item()
                if conf < self.state.conf_thresh:
                    continue
                    
                xyxy = det.xyxy.cpu().numpy().squeeze().astype(int)
                xmin, ymin, xmax, ymax = xyxy
                class_idx = int(det.cls.item())
                classname = self.state.labels[class_idx]
                
                detection_data.append({
                    "class": classname,
                    "confidence": float(conf),
                    "bbox": [int(xmin), int(ymin), int(xmax), int(ymax)],
                    "class_id": class_idx
                })
                
                current_objects.add(classname)
            
            # Updating detection tracking
            current_time = time.time()
            with self.state.lock:
                # Adding new objects
                for obj in current_objects:
                    if obj not in self.state.detection_start_time:
                        self.state.detection_start_time[obj] = current_time
                
                # Removing objects that left frame
                for obj in list(self.state.detection_start_time.keys()):
                    if obj not in current_objects:
                        self.state.detection_start_time.pop(obj)
                        self.state.spoken_objects.discard(obj)
            
            # Encodeing the frame
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_b64 = base64.b64encode(buffer).decode('utf-8')
            
            # Putting in queue (non-blocking)
            if not self.state.frame_queue.full():
                self.state.frame_queue.put({
                    "frame": frame_b64,
                    "detections": detection_data,
                    "raw_frame": frame  # Keep for OCR
                })
        
        self.cap.release()
        print("Video processor stopped")

# OCR Helper
def do_ocr_on_bbox(frame, bbox):
    xmin, ymin, xmax, ymax = bbox
    crop = frame[ymin:ymax, xmin:xmax]
    
    # Preprocessing
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    gray = cv2.fastNlMeansDenoising(gray, h=10)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    text = pytesseract.image_to_string(thresh, config='--psm 6')
    if not text.strip():
        text = pytesseract.image_to_string(gray, config='--psm 6')
    
    return text.strip()

# Command Handlers
async def handle_command(command: str, websocket: WebSocket):    
    if command == "SCAN":
        with state.lock:
            state.current_mode = "SCAN"
            state.last_guidance_time.clear()
        await websocket.send_json({
            "type": "tts",
            "text": "Scan mode"
        })
        
    elif command == "GUIDE":
        with state.lock:
            state.current_mode = "GUIDE"
            state.last_guidance_time.clear()
        await websocket.send_json({
            "type": "tts",
            "text": "Guide mode"
        })
        
    elif command == "SELECT":
        # Getting latest frame data
        if not state.frame_queue.empty():
            frame_data = state.frame_queue.queue[-1]
            detections = frame_data.get("detections", [])
            
            if detections:
                # Selecting largest object
                largest = max(detections, key=lambda d: 
                    (d["bbox"][2] - d["bbox"][0]) * (d["bbox"][3] - d["bbox"][1])
                )
                
                with state.lock:
                    state.active_object = largest["class"]
                    state.active_bbox = largest["bbox"]
                    state.current_mode = "GUIDE"
                
                await websocket.send_json({
                    "type": "tts",
                    "text": f"{largest['class']} selected"
                })
            else:
                await websocket.send_json({
                    "type": "tts",
                    "text": "No objects detected"
                })
        
    elif command == "READ":
        if state.current_mode == "GUIDE" and state.active_bbox:
            if not state.frame_queue.empty():
                frame_data = state.frame_queue.queue[-1]
                raw_frame = frame_data.get("raw_frame")
                
                if raw_frame is not None:
                    # Checking if object is in good position
                    bbox = state.active_bbox
                    bbox_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                    frame_area = raw_frame.shape[0] * raw_frame.shape[1]
                    area_ratio = bbox_area / frame_area
                    
                    if area_ratio < 0.20:
                        await websocket.send_json({
                            "type": "tts",
                            "text": "Please bring the object closer to read"
                        })
                    elif area_ratio > 0.55:
                        await websocket.send_json({
                            "type": "tts",
                            "text": "Move the object slightly away"
                        })
                    else:
                        await websocket.send_json({
                            "type": "tts",
                            "text": "Reading... Hold steady"
                        })
                        
                        # Perform OCR
                        text = do_ocr_on_bbox(raw_frame, bbox)
                        
                        if text:
                            await websocket.send_json({
                                "type": "tts",
                                "text": f"Reading text: {text}"
                            })
                            await websocket.send_json({
                                "type": "ocr_result",
                                "text": text
                            })
                        else:
                            await websocket.send_json({
                                "type": "tts",
                                "text": "No text detected"
                            })
        else:
            await websocket.send_json({
                "type": "tts",
                "text": "Select an object first"
            })

# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")
    
    # Starting video processor if not running
    if not state.running:
        state.running = True
        processor = VideoProcessor(state)
        processor.start()
    
    try:
        # Creating tasks for sending and receiving
        async def send_frames():
            fps_buffer = []
            while True:
                if not state.frame_queue.empty():
                    frame_data = state.frame_queue.get()
                    
                    t_start = time.perf_counter()
                    
                    # Checking for new object announcements
                    announcements = []
                    current_time = time.time()
                    
                    with state.lock:
                        if state.current_mode == "SCAN":
                            for obj, start_time in list(state.detection_start_time.items()):
                                if obj not in state.spoken_objects and \
                                   (current_time - start_time) >= state.confirmation_time:
                                    # Determining the position same as what i have doen in yolo_detect.py
                                    for det in frame_data["detections"]:
                                        if det["class"] == obj:
                                            bbox = det["bbox"]
                                            x_center = (bbox[0] + bbox[2]) / 2
                                            frame_width = 640
                                            
                                            if x_center < frame_width / 3:
                                                position = "left"
                                            elif x_center > 2 * frame_width / 3:
                                                position = "right"
                                            else:
                                                position = "center"
                                            
                                            announcements.append(f"Detected {obj} on the {position}")
                                            state.spoken_objects.add(obj)
                                            break
                    
                    # Sending announcements
                    for announcement in announcements:
                        await websocket.send_json({
                            "type": "tts",
                            "text": announcement
                        })
                    
                    # Sending frame data
                    await websocket.send_json({
                        "type": "frame",
                        "image": frame_data["frame"],
                        "detections": frame_data["detections"],
                        "mode": state.current_mode,
                        "active_object": state.active_object,
                        "active_bbox": state.active_bbox,
                        "fps": np.mean(fps_buffer) if fps_buffer else 0
                    })
                    
                    t_stop = time.perf_counter()
                    fps_buffer.append(1 / (t_stop - t_start))
                    if len(fps_buffer) > 30:
                        fps_buffer.pop(0)
                else:
                    await asyncio.sleep(0.01)
        
        async def receive_commands():
            while True:
                data = await websocket.receive_json()
                if data.get("type") == "command":
                    await handle_command(data.get("command"), websocket)
        
        # Running both tasks concurrently
        await asyncio.gather(
            send_frames(),
            receive_commands()
        )
        
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Keeping processor running for reconnections
        pass

# Startup: Loading YOLO model
@app.on_event("startup")
async def startup_event():
    print("Loading YOLO model...")
    model_path = "/Users/rasikdhakal/Desktop/Yolo/my_model_v2/my_model_v2.pt"
    state.model = YOLO(model_path)
    state.labels = state.model.names
    print(f"Model loaded: {len(state.labels)} classes")

@app.get("/")
async def root():
    return {"status": "running", "mode": state.current_mode}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)