# Project 13 - Burglar Detector With Photo Capture
# Raspberry Pi 5 / Picamera2 version

from gpiozero import Button, MotionSensor
from picamera2 import Picamera2, Preview
from libcamera import Transform
from time import sleep, monotonic
from pathlib import Path
from datetime import datetime
from threading import Lock, Event

# GPIO pins - BCM numbering
button = Button(17, bounce_time=0.05)
pir = MotionSensor(27)

# Camera setup
picam2 = Picamera2()

# camera.rotation = 180 대체
# 180도 회전 = hflip + vflip
camera_config = picam2.create_preview_configuration(
    main={"size": (1280, 720)},
    transform=Transform(hflip=True, vflip=True)
)

picam2.configure(camera_config)

# GUI 환경에서 preview 띄우기
# SSH/headless 환경이면 이 줄을 주석 처리해도 됨
picam2.start_preview(Preview.QTGL)

picam2.start()
sleep(2)  # camera warm-up

# Save path
save_dir = Path("/home/pi/Desktop")
save_dir.mkdir(parents=True, exist_ok=True)

photo_count = 0
last_capture_time = 0
capture_interval = 10  # seconds

capture_lock = Lock()
stop_event = Event()


def stop_camera():
    print("Stopping camera...")
    stop_event.set()


def take_photo():
    global photo_count, last_capture_time

    with capture_lock:
        now = monotonic()

        # PIR 센서가 계속 감지할 때 너무 많이 찍히는 것 방지
        if now - last_capture_time < capture_interval:
            return

        last_capture_time = now
        photo_count += 1

        filename = save_dir / f"image_{photo_count}_{datetime.now():%Y%m%d_%H%M%S}.jpg"

        picam2.capture_file(str(filename))
        print(f"A photo has been taken: {filename}")


# Button press stops the program
button.when_pressed = stop_camera

# Motion detection captures photo
pir.when_motion = take_photo

try:
    print("Burglar detector is running...")
    print("Press the button to stop.")

    while not stop_event.is_set():
        sleep(0.1)

except KeyboardInterrupt:
    print("Interrupted by keyboard.")

finally:
    print("Cleaning up camera...")
    picam2.stop_preview()
    picam2.stop()
    picam2.close()
    print("Done.")
