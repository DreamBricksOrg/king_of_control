import copy
import traceback
import json
from typing import List, Tuple

import cv2
import parameters as param
from hexagons_board import HexagonsBoard
from hex_board_model import HexBoardModel
from yolo_object_detector import YoloObjectDetector
from dual_camera import DualCamera
import time
from cv2_utils import stack_frames_vertically, draw_cross, draw_yolo_box
from hex_graph import HexGraph
from led_panel import LedPanel
from game_status import GameStatus
import logging
from utils import generate_timestamped_filename, ensure_directory


# Custom filter to only allow selected INFO logs
class StatsFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.INFO and 'STATS' in record.msg


# Configure logging to write to a file and to the std output
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a file handler and set its format and level
ensure_directory(param.LOGS_PATH)
log_filename = generate_timestamped_filename(param.LOGS_PATH, param.LOG_FILENAME_PREFIX, "log")
file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

stats_handler = logging.FileHandler(param.STATS_LOG_FILENAME)
stats_handler.setLevel(logging.INFO)
stats_handler.addFilter(StatsFilter())  # Apply filter
stats_handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))

# Create a stream handler and set its format and level
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stats_handler)
logger.addHandler(stream_handler)


logger = logging.getLogger(__name__)


class KingOfControl:
    class GameVariables:
        def __init__(self, graph):
            self.graph = graph
            self.ball_detector = YoloObjectDetector(class_id=param.YOLO_MODEL_BALL_ID, model_path=param.YOLO_MODEL_BALL)
            self.paths = self.choose_new_paths()
            self.start_brightness = 128
            self.brightness_direction = 10
            self.change_status_time = time.time()
            self.start_time = time.time()
            self.playing_time = 0
            self.chosen_path = None
            self.correct = set()
            self.wrong = set()
            self.current_status = GameStatus.BLANK
            self.draw_ball = True

        def choose_new_paths(self):
            self.paths = [self.graph.create_random_path_target_size(0, param.TARGET_PATH_SIZE),
                          self.graph.create_random_path_target_size(1, param.TARGET_PATH_SIZE)]
            return self.paths

    def __init__(self):
        self.clicked_point = None
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.HEX_CAL_COORD = [(2, 1), (0, 1), (0, 7), (2, 7)]

        logger.debug("Init Arduino")
        self.board = HexagonsBoard(port=param.ARDUINO_COM_PORT, baudrate=param.ARDUINO_BAUD_RATE)

        logger.debug("Init cameras")
        self.cameras = DualCamera(cam1_id=param.CAMERA1_ID, cam2_id=param.CAMERA2_ID,
                                  res1=param.CAMERA_RESOLUTION, res2=param.CAMERA_RESOLUTION)
        logger.debug("Init Board Model")
        self.hex_model_cam1 = HexBoardModel(param.HEXAGONS_SVG_FILE, center_offset=param.HEXAGONS_SVG_OFFSET, cam_pos=(0, param.CAMERA_RESOLUTION[1]*2))
        self.hex_model_cam2 = HexBoardModel(param.HEXAGONS_SVG_FILE, center_offset=param.HEXAGONS_SVG_OFFSET, cam_pos=(param.CAMERA_RESOLUTION[0]*2, param.CAMERA_RESOLUTION[1]*2))
        self.graph = HexGraph()
        self.led_panel = LedPanel(
            state_play_duration=param.MAX_TIME,
            countdown_video_path=param.COUNTDOWN_VIDEO,
            game_video_path=param.GAME_VIDEO,
            goal_video_path=param.GOAL_VIDEO,
            cta_image=param.CTA_IMAGE,
            offside_image=param.OFFSIDE_IMAGE,
            endgame_image=param.END_IMAGE,
            game_audio=param.GAME_AUDIO,
            cta_audio=param.CTA_AUDIO,
            goal_audio=param.GOAL_AUDIO,
            end_audio=param.END_AUDIO,
            off_image=param.OFF_IMAGE,
            offside_audio=param.OFFSIDE_AUDIO,
            countdown_audio=param.COUNTDOWN_AUDIO
        )

        self.game_vars = self.GameVariables(self.graph)
        self.prev_camera1_exposure = 0
        self.prev_camera2_exposure = 0

    def camera_setup(self):
        final_width = 800
        final_height = 225
        self.display_all_calibration_hexagons()
        exp1, exp2, key = self.cameras.display(final_width, final_height, vertical=0)
        logger.debug(f"Cameras exposures: {exp1} & {exp2}")

        if key == ord('r'):
            floor_quad1, floor_quad2 = self.load_floor_quads(param.CALIBRATION_FILE)
            self.hex_model_cam1.set_calibration_points(floor_quad1)
            self.hex_model_cam2.set_calibration_points(floor_quad2)
            return True

        return False

    def calibration(self):
        #self.led_panel.set_state(GameStatus.BLANK)
        self.led_panel.show_calibration_screen()

        hex_detector = YoloObjectDetector(class_id=0, model_path=param.YOLO_MODEL_HEXAGON)
        floor_quad1, floor_quad2 = self.get_calibration_points(hex_detector)

        self.led_panel.destroy_calibration_screen()

        self.hex_model_cam1.set_calibration_points(floor_quad1)
        self.hex_model_cam2.set_calibration_points(floor_quad2)

        self.save_floor_quads(param.CALIBRATION_FILE, floor_quad1, floor_quad2)

        self.restore_game_brightness()

    def manual_calibration(self):
        self.restore_game_brightness()

        floor_quad1 = self.get_calibration_points_from_mouse(1)
        floor_quad2 = self.get_calibration_points_from_mouse(2)

        self.hex_model_cam1.set_calibration_points(floor_quad1)
        self.hex_model_cam2.set_calibration_points(floor_quad2)

        self.save_floor_quads(param.CALIBRATION_FILE, floor_quad1, floor_quad2)

    def shutdown(self):
        self.led_panel.set_state(GameStatus.SHUTDOWN)
        self.led_panel.join()
        logger.debug("Led Panel Thread finished")
        cv2.destroyWindow("game")
        exit(0)

    def get_hex_under_ball_and_show_cameras(self):
        hex, frame1, frame2 = self.get_hex_under_ball(self.game_vars.ball_detector)
        composed_frame = stack_frames_vertically(frame1, frame2, 640, 720)
        cv2.imshow("game", composed_frame)

        return hex

    def run_cta(self):
        logger.debug("Running CTA")
        # waits for the player to put the ball on one of the first hexagons

        # update LEDs of starting hexagons
        self.game_vars.start_brightness += self.game_vars.brightness_direction
        if self.game_vars.start_brightness >= 255:
            self.game_vars.start_brightness = 255
            self.game_vars.brightness_direction = -self.game_vars.brightness_direction
        elif self.game_vars.start_brightness <= 0:
            self.game_vars.start_brightness = 0
            self.game_vars.brightness_direction = -self.game_vars.brightness_direction

        hex_color = (self.game_vars.start_brightness, self.game_vars.start_brightness, self.game_vars.start_brightness)
        self.board.set_hexagon(0, 0, hex_color)
        self.board.set_hexagon(1, 0, hex_color)

        hex = self.get_hex_under_ball_and_show_cameras()

        # put the ball in one the starting hexagons
        if hex and hex[1] == 0:
            self.game_vars.chosen_path = self.game_vars.paths[hex[0]]
            return GameStatus.COUNTDOWN

        return GameStatus.CTA

    def run_countdown(self):
        self.get_hex_under_ball_and_show_cameras()

        duration = time.time() - self.game_vars.change_status_time
        if duration >= param.COUNTDOWN_TIME:
            return GameStatus.GAME

        return GameStatus.COUNTDOWN

    def run_goal(self):
        duration = time.time() - self.game_vars.change_status_time
        if duration >= param.GOAL_TIME:
            return GameStatus.END

        return GameStatus.GOAL

    def run_offside(self):
        duration = time.time() - self.game_vars.change_status_time
        if duration >= param.OFFSIDE_TIME:
            return GameStatus.END

        return GameStatus.OFFSIDE

    def run_end(self):
        duration = time.time() - self.game_vars.change_status_time
        if duration >= param.END_TIME:
            return GameStatus.CTA

        return GameStatus.END

    def run_off(self):
        return GameStatus.OFF

    def run_game(self):
        self.game_vars.playing_time = time.time() - self.game_vars.start_time
        logger.info(f"Running Game: {self.game_vars.playing_time}")
        if self.game_vars.playing_time >= param.MAX_TIME:
            self.game_vars.playing_time = param.MAX_TIME
            return GameStatus.END

        hex = self.get_hex_under_ball_and_show_cameras()

        # if goal
        if hex and hex[1] == 8:
            return GameStatus.GOAL

        if hex in self.game_vars.chosen_path and hex not in self.game_vars.correct:
            self.board.set_hexagon(*hex, self.GREEN)
            self.game_vars.correct.add(hex)
            logger.info(f"Score: {self.calculate_score(len(self.game_vars.correct), len(self.game_vars.wrong), 0.0)}")

        if hex and hex not in self.game_vars.chosen_path and hex not in self.game_vars.wrong:
            self.board.set_hexagon(*hex, self.RED)
            self.game_vars.wrong.add(hex)
            logger.info(f"Score: {self.calculate_score(len(self.game_vars.correct), len(self.game_vars.wrong), 0.0)}")
            return GameStatus.OFFSIDE

        return GameStatus.GAME

    def game(self):

        self.game_vars.current_status = GameStatus.BLANK
        next_status = GameStatus.CTA
        while True:
            if self.game_vars.current_status == GameStatus.CTA:
                next_status = self.run_cta()
            elif self.game_vars.current_status == GameStatus.COUNTDOWN:
                next_status = self.run_countdown()
            elif self.game_vars.current_status == GameStatus.GAME:
                next_status = self.run_game()
            elif self.game_vars.current_status == GameStatus.GOAL:
                next_status = self.run_goal()
            elif self.game_vars.current_status == GameStatus.OFFSIDE:
                next_status = self.run_offside()
            elif self.game_vars.current_status == GameStatus.END:
                next_status = self.run_end()
            elif self.game_vars.current_status == GameStatus.OFF:
                next_status = self.run_off()

            if self.game_vars.current_status != next_status:
                logger.info(f"STATS: {next_status}")
                self.game_vars.current_status = next_status
                self.game_vars.change_status_time = time.time()
                self.led_panel.set_state(self.game_vars.current_status)

                if self.game_vars.current_status == GameStatus.CTA:
                    self.game_vars.start_brightness = 0
                    self.game_vars.brightness_direction = 10
                    self.game_vars.choose_new_paths()
                    self.board.clear()
                    self.board.set_goal(self.WHITE)

                elif self.game_vars.current_status == GameStatus.COUNTDOWN:
                    self.board.clear()
                    self.board.set_hexagon(*self.game_vars.chosen_path[0], self.GREEN)

                elif self.game_vars.current_status == GameStatus.GAME:
                    # shows the path
                    self.board.clear()
                    for i, node in enumerate(self.game_vars.chosen_path):
                        if i > 0:
                            self.board.set_hexagon(*node, self.WHITE)

                    # game starts
                    self.game_vars.start_time = time.time()
                    self.game_vars.correct = set()
                    self.game_vars.wrong = set()

                elif self.game_vars.current_status == GameStatus.GOAL:
                    self.board.set_goal(self.GREEN)

                elif self.game_vars.current_status == GameStatus.OFFSIDE:
                    self.board.set_goal(self.RED)

                elif self.game_vars.current_status == GameStatus.END:
                    self.board.set_goal(self.RED)

                elif self.game_vars.current_status == GameStatus.OFF:
                    self.board.clear()

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                logger.info("Exiting program")
                self.shutdown()
            elif key == ord('b'):
                self.game_vars.draw_ball = not self.game_vars.draw_ball
                logger.debug(f"Draw ball: {self.game_vars.draw_ball}")
            elif key == ord('p'):
                if self.game_vars.current_status == GameStatus.OFF:
                    self.game_vars.current_status = GameStatus.END
                else:
                    self.game_vars.current_status = GameStatus.OFF
                    self.led_panel.set_state(self.game_vars.current_status)
            elif key == ord('a'):
                self.cameras.init1.set_exposure(self.cameras.init1.get_exposure() - 1)
            elif key == ord('s'):
                self.cameras.init1.set_exposure(self.cameras.init1.get_exposure() + 1)
            elif key == ord('z'):
                self.cameras.init2.set_exposure(self.cameras.init2.get_exposure() - 1)
            elif key == ord('x'):
                self.cameras.init2.set_exposure(self.cameras.init2.get_exposure() + 1)

        time_left = param.MAX_TIME - self.game_vars.playing_time
        score = self.calculate_score(len(self.game_vars.correct), len(self.game_vars.wrong), time_left)
        logger.debug(f"Score: {score}")
        self.led_panel.set_score_value(int(score))
        # self.led_panel.set_state()

    def game_db(self):
        white = (255, 255, 255)
        red = (255, 0, 0)
        green = (0, 255, 0)
        ball_detector = self.game_vars.ball_detector  # YoloObjectDetector(class_id=param.YOLO_MODEL_BALL_ID, model_path=param.YOLO_MODEL_BALL)

        paths = [self.graph.create_random_path_target_size(0, param.TARGET_PATH_SIZE),
                 self.graph.create_random_path_target_size(1, param.TARGET_PATH_SIZE)]
        chosen_path = 0

        # waits for the player to put the ball on one of the first hexagons
        brightness = 0
        direction = 10
        self.board.clear()
        self.led_panel.set_state(GameStatus.CTA)
        while True:
            # update LEDs of starting hexagons
            brightness += direction
            if brightness >= 255:
                brightness = 255
                direction = -direction
            elif brightness <= 0:
                brightness = 0
                direction = -direction

            self.board.set_hexagon(0, 0, (brightness, brightness, brightness))
            self.board.set_hexagon(1, 0, (brightness, brightness, brightness))

            hex, frame1, frame2 = self.get_hex_under_ball(ball_detector)

            composed_frame = stack_frames_vertically(frame1, frame2, 640, 720)
            cv2.imshow("game", composed_frame)

            # put the ball in one the starting hexagons
            if hex and hex[1] == 0:
                chosen_path = paths[hex[0]]
                break

            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                exit(0)

        # shows the path
        self.board.clear()
        for node in chosen_path:
            self.board.set_hexagon(*node, white)


        # game starts
        start_time = time.time()
        self.led_panel.set_state(GameStatus.GAME)
        path = set(chosen_path)
        correct = set()
        wrong = set()
        while True:
            playing_time = time.time() - start_time
            if playing_time > param.MAX_TIME:
                break

            hex, frame1, frame2 = self.get_hex_under_ball(ball_detector)

            # if goal
            if hex and hex[1] == 8:
                break

            if hex in path and hex not in correct:
                self.board.set_hexagon(*hex, green)
                correct.add(hex)
                logger.info(f"Score: {self.calculate_score(len(correct), len(wrong), 0.0)}")

            if hex and hex not in path and hex not in wrong:
                self.board.set_hexagon(*hex, red)
                wrong.add(hex)
                logger.info(f"Score: {self.calculate_score(len(correct), len(wrong), 0.0)}")

            composed_frame = stack_frames_vertically(frame1, frame2, 640, 720)
            cv2.imshow("game", composed_frame)

            # if hex and hex[1] == 7:
            #    break

        playing_time = min(time.time() - start_time, param.MAX_TIME)
        time_left = param.MAX_TIME - playing_time
        score = self.calculate_score(len(correct), len(wrong), time_left)
        logger.info(f"Score: {score}")
        self.led_panel.set_score_value(int(score))
        self.led_panel.set_state(GameStatus.END)

    @staticmethod
    def calculate_score(num_correct, num_wrong, time_left):
        return time_left * param.TIME_SCORE + \
            num_correct * param.HEX_CORRECT_SCORE + \
            num_wrong * param.HEX_WRONG_SCORE

    def get_hex_under_ball(self, ball_detector, update_frames=True):
        frame1, frame2 = self.cameras.get_frames()

        bbox1, conf = ball_detector.detect_best(frame1, param.MIN_CONFIDENCE_BALL)
        bbox2 = None

        hex = None
        cam_used = 0
        hexagon = None
        ball_pos = (0, 0)
        if bbox1 is not None:
            idx, enabled_polygon, ball_pos = self.hex_model_cam1.get_polygon_under_ball(bbox1)
            cam_used = 1

            if enabled_polygon:
                hex = self.hex_model_cam1.hex_coordinates[idx]
                hexagon = self.hex_model_cam1.pers_polygons[idx]

        else:
            bbox2, conf = ball_detector.detect_best(frame2, param.MIN_CONFIDENCE_BALL)
            if bbox2 is not None:
                idx, enabled_polygon, ball_pos = self.hex_model_cam2.get_polygon_under_ball(bbox2)
                cam_used = 2

                if enabled_polygon:
                    hex = self.hex_model_cam2.hex_coordinates[idx]
                    hexagon = self.hex_model_cam2.pers_polygons[idx]

        if update_frames:
            self.hex_model_cam1.draw_hexagons(frame1, color=(200, 100, 100))
            self.hex_model_cam2.draw_hexagons(frame2, color=(200, 100, 100))

            if cam_used == 1:
                if hexagon is not None:
                    self.hex_model_cam1.draw_polylines(frame1, hexagon, color=(0, 255, 255))
                if self.game_vars.draw_ball:
                    draw_yolo_box(frame1, box=bbox1, label="Ball", conf=conf)
                    draw_cross(frame1, ball_pos, color=(255, 255, 0))

            elif cam_used == 2:
                if hexagon is not None:
                    self.hex_model_cam2.draw_polylines(frame2, hexagon, color=(0, 255, 255))
                if self.game_vars.draw_ball:
                    draw_yolo_box(frame2, box=bbox2, label="Ball", conf=conf)
                    draw_cross(frame2, ball_pos, color=(255, 255, 0))

        return hex, frame1, frame2

    def track_ball(self):
        ball_detector = YoloObjectDetector(class_id=param.YOLO_MODEL_BALL_ID, model_path=param.YOLO_MODEL_BALL)
        last_hex = None
        while True:
            hex, frame1, frame2 = self.get_hex_under_ball(ball_detector)

            if hex != last_hex:
                if last_hex is not None:
                    self.board.set_hexagon(*last_hex, (0, 0, 0))
                if hex is not None:
                    self.board.set_hexagon(*hex, (255, 255, 0))
                last_hex = hex

            composed_frame = stack_frames_vertically(frame1, frame2, 640, 720)
            winname = "Pressione espaco para continuar..."
            cv2.imshow(winname, composed_frame)

            if cv2.waitKey(1) & 0xFF == ord(' '):
                cv2.destroyWindow(winname)
                break

    def calibration_debug(self):
        magenta = (255, 0, 255)

        frame1, frame2 = self.cameras.get_frames()
        self.hex_model_cam1.draw_hexagons(frame1, color=magenta)
        self.hex_model_cam2.draw_hexagons(frame2, color=magenta)
        composed_frame = stack_frames_vertically(frame1, frame2, 640, 720)

        winname = None
        if composed_frame is not None:
            winname = "Pressione espaco para continuar..."
            cv2.imshow(winname, composed_frame)

        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):
                if winname:
                    cv2.destroyWindow(winname)
                break
            elif key == ord('m'):
                if winname:
                    cv2.destroyWindow(winname)
                logger.debug("Manual calibration")
                raise RuntimeError
            elif key == ord('q'):
                self.shutdown()

    def display_all_calibration_hexagons(self):
        self.board.clear()
        for coord in self.HEX_CAL_COORD:
            self.board.set_hexagon(*coord, self.RED)

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            #logger.debug(f"Clicked at: ({x}, {y})")
            self.clicked_point = (x, y)

    def open_window_user_selection(self, frame):
        winname = "Selecione meio do hexagono vermelho"
        # Show image window
        cv2.namedWindow(winname)
        self.clicked_point = None
        cv2.setMouseCallback(winname, self.mouse_callback)

        frame_copy = copy.deepcopy(frame)
        while True:
            # Show current image (with markers if needed)
            if self.clicked_point:
                frame_copy = copy.deepcopy(frame)
                cv2.circle(frame_copy, self.clicked_point, 5, (0, 0, 255), -1)

            cv2.imshow(winname, frame_copy)
            key = cv2.waitKey(1)

            if key & 0xFF == ord(' '):  # SPACE key to exit
                break

        cv2.destroyWindow(winname)

        if self.clicked_point is None or len(self.clicked_point) == 0:
            return None

        logger.debug("Selected point:", self.clicked_point)
        return self.clicked_point[0], self.clicked_point[1], self.clicked_point[0], self.clicked_point[1]

    def get_calibration_points_from_mouse(self, camera_id):
        debug_calibration = True
        bboxes = []

        coord_idx = 0
        num_exceptions = 0
        while coord_idx < len(self.HEX_CAL_COORD):
            coord = self.HEX_CAL_COORD[coord_idx]

            #self.led_panel.show_calibration_screen()
            #cv2.waitKey(3)

            # light up one hexagon
            self.board.clear()
            self.board.set_hexagon(*coord, self.RED)
            time.sleep(0.2)
            _, _ = self.cameras.get_frames()
            time.sleep(0.2)
            frame1, frame2 = self.cameras.get_frames()

            frame = frame1 if camera_id == 1 else frame2
            results = None

            # find it in both cameras
            bbox = self.open_window_user_selection(frame)
            if bbox is None:
                num_exceptions += 1
                if num_exceptions > 5:
                    self.show_frame(frame1)
                    logger.error(f"Erro na calibracao da camera {camera_id}")
                    raise RuntimeError(f"Erro na calibracao da camera {camera_id}")
                time.sleep(0.3)
                continue

            bboxes.append(bbox)

            coord_idx += 1
            num_exceptions = 0

        self.board.clear()
        if camera_id == 1:
            floor_quad = self.hex_model_cam1.calculate_floor_quad(bboxes)
        else:
            floor_quad = self.hex_model_cam2.calculate_floor_quad(bboxes)

        return floor_quad

    def get_calibration_points(self, yolo_object_detector):
        debug_calibration = True
        bboxes1 = []
        bboxes2 = []

        coord_idx = 0
        num_exceptions1 = 0
        num_exceptions2 = 0
        while coord_idx < len(self.HEX_CAL_COORD):
            coord = self.HEX_CAL_COORD[coord_idx]

            #self.led_panel.show_calibration_screen()
            #cv2.waitKey(3)

            # light up one hexagon
            self.board.clear()
            self.board.set_hexagon(*coord, self.RED)
            time.sleep(0.2)
            _, _ = self.cameras.get_frames()
            time.sleep(0.2)
            frame1, frame2 = self.cameras.get_frames()
            results1 = None

            # find it in both cameras
            bbox1, conf = yolo_object_detector.detect_best(frame1, param.MIN_CONFIDENCE_HEXAGON)
            if bbox1 is None:
                num_exceptions1 += 1
                if num_exceptions1 > 5:
                    self.show_frame(frame1)
                    logger.error(f"Erro na calibracao da camera 1")
                    raise RuntimeError(f"Erro na calibracao da camera 1")
                time.sleep(0.3)
                continue

            if debug_calibration:
                results1 = yolo_object_detector.get_last_results()

            bbox2, conf = yolo_object_detector.detect_best(frame2, param.MIN_CONFIDENCE_HEXAGON)
            if bbox2 is None:
                num_exceptions2 += 1
                if num_exceptions2 > 5:
                    self.show_frame(frame2)
                    logger.error(f"Erro na calibracao da camera 2")
                    raise RuntimeError(f"Erro na calibracao da camera 2")
                time.sleep(0.3)
                continue

            if debug_calibration:
                results2 = yolo_object_detector.get_last_results()

                # Draw detections using built-in plot() method
                annotated_frame1 = results1[0].plot()
                annotated_frame2 = results2[0].plot()

                composed_frame = stack_frames_vertically(annotated_frame1, annotated_frame2, 640, 720)
                self.show_frame(composed_frame)

            bboxes1.append(bbox1)
            bboxes2.append(bbox2)

            coord_idx += 1
            num_exceptions1 = 0
            num_exceptions2 = 0

        self.board.clear()
        floor_quad1 = self.hex_model_cam1.calculate_floor_quad(bboxes1)
        floor_quad2 = self.hex_model_cam1.calculate_floor_quad(bboxes2)

        return floor_quad1, floor_quad2


    @staticmethod
    def save_floor_quads(file_path: str, floor_quad1: List[int], floor_quad2: List[int]) -> None:
        data = {
            "floor_quad1": floor_quad1,
            "floor_quad2": floor_quad2
        }
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load_floor_quads(file_path: str) -> Tuple[List[int], List[int]]:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data["floor_quad1"], data["floor_quad2"]

    @staticmethod
    def show_frame(frame, winname="Pressione espaco para continuar..."):
        while True:
            cv2.imshow(winname, frame)
            if cv2.waitKey(1) & 0xFF == ord(' '):
                cv2.destroyWindow(winname)
                break

    def debug_hex_led_mapping(self):
        hex_id = 0
        num_hexes = len(self.hex_model_cam1.hexagons)
        while True:
            frame1, frame2 = self.cameras.get_frames()

            hexagon = self.hex_model_cam1.hexagons[hex_id]
            pers_hex = self.hex_model_cam1.pers_polygons[hex_id]
            hex_coord = self.hex_model_cam1.hex_coordinates[(hex_id + 1) % num_hexes]

            self.hex_model_cam1.draw_hexagons(frame1, color=(100, 100, 100))
            self.hex_model_cam1.draw_polylines(frame1, pers_hex, color=(0, 255, 255))

            composed_frame = frame1  # stack_frames_vertically(frame1, frame2, 640, 720)
            winname = "Pressione espaco para continuar..."
            cv2.imshow(winname, composed_frame)

            logger.debug(f"hexagon: {len(hexagon)}-{self.hex_model_cam1.get_avg_point(hexagon)}-{hexagon}")
            logger.debug(f"pers_hex: {len(pers_hex)}-{self.hex_model_cam1.get_avg_point(pers_hex)}-{pers_hex}")
            logger.debug(f"hex_coord: {hex_coord}")
            self.board.set_hexagon(*hex_coord, (255, 255, 0))
            time.sleep(2)
            self.board.set_hexagon(*hex_coord, (0, 0, 0))
            hex_id = (hex_id + 1) % num_hexes

            if cv2.waitKey(1) & 0xFF == ord(' '):
                cv2.destroyWindow(winname)
                break

    def store_game_brightness(self):
        # store game brightness
        self.prev_camera1_exposure = self.cameras.init1.get_exposure()
        self.prev_camera2_exposure = self.cameras.init2.get_exposure()

    def restore_game_brightness(self):
        # restore game brightness
        self.cameras.init1.set_exposure(self.prev_camera1_exposure)
        self.cameras.init2.set_exposure(self.prev_camera2_exposure)

    def calibration_auto_exposure(self):
        self.display_all_calibration_hexagons()
        self.led_panel.show_calibration_screen()

        hex_detector = YoloObjectDetector(class_id=0, model_path=param.YOLO_MODEL_HEXAGON)

        self.store_game_brightness()

        logger.debug("calibrating camera 1")
        self.calibrate_camera_exposure(hex_detector, 1)
        logger.debug("calibrating camera 2")
        self.calibrate_camera_exposure(hex_detector, 2)

    @staticmethod
    def calculate_calibration_score(target_num_boxes, boxes, avg_conf):
        score = avg_conf * 100
        if len(boxes) < target_num_boxes:
            score -= 30 * (target_num_boxes - len(boxes))
        elif len(boxes) > target_num_boxes:
            score -= 10 * (len(boxes) - target_num_boxes)

        return score

    def calibrate_camera_exposure(self, hex_detector, camera_id):
        min_exposure = param.MIN_CALIBRATION_EXPOSURE
        max_exposure = param.MAX_CALIBRATION_EXPOSURE
        best_score = -100000
        best_exposure = min_exposure
        exposure = min_exposure
        if camera_id == 1:
            self.cameras.init1.set_exposure(exposure, save=False)
        else:
            self.cameras.init2.set_exposure(exposure, save=False)
        while exposure <= max_exposure:
            frame1, frame2 = self.cameras.get_frames()
            frame = frame1 if camera_id == 1 else frame2
            boxes, avg_conf = hex_detector.detect_avg_confidence(frame, param.MIN_CONFIDENCE_HEXAGON)
            score = self.calculate_calibration_score(4, boxes, avg_conf)
            if score > best_score:
                logger.debug(f"new best_score: {best_score}, score: {score}, boxes: {len(boxes)}, avg_conf: {avg_conf}, best_exposure: {best_exposure}, exposure: {exposure}")
                best_score = score
                best_exposure = exposure
            else:
                logger.debug(f"best_score: {best_score}, score: {score}, boxes: {len(boxes)}, avg_conf: {avg_conf}, best_exposure: {best_exposure}, exposure: {exposure}")

            _, _ = self.cameras.get_frames()
            cv2.waitKey(60)
            exposure = exposure + 1
            if camera_id == 1:
                self.cameras.init1.set_exposure(exposure, save=False)
            else:
                self.cameras.init2.set_exposure(exposure, save=False)

        _, _ = self.cameras.get_frames()
        cv2.waitKey(60)
        if camera_id == 1:
            self.cameras.init1.set_exposure(best_exposure, save=False)
            logger.debug(f"final best_score: {best_score}, score: {score}, boxes: {len(boxes)}, avg_conf: {avg_conf}, best_exposure: {best_exposure}, exposure: {self.cameras.init1.get_exposure()}")
        else:
            self.cameras.init2.set_exposure(best_exposure, save=False)
            logger.debug(f"final best_score: {best_score}, score: {score}, boxes: {len(boxes)}, avg_conf: {avg_conf}, best_exposure: {best_exposure}, exposure: {self.cameras.init2.get_exposure()}")

    def run(self):
        try:
            calibration_loaded = self.camera_setup()

            if not calibration_loaded:
                try: # automatic calibration
                    self.calibration_auto_exposure()
                    self.calibration()
                    self.calibration_debug()
                except RuntimeError:
                    while True:
                        try:
                            self.manual_calibration()
                            self.calibration_debug()
                            break
                        except RuntimeError:
                            pass

            self.led_panel.start()
            self.game()
        except Exception as e:
            logger.critical(f"Error: {e}\n{traceback.format_exc()}")


if __name__ == "__main__0":
    koc = KingOfControl()
    koc.camera_setup()
    # koc.calibration()
    # koc.calibration_debug()
    # koc.debug_hex_led_mapping()
    # koc.track_ball()
    while True:
        koc.game()
        start_time = time.time()
        while time.time() - start_time < 5:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                exit(0)

if __name__ == "__main__":
    logger.info("Application King of Control started (logging to file).")
    koc = KingOfControl()
    koc.run()
