import cv2
import parameters as param
from hexagons_board import HexagonsBoard
from hex_board_model import HexBoardModel
from yolo_object_detector import YoloObjectDetector
from dual_camera import DualCamera
import time
from cv2_utils import stack_frames_vertically


class KingOfControl:
    def __init__(self):
        print("Init cameras")
        self.cameras = DualCamera(cam1_id=param.CAMERA1_ID, cam2_id=param.CAMERA2_ID,
                                  res1=param.CAMERA_RESOLUTION, res2=param.CAMERA_RESOLUTION)
        print("Init Arduino")
        self.board = HexagonsBoard(port=param.ARDUINO_COM_PORT, baudrate=param.ARDUINO_BAUD_RATE)
        print("Init Board Model")
        self.hex_model_cam1 = HexBoardModel(param.HEXAGONS_SVG_FILE, center_offset=param.HEXAGONS_SVG_OFFSET)
        self.hex_model_cam2 = HexBoardModel(param.HEXAGONS_SVG_FILE, center_offset=param.HEXAGONS_SVG_OFFSET)

    def camera_setup(self):
        final_width = 640
        final_height = 720
        self.cameras.display(final_width, final_height)
        cv2.destroyAllWindows()

    def calibration(self):
        yolo_object_detector = YoloObjectDetector(class_id=0, model_path=param.YOLO_MODEL_HEXAGON)
        floor_quad1, floor_quad2 = self.get_calibration_points(yolo_object_detector)

        self.hex_model_cam1.set_calibration_points(floor_quad1)
        self.hex_model_cam2.set_calibration_points(floor_quad2)

        # debug output
        frame1, frame2 = self.cameras.get_frames()
        self.hex_model_cam1.draw_hexagons(frame1, color=(80, 80, 80))
        self.hex_model_cam2.draw_hexagons(frame2, color=(80, 80, 80))
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


if __name__ == "__main__":
    koc = KingOfControl();
    koc.camera_setup()
    koc.calibration()