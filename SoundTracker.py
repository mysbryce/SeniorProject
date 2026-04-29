import pigpio
import threading
import time

# --- Pin Config ---
LEFT_SENSOR  = 17   # Pin 11 = GPIO17
RIGHT_SENSOR = 27   # Pin 13 = GPIO27
SERVO_PIN    = 18   # Pin 12 = GPIO18

# --- Servo Range ---
SERVO_MIN = 500
SERVO_MAX = 2500
SERVO_MID = 1500
STEP      = 150

# --- Global state ---
_pi       = None
_running  = False
_thread   = None
_pulse    = SERVO_MID


def _move_servo(pulse):
    global _pulse
    pulse = max(SERVO_MIN, min(SERVO_MAX, pulse))
    _pulse = pulse
    _pi.set_servo_pulsewidth(SERVO_PIN, pulse)


def _tracker_loop():
    global _running
    print("[Tracker] Sound tracking started")

    while _running:
        left  = _pi.read(LEFT_SENSOR)
        right = _pi.read(RIGHT_SENSOR)

        if left == 1 and right == 1:
            # Sound from center — face forward
            print("[Tracker] Sound CENTER")
            _move_servo(SERVO_MID)

        elif left == 1 and right == 0:
            # Sound from left — turn left
            print("[Tracker] Sound LEFT")
            _move_servo(_pulse - STEP)

        elif right == 1 and left == 0:
            # Sound from right — turn right
            print("[Tracker] Sound RIGHT")
            _move_servo(_pulse + STEP)

        time.sleep(0.05)

    # Stop servo when done
    _pi.set_servo_pulsewidth(SERVO_PIN, 0)
    print("[Tracker] Sound tracking stopped")


def start():
    """Call this to start sound tracking in background."""
    global _pi, _running, _thread, _pulse

    _pi = pigpio.pi()
    if not _pi.connected:
        raise RuntimeError(
            "pigpio not running — run: sudo systemctl start pigpio"
        )

    _pi.set_mode(LEFT_SENSOR,  pigpio.INPUT)
    _pi.set_mode(RIGHT_SENSOR, pigpio.INPUT)
    _pi.set_pull_up_down(LEFT_SENSOR,  pigpio.PUD_DOWN)
    _pi.set_pull_up_down(RIGHT_SENSOR, pigpio.PUD_DOWN)

    # Center servo on startup
    _pulse   = SERVO_MID
    _running = True
    _move_servo(SERVO_MID)
    time.sleep(0.3)

    # Run in background thread so Rose keeps working normally
    _thread = threading.Thread(target=_tracker_loop, daemon=True)
    _thread.start()


def stop():
    """Call this to stop sound tracking cleanly."""
    global _running
    _running = False
    if _thread:
        _thread.join(timeout=2)
    if _pi:
        _pi.stop()