from datetime import time

import cv2

import parameters


class CameraInitializer:
    def __init__(self, cam_id, width, height, result_dict):
        self.cam_id = cam_id
        self.width = width
        self.height = height
        self.result_dict = result_dict

    def initialize(self):
        print(f"Starting camera {self.cam_id}")
        cap = cv2.VideoCapture(self.cam_id, cv2.CAP_DSHOW) if parameters.USE_DSHOW else cv2.VideoCapture(self.cam_id)
        if not cap.isOpened():
            print(f"Error: Could not open camera {self.cam_id}")
            return

        # Get current resolution
        current_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        current_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Only set if different
        if (current_width != self.width) or (current_height != self.height):
            print(f"Setting resolution for camera {self.cam_id}")
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        print(f"Setting parameters for camera {self.cam_id}")
        # Optional: disable auto exposure and autofocus to prevent slow start

        print("FPS:", cap.get(cv2.CAP_PROP_FPS))
        print("Autoexposure:", cap.get(cv2.CAP_PROP_AUTO_EXPOSURE))
        print("Exposure:", cap.get(cv2.CAP_PROP_EXPOSURE))
        print("Autofocus:", cap.get(cv2.CAP_PROP_AUTOFOCUS))
        print("Focus:", cap.get(cv2.CAP_PROP_FOCUS))


        if False:
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # 0.25 = manual, 0.75 = auto
            cap.set(cv2.CAP_PROP_EXPOSURE, -9)         # You can tune this
            cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)         # Turn off autofocus
            cap.set(cv2.CAP_PROP_FOCUS, 0)             # Set a fixed focus value

        print("FPS:", cap.get(cv2.CAP_PROP_FPS))
        print("Autoexposure:", cap.get(cv2.CAP_PROP_AUTO_EXPOSURE))
        print("Exposure:", cap.get(cv2.CAP_PROP_EXPOSURE))
        print("Autofocus:", cap.get(cv2.CAP_PROP_AUTOFOCUS))
        print("Focus:", cap.get(cv2.CAP_PROP_FOCUS))

        # Warm up camera (optional but helps)
        for _ in range(5):
            cap.read()

        self.result_dict[self.cam_id] = cap


def test_start_with_threads():
    import threading

    # Launch threads to initialize both cameras
    camera_caps = {}
    threads = []

    for cam_id in [0, 1]:
        init = CameraInitializer(cam_id, 1280, 720, camera_caps)
        t = threading.Thread(target=init.initialize)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    # Now you can access camera_caps[0] and camera_caps[1]
    cam0 = camera_caps[0]
    cam1 = camera_caps[1]

    return cam0, cam1

def test_change_exposure():
    camera_caps = {}
    cam_id = parameters.CAMERA1_ID
    init = CameraInitializer(cam_id, 1280, 720, camera_caps)
    init.initialize()
    cap = camera_caps[cam_id]

    _, _ = cap.read()
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # 0.25 = manual, 0.75 = auto

    exposure = 0
    direction = 1
    while True:
        ret, frame = cap.read()

        cv2.imshow("Camera", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("a"):
            exposure -= direction
            print(exposure)
            cap.set(cv2.CAP_PROP_EXPOSURE, exposure)         # You can tune this
        elif key == ord("s"):
            exposure += direction
            print(exposure)
            cap.set(cv2.CAP_PROP_EXPOSURE, exposure)         # You can tune this
        elif key == ord('q'):
            break

if __name__ == "__main__":
    #test_start_with_threads()
    test_change_exposure()