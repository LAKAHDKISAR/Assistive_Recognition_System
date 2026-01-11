import asyncio
import base64
import cv2
import time
import os
import json
import numpy as np
from threading import Thread, Lock
from queue import Queue
from typing import Optional, Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import pytesseract

import config


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#STATE

class AppState:
    def __init__(self):
        self.model: Optional[YOLO] = None
        self.labels: Dict[int, str] = {}

        self.current_mode = "SCAN"
        self.active_object: Optional[str] = None
        self.active_bbox: Optional[List[int]] = None

        self.frame_queue = Queue(maxsize=5)
        self.running = False
        self.lock = Lock()

        self.spoken_objects = set()
        self.detection_start_time = {}
        self.last_guidance_time = {}

        self.connected_clients = 0

        self.conf_thresh = config.CONFIDENCE_THRESHOLD
        self.camera_index = config.CAMERA_INDEX
        self.confirmation_time = config.CONFIRMATION_TIME
        self.guidance_cooldown = config.GUIDANCE_COOLDOWN

state = AppState()

#VIDEO PROCESSOR

class VideoProcessor(Thread):
    def __init__(self, state: AppState):
        super().__init__(daemon=True)
        self.state = state
        self.cap = None

    def run(self):
        print("Starting video processor...")

        try:
            self.cap = cv2.VideoCapture(
                self.state.camera_index,
                cv2.CAP_AVFOUNDATION
            )

            if not self.cap.isOpened():
                print("ERROR: Cannot open camera")
                self.state.running = False
                return

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

            print("Camera opened successfully")

            while self.state.running:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    print("Failed to read frame from camera!")
                    time.sleep(0.1)
                    continue
                else:
                    print(f"Got frame with shape: {frame.shape}")

                results = self.state.model(frame, verbose=False)
                detections = results[0].boxes

                detection_data = []
                current_objects = set()

                for det in detections:
                    conf = det.conf.item()
                    if conf < self.state.conf_thresh:
                        continue

                    bbox = det.xyxy.cpu().numpy().squeeze().astype(int)
                    bbox = [int(x) for x in bbox]

                    class_id = int(det.cls.item())
                    classname = self.state.labels[class_id]

                    detection_data.append({
                        "class": classname,
                        "confidence": float(conf),
                        "bbox": bbox,
                        "class_id": class_id
                    })

                    current_objects.add(classname)


                now = time.time()
                with self.state.lock:
                    for obj in current_objects:
                        self.state.detection_start_time.setdefault(obj, now)

                    for obj in list(self.state.detection_start_time):
                        if obj not in current_objects:
                            self.state.detection_start_time.pop(obj)
                            self.state.spoken_objects.discard(obj)

                success, buffer = cv2.imencode(
                    ".jpg", frame,
                    [cv2.IMWRITE_JPEG_QUALITY, config.JPEG_QUALITY]
                )
                if not success:
                    print("Failed to encode frame!")
                    time.sleep(0.1)
                    continue

                encoded_frame = base64.b64encode(buffer).decode()
                print(f"Encoded frame size: {len(encoded_frame)} characters")


                payload = {
                    "frame": base64.b64encode(buffer).decode(),
                    "detections": detection_data,
                    "raw_frame": frame
                }

                if self.state.frame_queue.full():
                    self.state.frame_queue.get_nowait()

                self.state.frame_queue.put(payload)
                print("Frame base64 preview:", payload["frame"][:50])

                time.sleep(0.03)

        except Exception as e:
            print("Video processor error:", e)
        finally:
            if self.cap:
                self.cap.release()
            self.state.running = False
            print("Video processor stopped")


def do_ocr_on_bbox(frame, bbox):
    x1, y1, x2, y2 = bbox
    crop = frame[y1:y2, x1:x2]

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    return pytesseract.image_to_string(gray, config="--psm 6").strip()

# COMMANDS

async def handle_command(cmd: str, ws: WebSocket):
    if cmd == "SCAN":
        state.current_mode = "SCAN"
        await ws.send_json({"type": "tts", "text": "Scan mode"})

    elif cmd == "GUIDE":
        state.current_mode = "GUIDE"
        await ws.send_json({"type": "tts", "text": "Guide mode"})

    elif cmd == "SELECT":
        if not state.frame_queue.empty():
            frame = list(state.frame_queue.queue)[-1]
            if frame["detections"]:
                obj = max(
                    frame["detections"],
                    key=lambda d: (d["bbox"][2]-d["bbox"][0]) *
                                  (d["bbox"][3]-d["bbox"][1])
                )
                state.active_object = obj["class"]
                state.active_bbox = obj["bbox"]
                await ws.send_json({"type": "tts", "text": f"{obj['class']} selected"})

    elif cmd == "READ":
        if state.active_bbox and not state.frame_queue.empty():
            frame = list(state.frame_queue.queue)[-1]
            text = do_ocr_on_bbox(frame["raw_frame"], state.active_bbox)
            await ws.send_json({"type": "tts", "text": text or "No text found"})

#WEBSOCKET

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()

    with state.lock:
        state.connected_clients += 1
        if not state.running:
            state.running = True
            VideoProcessor(state).start()

    try:
        while True:
            if not state.frame_queue.empty():
                frame = state.frame_queue.get()
                await ws.send_json({
                    "type": "frame",
                    "image": frame["frame"],
                    "detections": frame["detections"],
                    "mode": state.current_mode
                })

            try:
                msg = await asyncio.wait_for(ws.receive_json(), timeout=0.01)
                if msg.get("type") == "command":
                    await handle_command(msg["command"], ws)
            except asyncio.TimeoutError:
                pass

            await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        pass
    finally:
        with state.lock:
            state.connected_clients -= 1
            if state.connected_clients == 0:
                state.running = False

# LIFECYCLE

@app.on_event("startup")
async def startup():
    print("Loading YOLO model...")
    if not os.path.exists(config.MODEL_PATH):
        raise FileNotFoundError(config.MODEL_PATH)

    state.model = YOLO(config.MODEL_PATH)
    state.labels = state.model.names
    print("Model loaded:", list(state.labels.values()))

@app.on_event("shutdown")
async def shutdown():
    print("Shutting down backend")
    state.running = False

@app.get("/")
async def root():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)
