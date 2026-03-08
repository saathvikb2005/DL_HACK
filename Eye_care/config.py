CAMERA_INDEX = 0

CAPTURE_FPS = 30
PROCESS_EVERY_N_FRAMES = 1

EAR_BLINK_THRESHOLD = 0.24
EAR_CONSEC_FRAMES = 3

# ── Fatigue Detection Thresholds ──
LOW_BLINK_RATE = 10
CONTINUOUS_STARE_SEC = 20
MAX_SCREEN_TIME_MIN = 40
BREAK_DURATION_SEC = 20

# ── Yawn Detection Thresholds ──
EXCESSIVE_YAWNS_COUNT = 3      # Yawns per time window
YAWN_WINDOW_MIN = 5             # Time window in minutes
YAWN_FATIGUE_THRESHOLD = 2      # Yawns in short period = high fatigue

COOLDOWN_BLINK = 120
COOLDOWN_STARE = 60
COOLDOWN_SCREEN_TIME = 300
COOLDOWN_YAWN = 180  # 3 minutes cooldown for yawn fatigue alerts

SAVE_VIDEO = False
CLOUD_PROCESSING = False