import cv2
from cv2_utils import stack_frames_vertically, stack_frames_horizontally
import threading
from camera_initializer import CameraInitializer
import parameters as param
import logging

logger = logging.getLogger(__name__)


class DualCamera:
    def __init__(self, cam1_id, cam2_id, res1=(640, 480), res2=(640, 480)):
        #print(f"start camera {cam1_id}")
        #self.cam1 = self.initialize_camera(cam1_id, *res1)
        #print(f"start camera {cam2_id}")
        #self.cam2 = self.initialize_camera(cam2_id, *res2)

        camera_caps = self.initialize_cameras(cam1_id, cam2_id)
        # Now you can access camera_caps[0] and camera_caps[1]
        self.init1 = camera_caps[cam1_id]
        self.init2 = camera_caps[cam2_id]
        self.cam1 = self.init1.cap
        self.cam2 = self.init2.cap

    def set_exposure1(self, exposure):
        self.init1.set_exposure(exposure)

    def set_exposure2(self, exposure):
        self.init2.set_exposure(exposure)

    @staticmethod
    def initialize_cameras(cam1_id, cam2_id):
        # Launch threads to initialize both cameras
        camera_caps = {}
        threads = []

        for cam_id in [cam1_id, cam2_id]:
            init = CameraInitializer(cam_id, 1280, 720, camera_caps)
            t = threading.Thread(target=init.initialize)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        return camera_caps

    @staticmethod
    def initialize_camera(cam_id, desired_width, desired_height):
        cap = cv2.VideoCapture(cam_id)
        if not cap.isOpened():
            raise RuntimeError(f"Camera {cam_id} could not be opened.")

        current_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        current_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if current_width != desired_width or current_height != desired_height:
            logger.debug(f"set resolution for camera {cam_id}")
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, desired_width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, desired_height)

        return cap

    def get_frames(self):
        ret1, frame1 = self.cam1.read()
        ret2, frame2 = self.cam2.read()

        if not ret1 or not ret2:
            raise RuntimeError("Failed to read from one or both cameras.")

        return frame1, frame2

    def display(self, final_width, final_height, vertical=True):
        window_title = "Pressione espaco para continuar..."
        while True:
            frame1, frame2 = self.get_frames()
            composed_frame = stack_frames_vertically(frame1, frame2, final_width, final_height) if vertical \
                else stack_frames_horizontally(frame1, frame2, final_width, final_height)

            if composed_frame is not None:
                cv2.imshow(window_title, composed_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):
                cv2.destroyWindow(window_title)
                break
            elif key == ord('r'):
                    cv2.destroyWindow(window_title)
                    break
            elif key == ord('a'):
                self.init1.set_exposure(self.init1.get_exposure()-1)
            elif key == ord('s'):
                self.init1.set_exposure(self.init1.get_exposure()+1)
            elif key == ord('z'):
                self.init2.set_exposure(self.init2.get_exposure()-1)
            elif key == ord('x'):
                self.init2.set_exposure(self.init2.get_exposure()+1)

        return self.init1.get_exposure(), self.init2.get_exposure(), key

    def release(self):
        if self.cam1.isOpened():
            self.cam1.release()
        if self.cam2.isOpened():
            self.cam2.release()
        cv2.destroyAllWindows()


def test_dual_camera():

    # Initialize the camera (camera IDs and desired resolution per camera)
    cam = DualCamera(cam1_id=0, cam2_id=1, res1=(1280, 720), res2=(1280, 720))

    final_width = 640
    final_height = 720
    cam.display(final_width, final_height)

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__1":
    test_dual_camera()

if __name__ == "__main__":
    dual_cam = DualCamera(param.CAMERA1_ID, param.CAMERA2_ID, (1280, 720), (1280, 720))

    try:
        while True:
            frame0, frame1 = dual_cam.get_frames()
            cv2.imshow("Camera 1", frame0)
            cv2.imshow("Camera 2", frame1)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        dual_cam.release()
