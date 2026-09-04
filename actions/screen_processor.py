import asyncio
import base64
import io
import json
import re
import os
import sys
import time
import threading
import cv2
import mss
import mss.tools
import sounddevice as sd
import numpy as np
from pathlib import Path

try:
    import PIL.Image
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

from google import genai
from google.genai import types

def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR        = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

LIVE_MODEL          = "models/gemini-2.5-flash-native-audio-preview-12-2025"
CHANNELS            = 1
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE          = 1024

IMG_MAX_W = 640
IMG_MAX_H = 360
JPEG_Q    = 55

SYSTEM_PROMPT = (
    "You are Ultron Jarvis (Hidayat AI), an open-source assistant. "
    "Analyze images with technical precision and intelligence. "
    "Help the user in a way they can understand — don't be overly complex. "
    "Be concise, smart, and helpful like Tony Stark's AI assistant. "
    "Respond in maximum 2 short sentences. Speed is priority. "
    "Address the user as 'sir' for a tone of respect. "
    "Ask if the user needs any further help with their problem."
)


def _get_api_key() -> str:
    try:
        with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
            keys = json.load(f)
        key = keys.get("gemini_api_key", "")
        if not key:
            raise ValueError("gemini_api_key not found")
        return key
    except Exception as e:
        raise RuntimeError(f"Could not load API key: {e}")


def _get_camera_index() -> int:
    try:
        with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        if "camera_index" in cfg:
            return int(cfg["camera_index"])
    except Exception:
        pass

    print("[Camera] [FIND] No camera index in config. Auto-detecting...")
    best_index = 0

    for idx in range(6):
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            continue
        for _ in range(5):
            cap.read()
        ret, frame = cap.read()
        cap.release()
        if ret and frame is not None and frame.mean() > 5:
            best_index = idx
            print(f"[Camera] [OK] Camera found at index {idx} — saving to config.")
            break
        else:
            print(f"[Camera] [WARN]  Index {idx}: no valid frame.")

    try:
        cfg = {}
        if API_CONFIG_PATH.exists():
            with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        cfg["camera_index"] = best_index
        with open(API_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
        print(f"[Camera] [SAVE] Camera index {best_index} saved to config.")
    except Exception as e:
        print(f"[Camera] [WARN]  Could not save camera index: {e}")

    return best_index


def _to_jpeg(img_bytes: bytes) -> bytes:
    if not _PIL_OK:
        return img_bytes
    img = PIL.Image.open(io.BytesIO(img_bytes)).convert("RGB")
    resample = getattr(PIL.Image, "Resampling", PIL.Image).BILINEAR
    img.thumbnail([IMG_MAX_W, IMG_MAX_H], resample)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_Q, optimize=False)
    return buf.getvalue()


def _capture_screenshot() -> bytes:
    try:
        if _PIL_OK:
            from PIL import ImageGrab
            img = ImageGrab.grab(all_screens=True).convert("RGB")
            resample = getattr(PIL.Image, "Resampling", PIL.Image).BILINEAR
            img.thumbnail([IMG_MAX_W, IMG_MAX_H], resample)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=JPEG_Q, optimize=False)
            return buf.getvalue()
        else:
            raise RuntimeError("PIL not available")
    except Exception as e:
        print(f"[ScreenProcess] PIL ImageGrab failed ({e}). Falling back to mss.")
        with mss.mss() as sct:
            monitors = getattr(sct, "monitors", []) or []
            if len(monitors) > 1:
                monitor = monitors[1]
            elif monitors:
                monitor = monitors[0]
            else:
                raise RuntimeError("No monitors were detected for screen capture.")
            shot = sct.grab(monitor)
            png_bytes = mss.tools.to_png(shot.rgb, shot.size)
        return _to_jpeg(png_bytes)


def _capture_camera() -> bytes:
    camera_index = _get_camera_index()
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError(f"Camera could not be opened: index {camera_index}")
    for _ in range(10):
        cap.read()
    ret, frame = cap.read()
    cap.release()
    if not ret or frame is None:
        raise RuntimeError("Could not capture camera frame.")
    if _PIL_OK:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(rgb)
        img.thumbnail([IMG_MAX_W, IMG_MAX_H], PIL.Image.BILINEAR)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_Q, optimize=False)
        return buf.getvalue()
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_Q])
    return buf.tobytes()


class _LiveSession:

    def __init__(self):
        self._loop:      asyncio.AbstractEventLoop | None = None
        self._thread:    threading.Thread | None          = None
        self._session                                     = None
        self._out_queue: asyncio.Queue | None             = None
        self._audio_in:  asyncio.Queue | None             = None
        self._ready:     threading.Event                  = threading.Event()
        self._player                                      = None
        self._send_lock: asyncio.Lock | None              = None

    def start(self, player=None):
        if self._thread and self._thread.is_alive():
            return
        self._player = player
        self._thread = threading.Thread(
            target=self._run_loop, daemon=True, name="VisionSessionThread"
        )
        self._thread.start()
        ok = self._ready.wait(timeout=20)
        if not ok:
            raise RuntimeError("Vision session did not start within 20s.")
        print("[ScreenProcess] [OK] Vision session ready (no mic)")

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._main())

    async def _main(self):
        self._out_queue = asyncio.Queue(maxsize=30)
        self._audio_in  = asyncio.Queue()
        self._send_lock = asyncio.Lock()

        client = genai.Client(
            api_key=_get_api_key(),
            http_options={"api_version": "v1beta"}
        )

        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription={},
            system_instruction=SYSTEM_PROMPT,
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Charon"
                    )
                )
            ),
        )

        while True:
            try:
                print("[ScreenProcess] [CONNECT] Vision session connecting...")
                async with client.aio.live.connect(model=LIVE_MODEL, config=config) as session:
                    self._session = session
                    self._ready.set()
                    print("[ScreenProcess] [OK] Vision session connected")
                    async with asyncio.TaskGroup() as tg:
                        tg.create_task(self._send_loop())
                        tg.create_task(self._recv_loop())
                        tg.create_task(self._play_loop())
            except Exception as e:
                print(f"[ScreenProcess] [WARN] Disconnected: {e} — reconnecting...")
                self._session = None
                self._ready.clear()
                await asyncio.sleep(2)
                print("[ScreenProcess] [WARN] Reconnect attempt will retry")

    async def _send_loop(self):
        while True:
            item = await self._out_queue.get()
            if self._session:
                image_bytes, mime_type, user_text = item
                try:
                    b64 = base64.b64encode(image_bytes).decode("utf-8")
                    await self._session.send_client_content(
                        turns={
                            "parts": [
                                {"inline_data": {"mime_type": mime_type, "data": b64}},
                                {"text": user_text}
                            ]
                        },
                        turn_complete=True
                    )
                    print("[ScreenProcess] [OK] Image sent")
                except Exception as e:
                    print(f"[ScreenProcess] [WARN] Send error: {e}")
                    if self._player and hasattr(self._player, "set_scanning"):
                        self._player.set_scanning(False, "")
                        if hasattr(self._player, "write_log"):
                            self._player.write_log("System Event: Failed to transmit screen to AI. Please check your internet connection or API key.")
            else:
                print("[ScreenProcess] [WARN] Session not ready, discarding message")
                if self._player and hasattr(self._player, "set_scanning"):
                    self._player.set_scanning(False, "")
                    if hasattr(self._player, "write_log"):
                        self._player.write_log("System Event: The AI Vision module is currently offline. It might be reconnecting.")

    async def _recv_loop(self):
        transcript_buf: list[str] = []
        try:
            async for response in self._session.receive():
                if response.data:
                    await self._audio_in.put(response.data)
                sc = response.server_content
                if not sc:
                    continue

                if sc.output_transcription and sc.output_transcription.text:
                    chunk = sc.output_transcription.text.strip()
                    if chunk:
                        transcript_buf.append(chunk)

                if sc.turn_complete:
                    if transcript_buf and self._player:
                        full = re.sub(r'\s+', ' ', " ".join(transcript_buf)).strip()
                        if full:
                            self._player.write_log(f"Ultron Jarvis: {full}")
                            print(f"[ScreenProcess] [MSG] {full}")
                            if hasattr(self._player, "set_scanning"):
                                self._player.set_scanning(False, "")
                    transcript_buf = []
        except Exception as e:
            print(f"[ScreenProcess] [ERR] Recv error: {e}")
            transcript_buf = []
            if self._player and hasattr(self._player, "set_scanning"):
                self._player.set_scanning(False, "")
            await asyncio.sleep(0.3)

    async def _play_loop(self):
        stream = sd.RawOutputStream(
            samplerate=RECEIVE_SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=CHUNK_SIZE,
        )
        stream.start()
        try:
            while True:
                chunk = await self._audio_in.get()
                await asyncio.to_thread(stream.write, chunk)
        except Exception as e:
            print(f"[ScreenProcess] [ERR] Play error: {e}")
            raise
        finally:
            stream.stop()
            stream.close()

    def analyze(self, image_bytes: bytes, mime_type: str, user_text: str):
        import time
        # Wait for the background thread to initialize the event loop
        for _ in range(50):
            if self._loop:
                break
            time.sleep(0.1)
            
        if not self._loop:
            print("[ScreenProcess] [ERR] Failed to start async loop")
            return
        if not self._out_queue:
            print("[ScreenProcess] [ERR] Out queue is not initialized")
            return
        print(f"[ScreenProcess] enqueueing payload: {len(image_bytes)} bytes, mime={mime_type}, text={user_text[:40]}")
        asyncio.run_coroutine_threadsafe(
            self._out_queue.put((image_bytes, mime_type, user_text)),
            self._loop
        )

    def is_ready(self) -> bool:
        return self._session is not None


_live       = _LiveSession()
_started    = False
_start_lock = threading.Lock()


def _ensure_started(player=None):
    global _started
    with _start_lock:
        if not _started:
            _live.start(player=player)
            _started = True
        elif player is not None:
            _live._player = player


def screen_process(
    parameters:     dict,
    response:       str | None = None,
    player=None,
    session_memory=None,
    image_bytes:    bytes | None = None,
) -> bool:
    user_text = (parameters or {}).get("text") or (parameters or {}).get("user_text", "")
    user_text = (user_text or "").strip()
    if not user_text:
        print("[ScreenProcess] [WARN] No user_text provided.")
        return False

    angle = (parameters or {}).get("angle", "screen").lower().strip()
    print(f"[ScreenProcess] angle={angle!r}  text={user_text!r}")

    def _screen_failure(message: str) -> bool:
        print(f"[ScreenProcess] [FAIL] {message}")
        if player and hasattr(player, "update_task_workspace"):
            try:
                player.update_task_workspace(
                    status="Screen analysis failed",
                    output=message,
                    percent=0,
                )
            except Exception:
                pass
        if player and hasattr(player, "write_log"):
            player.write_log(f"System Event: {message}")
        if player and hasattr(player, "set_scanning") and angle != "camera":
            player.set_scanning(False, "")
        return False

    try:
        _ensure_started(player=player)
    except Exception as e:
        import traceback; traceback.print_exc()
        msg = f"[ScreenProcess] [ERR] Vision initialization failed: {e}"
        print(msg)
        return _screen_failure("Vision module failed to initialize. Check your internet connection and API key.")

    if player and hasattr(player, "set_scanning") and angle != "camera":
        player.set_scanning(True, "SCANNING SCREEN")

    try:
        if angle == "camera":
            image_bytes = _capture_camera()
            mime_type   = "image/jpeg"
            print("[ScreenProcess] [CAMERA] Camera captured")
        else:
            if image_bytes:
                mime_type = "image/jpeg"
                print("[ScreenProcess] [SCREEN] Using pre-captured UI screenshot")
            else:
                image_bytes = _capture_screenshot()
                mime_type   = "image/jpeg" if _PIL_OK else "image/png"
                print("[ScreenProcess] [SCREEN] Screen captured")
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"[ScreenProcess] [ERR] Capture error: {e}")
        return _screen_failure("Failed to capture the screen. Please ensure the application has permission to capture your display.")

    if not image_bytes:
        print("[ScreenProcess] [ERR] No image bytes available for analysis.")
        return _screen_failure("Screen capture returned empty data. Try again or restart the app.")

    if not _live.is_ready():
        print("[ScreenProcess] [ERR] Vision module is not ready to send image.")
        return _screen_failure("Vision module is offline. It may still be reconnecting.")

    # Prevent getting stuck if screen capture fails and returns None
    if not image_bytes:
        print("[ScreenProcess] [ERR] Failed to capture image bytes.")
        if player and hasattr(player, "set_scanning") and angle != "camera":
            player.set_scanning(False, "")
            if hasattr(player, "write_log"):
                player.write_log("System Event: Failed to capture screen (Windows graphics function failed). Please check your display settings.")
        return False

    print(f"[ScreenProcess] [PKG] {len(image_bytes)} bytes → sending")
    _live.analyze(image_bytes, mime_type, user_text)
    return True


def warmup_session(player=None):
    try:
        _ensure_started(player=player)
    except Exception as e:
        print(f"[ScreenProcess] [WARN] Warmup error: {e}")


if __name__ == "__main__":
    print("[TEST] screen_processor.py v8 — image-only session")
    print("=" * 50)
    mode    = input("screen / camera (default: screen): ").strip().lower() or "screen"
    request = input("Question (Enter for default): ").strip() or "What do you see? Be brief."

    t0 = time.perf_counter()
    warmup_session()
    print(f"Session ready — {time.perf_counter()-t0:.2f}s\n")

    t1     = time.perf_counter()
    result = screen_process({"angle": mode, "text": request}, player=None)
    print(f"Sent — {time.perf_counter()-t1:.3f}s | audio incoming...")
    time.sleep(8)
    print(f"\n{'[OK]' if result else '[ERR]'}")
