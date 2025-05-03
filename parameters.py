
CAMERA1_ID = 0
CAMERA2_ID = 1
CAMERA_RESOLUTION = (640, 360)

ARDUINO_COM_PORT = "COM4"
ARDUINO_BAUD_RATE = 115200

HEXAGONS_SVG_FILE = r"static\assets\hexagons.svg"
HEXAGONS_SVG_OFFSET = (-75.0, 150.0)

YOLO_MODEL_HEXAGON = r"static\models\yolo11m_hexagon.pt"
xYOLO_MODEL_BALL = r"static\models\yolo11m.pt"
YOLO_MODEL_BALL = r"static\models\custom_ball.pt"
xYOLO_MODEL_BALL_ID = 32
YOLO_MODEL_BALL_ID = 0

# game parameters
MAX_TIME = 10    # in seconds
COUNTDOWN_TIME = 4 # in seconds
END_TIME = 5
GOAL_TIME = 8
OFFSIDE_TIME = 3

TARGET_PATH_SIZE = 9
TIME_SCORE = 100   # points per second
HEX_CORRECT_SCORE = 500
HEX_WRONG_SCORE = -1000

GAME_AUDIO = "torcida"
END_AUDIO = "3apitos"
CTA_AUDIO = "champions"
GOAL_AUDIO = "gol"
OFFSIDE_AUDIO = "1apito"
COUNTDOWN_AUDIO = "countdown"

OFFSIDE_IMAGE = r"images\offside.png"
CTA_IMAGE = r"images\cta.png"
END_IMAGE = r"images\end_game.png"
OFF_IMAGE = r"images\off.png"

COUNTDOWN_VIDEO = r"images\countdown.mp4"
GAME_VIDEO = r"images\game.mp4"
GOAL_VIDEO = r"images\goal.mp4"

USE_DSHOW = True
