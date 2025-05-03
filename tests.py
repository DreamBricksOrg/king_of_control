import time
import cv2
from ultralytics import YOLO
from dual_camera import DualCamera
from cv2_utils import stack_frames_vertically
import parameters as param
from hexagons_board import HexagonsBoard

#YOLO_MODEL = r"static\models\yolo11m.pt"
#YOLO_MODEL = r"static\models\custom_ball.pt"
YOLO_MODEL = r"static\models\yolo11m_hexagon.pt"

class Tests:
    def __init__(self,
                 model_path='static/models/custom_ball.pt',
                 camera_index=0):
        self.model_path = model_path
        self.camera_index = camera_index

    def ball_recognition_test(self):
        model = YOLO(self.model_path)
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)

        if not cap.isOpened():
            print("Erro ao acessar a webcam.")
            return

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Falha ao capturar imagem da câmera.")
                    break

                results = model(frame)[0]

                for box in results.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = box.conf[0]
                    cls_id = int(box.cls[0])
                    label = model.names[cls_id]

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                cv2.imshow('Ball Recognition Test', frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Encerrando teste por comando do usuário (tecla 'q').")
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()


def test_yolo_dual_camera():

    # Load YOLOv8 or YOLOv11 model
    model = YOLO(YOLO_MODEL)  # You can replace with 'yolov11.pt' if you have it

    # Open the webcam (change 0 to a different index if needed)
    dual_cam = DualCamera(0, 1, (1280, 720), (1280, 720))

    while True:
        frame1, frame2 = dual_cam.get_frames()

        # Run detection
        results1 = model(frame1)
        results2 = model(frame2)

        # Draw detections using built-in plot() method
        annotated_frame1 = results1[0].plot()
        annotated_frame2 = results2[0].plot()

        composed_frame = stack_frames_vertically(annotated_frame1, annotated_frame2, 640, 720)
        cv2.imshow("Pressione espaco para continuar...", composed_frame)

        if cv2.waitKey(1) & 0xFF == ord(' '):
            cv2.destroyAllWindows()
            break

    # Clean up
    cv2.destroyAllWindows()

def change_hexagon_gen(sender, color):
    prev_col = 0
    prev_row = 0
    while True:
        for row in range(8):
            num_cols = 3 if row % 2 else 2
            for col in range(num_cols):
                sender.set_hexagon(prev_col, prev_row, (0,0,0))
                sender.set_hexagon(col, row, color)
                prev_col = col
                prev_row = row
                start = time.time()
                while time.time() - start < 0.3:
                    yield

def test_calibration():
    port = param.ARDUINO_COM_PORT
    sender = HexagonsBoard(port=port, baudrate=115200)  # Replace with your actual port, e.g., "/dev/ttyUSB0" on Linux
    color = (255, 0, 0)
    chg_hex = change_hexagon_gen(sender, color)

    print("Sending data...")

    # Load YOLOv8 or YOLOv11 model
    model = YOLO(param.YOLO_MODEL_HEXAGON)

    # Open the webcam (change 0 to a different index if needed)
    dual_cam = DualCamera(0, 1, (1280, 720), (1280, 720))

    while True:
        frame1, frame2 = dual_cam.get_frames()

        next(chg_hex)

        # Run detection
        results1 = model(frame1)
        results2 = model(frame2)

        # Draw detections using built-in plot() method
        annotated_frame1 = results1[0].plot()
        annotated_frame2 = results2[0].plot()

        composed_frame = stack_frames_vertically(annotated_frame1, annotated_frame2, 640, 720)
        cv2.imshow("Pressione espaco para continuar...", composed_frame)

        if cv2.waitKey(1) & 0xFF == ord(' '):
            cv2.destroyAllWindows()
            break

    # Clean up
    cv2.destroyAllWindows()


# Exemplo de uso:
if __name__ == "__main__":
    #tests = Tests()
    #tests.ball_recognition_test()

    #test_yolo_dual_camera()
    test_calibration()

