from datetime import time
import json
import os

import cv2

import parameters


# Default camera parameters
DEFAULT_CAMERA_PARAMS = {
    "exposure": -5,
    "brightness": 128
}

class CameraInitializer:
    def __init__(self, cam_id, width, height, result_dict):
        self.cam_id = cam_id
        self.params_file = f"camera_params_{cam_id}.json"
        self.width = width
        self.height = height
        self.result_dict = result_dict
        self.camera_parameters = self.load_camera_params()
        self.cap = None

    def initialize(self):
        print(f"Starting camera {self.cam_id}")
        self.cap = cv2.VideoCapture(self.cam_id, cv2.CAP_DSHOW) if parameters.USE_DSHOW else cv2.VideoCapture(self.cam_id)
        if not self.cap.isOpened():
            print(f"Error: Could not open camera {self.cam_id}")
            return

        # Get current resolution
        current_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        current_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Only set if different
        if (current_width != self.width) or (current_height != self.height):
            print(f"Setting resolution for camera {self.cam_id}")
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        print(f"Setting parameters for camera {self.cam_id}")

        _, _ = self.cap.read() # changing the parameters only works if we read a frame before

        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # 0.25 = manual, 0.75 = auto
        self.cap.set(cv2.CAP_PROP_EXPOSURE, self.get_exposure())
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, self.get_brightness())
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)         # Turn off autofocus
        self.cap.set(cv2.CAP_PROP_FOCUS, 0)             # Set a fixed focus value

        print("FPS:", self.cap.get(cv2.CAP_PROP_FPS))
        print("Autoexposure:", self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE))
        print("Exposure:", self.cap.get(cv2.CAP_PROP_EXPOSURE))
        print("Brightness:", self.cap.get(cv2.CAP_PROP_BRIGHTNESS))
        print("Autofocus:", self.cap.get(cv2.CAP_PROP_AUTOFOCUS))
        print("Focus:", self.cap.get(cv2.CAP_PROP_FOCUS))

        # Warm up camera (optional but helps)
        for _ in range(5):
            self.cap.read()

        self.result_dict[self.cam_id] = self

    def get_exposure(self):
        return self.camera_parameters["exposure"]

    def get_brightness(self):
        return self.camera_parameters["brightness"]

    def set_exposure(self, exposure):
        self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure)
        self.camera_parameters["exposure"] = exposure
        self.save_camera_params(self.camera_parameters)

    def set_brightness(self, brightness):
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
        self.camera_parameters["brightness"] = brightness
        self.save_camera_params(self.camera_parameters)

    def load_camera_params(self):
        if not os.path.exists(self.params_file):
            # Create with defaults if file doesn't exist
            self.save_camera_params(DEFAULT_CAMERA_PARAMS)
            return DEFAULT_CAMERA_PARAMS.copy()

        with open(self.params_file, 'r') as f:
            return json.load(f)

    def save_camera_params(self, params):
        with open(self.params_file, 'w') as f:
            json.dump(params, f, indent=4)


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
    camera1 = CameraInitializer(cam_id, 1280, 720, camera_caps)
    camera1.initialize()
    cap = camera_caps[cam_id].cap

    exposure = camera1.get_exposure()
    direction = 1
    while True:
        ret, frame = cap.read()

        cv2.imshow("Camera", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("a"):
            exposure -= direction
            print(exposure)
            camera1.set_exposure(exposure)
        elif key == ord("s"):
            exposure += direction
            print(exposure)
            camera1.set_exposure(exposure)
        elif key == ord('q'):
            break

if __name__ == "__main__":
    #test_start_with_threads()
    test_change_exposure()