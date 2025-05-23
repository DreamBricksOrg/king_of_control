from local_parameters import *

CAMERA1_ID = 0
CAMERA2_ID = 1
CAMERA_RESOLUTION = (640, 360)

ARDUINO_BAUD_RATE = 115200
DUMMY_ARDUINO = 0  # set to 1 to run without an Arduino

GAME_MODE = 0  # 0-NORMAL, 1-TRACK, 2-POINTS

LOG_API = "https://dbutils.ddns.net"

HEXAGONS_SVG_FILE = r"static\assets\hexagons2.svg"
HEXAGONS_SVG_OFFSET = (-75.0, 150.0)

YOLO_MODEL_HEXAGON = r"static\models\yolo11m_hexagon.pt"
xYOLO_MODEL_BALL = r"static\models\custom_ball.pt"
YOLO_MODEL_BALL = r"static\models\ucl_custom_ball_v3.pt"
YOLO_MODEL_BALL_ID = 0
MIN_CONFIDENCE_BALL = 0.65
MIN_CONFIDENCE_HEXAGON = 0.70

# game parameters
MAX_TIME = 10    # in seconds
COUNTDOWN_TIME = 4 # in seconds
END_TIME = 5
GOAL_TIME = 8
OFFSIDE_TIME = 3

TARGET_PATH_SIZE = 9
TIME_SCORE = 500   # points per second
HEX_CORRECT_SCORE = 300
HEX_WRONG_SCORE = -700
GOAL_SCORE = 1000

GAME_AUDIO = "torcida"
END_AUDIO = "3apitos"
CTA_AUDIO = "champions"
GOAL_AUDIO = "gol"
OFFSIDE_AUDIO = "1apito"
COUNTDOWN_AUDIO = "countdown"

OFFSIDE_IMAGE = r"images\offside.png"
CTA_IMAGE = r"images\cta.png"
END_IMAGE = r"images\end_game.png"
SCORE_END_IMAGE = r"images\end_game_points.png"
OFF_IMAGE = r"images\off.png"

COUNTDOWN_VIDEO = r"images\countdown_30fps.mp4"
GAME_VIDEO = r"images\game_30fps.mp4"
GOAL_VIDEO = r"images\goal_30fps.mp4"

LOGS_PATH = "logs"
STATS_LOG_FILENAME = f"{LOGS_PATH}\\hnk_reictrl_{LOCATION}.log"
LOG_FILENAME_PREFIX = "hnk_reictrl"

CALIBRATION_FILE = "calibration.json"

USE_DSHOW = True

