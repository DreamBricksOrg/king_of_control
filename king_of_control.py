import parameters as param
from hexagons_board import HexagonsBoard
from hex_board_model import HexBoardModel
from yolo_object_detector import YoloObjectDetector
from dual_camera import DualCamera
import time

class KingOfControl:
    def __init__(self):
        self.cameras = DualCamera(cam1_id=param.CAMERA1_ID, cam2_id=param.CAMERA2_ID,
                                  res1=param.CAMERA_RESOLUTION, res2=param.CAMERA_RESOLUTION)
        self.board = HexagonsBoard(port=param.ARDUINO_COM_PORT, baudrate=param.ARDUINO_BAUD_RATE)
        self.hex_model_cam1 = HexBoardModel(param.HEXAGONS_SVG_FILE, center_offset=param.HEXAGONS_SVG_OFFSET)
        self.hex_model_cam2 = HexBoardModel(param.HEXAGONS_SVG_FILE, center_offset=param.HEXAGONS_SVG_OFFSET)

    def camera_setup(self):
        final_width = 640
        final_height = 720
        self.cameras.display(final_width, final_height)

    def calibration(self):
        yolo_object_detector = YoloObjectDetector(class_id=0, model_path=param.YOLO_MODEL_HEXAGON)
        self.get_calibration_points(yolo_object_detector)

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
            self.board.set_hexagon(*coord, red)
            time.sleep(0.2)
            frame1, frame2 = self.cameras.get_frames()

            # find it in both cameras
            result1 = yolo_object_detector.detect(frame1)
            result2 = yolo_object_detector.detect(frame2)

            try:
                bbox1 = self.find_best_bbox(result1)
                bboxes1.append(bbox1)
            except:
                num_exceptions1 += 1

            if num_exceptions2 > 5:
                print("Erro na calibracao da camera 1")
                exit(1)

            try:
                bbox2 = self.find_best_bbox(result2)
                bboxes2.append(bbox2)
            except:
                num_exceptions2 += 1

            if num_exceptions2 > 5:
                print("Erro na calibracao da camera 2")
                exit(1)

            coord_idx += 1
            num_exceptions1 = 0
            num_exceptions2 = 0

        def find_best_bbox():
            pass

