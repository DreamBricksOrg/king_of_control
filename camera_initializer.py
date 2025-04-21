import cv2


class CameraInitializer:
    def __init__(self, cam_id, width, height, result_dict):
        self.cam_id = cam_id
        self.width = width
        self.height = height
        self.result_dict = result_dict

    def initialize(self):
        print(f"Starting camera {self.cam_id}")
        cap = cv2.VideoCapture(self.cam_id)#, cv2.CAP_DSHOW)
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
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # 0.25 = manual, 0.75 = auto
        cap.set(cv2.CAP_PROP_EXPOSURE, -8)         # You can tune this
        cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)         # Turn off autofocus
        cap.set(cv2.CAP_PROP_FOCUS, 0)             # Set a fixed focus value

        # Warm up camera (optional but helps)
        for _ in range(5):
            cap.read()

        self.result_dict[self.cam_id] = cap


if __name__ == "__main__":
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
