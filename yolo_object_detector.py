from ultralytics import YOLO
import cv2
import numpy as np


class YoloObjectDetector:
    def __init__(self, class_id: int, model_path: str):
        """
        Initialize the detector with a class ID and YOLO model.

        :param class_id: The class ID to detect (e.g., 0 for person).
        :param model_path: Path to the YOLO model file.
        """
        self.class_id = class_id
        self.model = YOLO(model_path)
        self.last_results = None

    def get_last_results(self):
        return self.last_results

    def detect(self, frame: np.ndarray):
        """
        Detect objects of the specified class_id in the given frame.

        :param frame: Image frame as a numpy array (e.g., from OpenCV).
        :return: List of bounding boxes [x1, y1, x2, y2] for detected objects.
        """
        self.last_results = self.model(frame)[0]
        boxes = []

        for box in self.last_results.boxes:
            if int(box.cls[0]) == self.class_id:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                boxes.append([x1, y1, x2, y2])

        return boxes

    def track(self, frame: np.ndarray):
        """
        Detect objects of the specified class_id in the given frame.

        :param frame: Image frame as a numpy array (e.g., from OpenCV).
        :return: List of bounding boxes [x1, y1, x2, y2] for detected objects.
        """
        self.last_results = []

        yolo_result = self.model.track(frame)[0]

        for box in yolo_result.boxes:
            if int(box.cls[0]) == self.class_id:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                self.last_results.append([x1, y1, x2, y2])

        return self.last_results

    def track_best(self, frame: np.ndarray):
        """
        Detect objects of the specified class_id in the given frame.

        :param frame: Image frame as a numpy array (e.g., from OpenCV).
        :return: List of bounding boxes [x1, y1, x2, y2] for detected objects.
        """
        best_box = None
        best_conf = -1
        best_area = -1

        self.last_results = self.model.track(frame)[0]

        for box in self.last_results.boxes:
            conf = float(box.conf)
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            area = (x2 - x1) * (y2 - y1)
            if (conf > best_conf) or (conf == best_conf and area > best_area):
                best_box = [x1, y1, x2, y2]
                best_conf = conf
                best_area = area

        return best_box

    def detect_best(self, frame):
        self.last_results = self.model(frame)[0]
        best_box = None
        best_conf = -1
        best_area = -1

        for box in self.last_results.boxes:
            if int(box.cls) == self.class_id:
                conf = float(box.conf)
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                area = (x2 - x1) * (y2 - y1)
                if (conf > best_conf) or (conf == best_conf and area > best_area):
                    best_box = [x1, y1, x2, y2]
                    best_conf = conf
                    best_area = area

        return best_box


if __name__ == "__main__":
    import parameters as param

    model = param.YOLO_MODEL_HEXAGON
    image_path = r"G:\.shortcut-targets-by-id\1fkb-UGTUpl-Y0sfSv5SLxwTJoPIFEjRc\Projetos\EA\HnkControleBola\videos\WIN_20250418_15_22_51_Pro.jpg"
    detector = YoloObjectDetector(class_id=0, model_path=model)
    frame = cv2.imread(image_path)
    best_box = detector.detect_best(frame)
    boxes = detector.detect(frame)

    for box in boxes:
        print(box)
        x1, y1, x2, y2 = box
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

    if best_box is not None:
        print(best_box)
        x1, y1, x2, y2 = best_box
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 0), 2)

    cv2.imshow("Detected", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
