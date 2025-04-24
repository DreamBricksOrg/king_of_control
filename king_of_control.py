import cv2
import parameters as param
from hexagons_board import HexagonsBoard
from hex_board_model import HexBoardModel
from yolo_object_detector import YoloObjectDetector
from dual_camera import DualCamera
import time
from cv2_utils import stack_frames_vertically, draw_cross
from hex_graph import HexGraph
from led_panel import LedPanel

class KingOfControl:
    def __init__(self):
        print("Init Arduino")
        self.board = HexagonsBoard(port=param.ARDUINO_COM_PORT, baudrate=param.ARDUINO_BAUD_RATE)

        print("Init cameras")
        self.cameras = DualCamera(cam1_id=param.CAMERA1_ID, cam2_id=param.CAMERA2_ID,
                                  res1=param.CAMERA_RESOLUTION, res2=param.CAMERA_RESOLUTION)
        print("Init Board Model")
        self.hex_model_cam1 = HexBoardModel(param.HEXAGONS_SVG_FILE, center_offset=param.HEXAGONS_SVG_OFFSET, cam_pos=(0, param.CAMERA_RESOLUTION[1]))
        self.hex_model_cam2 = HexBoardModel(param.HEXAGONS_SVG_FILE, center_offset=param.HEXAGONS_SVG_OFFSET, cam_pos=param.CAMERA_RESOLUTION)
        self.graph = HexGraph()
        self.led_panel = LedPanel(state_play_duration=param.MAX_TIME)

    def camera_setup(self):
        final_width = 640
        final_height = 720
        self.cameras.display(final_width, final_height)
        cv2.destroyAllWindows()

    def calibration(self):
        self.led_panel.set_state('BLANK')
        hex_detector = YoloObjectDetector(class_id=0, model_path=param.YOLO_MODEL_HEXAGON)
        floor_quad1, floor_quad2 = self.get_calibration_points(hex_detector)

        self.hex_model_cam1.set_calibration_points(floor_quad1)
        self.hex_model_cam2.set_calibration_points(floor_quad2)

    def game(self):
        white = (255, 255, 255)
        red = (255, 0, 0)
        green = (0, 255, 0)
        ball_detector = YoloObjectDetector(class_id=32, model_path=param.YOLO_MODEL_BALL)

        paths = [self.graph.create_random_path_target_size(0, param.TARGET_PATH_SIZE),
                 self.graph.create_random_path_target_size(1, param.TARGET_PATH_SIZE)]
        chosen_path = 0

        # waits for the player to put the ball on one of the first hexagons
        brightness = 0
        direction = 10
        self.board.clear()
        self.led_panel.set_state('CTA')
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
        self.led_panel.set_state('PLAY')
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
                print(f"Score: {self.calculate_score(len(correct), len(wrong), 0.0)}")

            if hex and hex not in path and hex not in wrong:
                self.board.set_hexagon(*hex, red)
                wrong.add(hex)
                print(f"Score: {self.calculate_score(len(correct), len(wrong), 0.0)}")

            composed_frame = stack_frames_vertically(frame1, frame2, 640, 720)
            cv2.imshow("game", composed_frame)

            #if hex and hex[1] == 7:
            #    break

        playing_time = min(time.time() - start_time, param.MAX_TIME)
        time_left = param.MAX_TIME - playing_time
        score = self.calculate_score(len(correct), len(wrong), time_left)
        print(f"Score: {score}")
        self.led_panel.set_score_value(int(score))
        self.led_panel.set_state('SCORE')

    @staticmethod
    def calculate_score(num_correct, num_wrong, time_left):
        return time_left * param.TIME_SCORE + \
            num_correct * param.HEX_CORRECT_SCORE + \
            num_wrong * param.HEX_WRONG_SCORE

    def get_hex_under_ball(self, ball_detector, update_frames=True):
        frame1, frame2 = self.cameras.get_frames()

        bbox1 = ball_detector.detect_best(frame1)

        hex = None
        if bbox1 is not None:
            idx, enabled_polygon = self.hex_model_cam1.get_polygon_under_ball(bbox1)
            if enabled_polygon:
                hex = self.hex_model_cam1.hex_coordinates[idx]
                hexagon = self.hex_model_cam1.pers_polygons[idx]

                if update_frames:
                    label = "Ball"
                    x1, y1, x2, y2 = bbox1
                    cv2.rectangle(frame1, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
                    cv2.putText(frame1, label, (int(x1), int(y1) - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                    self.hex_model_cam1.draw_hexagons(frame1, color=(100, 100, 100))
                    self.hex_model_cam1.draw_polylines(frame1, hexagon, color=(0, 255, 255))
                    # hex = self.hex_model_cam1.get_hex_under_ball(bbox1)
        else:
            bbox2 = ball_detector.detect_best(frame2)
            if bbox2 is not None:
                idx, enabled_polygon = self.hex_model_cam2.get_polygon_under_ball(bbox2)
                if enabled_polygon:
                    hex = self.hex_model_cam2.hex_coordinates[idx]
                    hexagon = self.hex_model_cam2.pers_polygons[idx]

                    if update_frames:
                        label = "Ball"
                        x1, y1, x2, y2 = bbox2
                        cv2.rectangle(frame2, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
                        cv2.putText(frame2, label, (int(x1), int(y1) - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                        self.hex_model_cam2.draw_hexagons(frame2, color=(100, 100, 100))
                        self.hex_model_cam2.draw_polylines(frame2, hexagon, color=(0, 255, 255))
                        # hex = self.hex_model_cam2.get_hex_under_ball(bbox2)

        return hex, frame1, frame2

    def track_ball(self):
        ball_detector = YoloObjectDetector(class_id=32, model_path=param.YOLO_MODEL_BALL)
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
            cv2.imshow("Pressione espaco para continuar...", composed_frame)

            if cv2.waitKey(1) & 0xFF == ord(' '):
                cv2.destroyAllWindows()
                break

    def calibration_debug(self):
        magenta = (255, 0, 255)

        frame1, frame2 = self.cameras.get_frames()
        self.hex_model_cam1.draw_hexagons(frame1, color=magenta)
        self.hex_model_cam2.draw_hexagons(frame2, color=magenta)
        composed_frame = stack_frames_vertically(frame1, frame2, 640, 720)

        if composed_frame is not None:
            cv2.imshow("Pressione espaco para continuar...", composed_frame)

        while True:
            if cv2.waitKey(1) & 0xFF == ord(' '):
                cv2.destroyAllWindows()
                break

    def get_calibration_points(self, yolo_object_detector):
        hex_cal_coord = [(2, 1), (0, 1), (0, 7), (2, 7)]
        red = (255, 0, 0)
        bboxes1 = []
        bboxes2 = []

        coord_idx = 0
        num_exceptions1 = 0
        num_exceptions2 = 0
        while coord_idx < len(hex_cal_coord):
            coord = hex_cal_coord[coord_idx]

            # light up one hexagon
            self.board.clear()
            self.board.set_hexagon(*coord, red)
            time.sleep(0.2)
            frame1, frame2 = self.cameras.get_frames()

            # find it in both cameras
            bbox1 = yolo_object_detector.detect_best(frame1)
            if bbox1 is None:
                num_exceptions1 += 1
                if num_exceptions1 > 5:
                    self.show_frame(frame1)
                    raise RuntimeError(f"Erro na calibracao da camera 1")
                time.sleep(0.3)
                continue

            bbox2 = yolo_object_detector.detect_best(frame2)
            if bbox2 is None:
                num_exceptions2 += 1
                if num_exceptions2 > 5:
                    self.show_frame(frame2)
                    raise RuntimeError(f"Erro na calibracao da camera 2")
                time.sleep(0.3)
                continue

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
    def show_frame(frame, title="Pressione espaco para continuar..."):
        while True:
            cv2.imshow(title, frame)
            if cv2.waitKey(1) & 0xFF == ord(' '):
                cv2.destroyAllWindows()
                break

    def debug_hex_led_mapping(self):
        hex_id = 0
        num_hexes = len(self.hex_model_cam1.hexagons)
        while True:
            frame1, frame2 = self.cameras.get_frames()

            hexagon = self.hex_model_cam1.hexagons[hex_id]
            pers_hex = self.hex_model_cam1.pers_polygons[hex_id]
            hex_coord = self.hex_model_cam1.hex_coordinates[(hex_id+1) % num_hexes]

            self.hex_model_cam1.draw_hexagons(frame1, color=(100, 100, 100))
            self.hex_model_cam1.draw_polylines(frame1, pers_hex, color=(0, 255, 255))

            composed_frame = frame1 #stack_frames_vertically(frame1, frame2, 640, 720)
            cv2.imshow("Pressione espaco para continuar...", composed_frame)

            print(f"hexagon: {len(hexagon)}-{self.hex_model_cam1.get_avg_point(hexagon)}-{hexagon}")
            print(f"pers_hex: {len(pers_hex)}-{self.hex_model_cam1.get_avg_point(pers_hex)}-{pers_hex}")
            print(f"hex_coord: {hex_coord}")
            self.board.set_hexagon(*hex_coord, (255, 255, 0))
            time.sleep(2)
            self.board.set_hexagon(*hex_coord, (0, 0, 0))
            hex_id = (hex_id + 1) % num_hexes

            if cv2.waitKey(1) & 0xFF == ord(' '):
                cv2.destroyAllWindows()
                break


if __name__ == "__main__":
    koc = KingOfControl();
    koc.camera_setup()
    koc.calibration()
    #koc.calibration_debug()
    #koc.debug_hex_led_mapping()
    #koc.track_ball()
    while True:
        koc.game()
        start_time = time.time()
        while time.time() - start_time < 5:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                exit(0)

