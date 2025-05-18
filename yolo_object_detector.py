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
        self.last_results = self.model(frame)
        boxes = []

        for result in self.last_results:
            for box in result.boxes:
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

        self.last_results = self.model.track(frame)

        for result in self.last_results:
            for box in result.boxes:
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

        self.last_results = self.model.track(frame)

        for result in self.last_results:
            for box in result.boxes:
                conf = float(box.conf)
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                area = (x2 - x1) * (y2 - y1)
                if (conf > best_conf) or (conf == best_conf and area > best_area):
                    best_box = [x1, y1, x2, y2]
                    best_conf = conf
                    best_area = area

        return best_box

    def detect_best(self, frame, min_conf=0.0):
        self.last_results = self.model.predict(frame, conf=min_conf)
        best_box = None
        best_conf = -1
        best_area = -1

        for result in self.last_results:
            for box in result.boxes:
                if int(box.cls) == self.class_id:
                    conf = float(box.conf)
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    area = (x2 - x1) * (y2 - y1)
                    if (conf > best_conf) or (conf == best_conf and area > best_area):
                        best_box = [x1, y1, x2, y2]
                        best_conf = conf
                        best_area = area

        #if best_conf < min_conf:
        #    return None

        return best_box

    def detect_avg_confidence(self, frame: np.ndarray, min_conf=0.0):
        """
        Detect objects of the specified class_id in the given frame.

        :param frame: Image frame as a numpy array (e.g., from OpenCV).
        :param min_conf: Minimum confidence level to accept a detection as valid (0.0 to 1.0) .
        :return: List of bounding boxes [x1, y1, x2, y2] for detected objects.
        """
        self.last_results = self.model(frame, conf=min_conf)
        boxes = []

        sum_conf = 0
        for result in self.last_results:
            for box in result.boxes:
                if int(box.cls[0]) == self.class_id:
                    conf = float(box.conf)
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    sum_conf += conf
                    boxes.append([x1, y1, x2, y2])

        avg_conf = sum_conf / len(boxes) if len(boxes) > 0 else 0

        return boxes, avg_conf


if __name__ == "__main__":
    import parameters as param

    model = param.YOLO_MODEL_HEXAGON
    image_path = r"images\img_calibration_01.jpg"
    detector = YoloObjectDetector(class_id=0, model_path=model)
    frame = cv2.imread(image_path)
    best_box = detector.detect_best(frame, min_conf=0.5)
    #boxes = detector.detect(frame)

    if False:
        for box in boxes:
            print(box)
            x1, y1, x2, y2 = box
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

        if best_box is not None:
            print(best_box)
            x1, y1, x2, y2 = best_box
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 0), 2)
    else:
        frame = detector.last_results[0].plot()

    cv2.imshow("Detected", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
