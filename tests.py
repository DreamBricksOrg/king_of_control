import cv2
from ultralytics import YOLO

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

# Exemplo de uso:
if __name__ == "__main__":
    tests = Tests()
    tests.ball_recognition_test()
