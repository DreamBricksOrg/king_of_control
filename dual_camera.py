import cv2
from cv2_utils import stack_frames_vertically


class DualCamera:
    def __init__(self, cam1_id, cam2_id, res1=(640, 480), res2=(640, 480)):
        self.cam1 = cv2.VideoCapture(cam1_id)
        self.cam2 = cv2.VideoCapture(cam2_id)

        # Set resolution for camera 1
        self.cam1.set(cv2.CAP_PROP_FRAME_WIDTH, res1[0])
        self.cam1.set(cv2.CAP_PROP_FRAME_HEIGHT, res1[1])

        # Set resolution for camera 2
        self.cam2.set(cv2.CAP_PROP_FRAME_WIDTH, res2[0])
        self.cam2.set(cv2.CAP_PROP_FRAME_HEIGHT, res2[1])

        if not self.cam1.isOpened():
            raise ValueError(f"Camera with ID {cam1_id} could not be opened.")
        if not self.cam2.isOpened():
            raise ValueError(f"Camera with ID {cam2_id} could not be opened.")

    def get_frames(self):
        ret1, frame1 = self.cam1.read()
        ret2, frame2 = self.cam2.read()

        if not ret1 or not ret2:
            raise RuntimeError("Failed to read from one or both cameras.")

        return frame1, frame2

    def display(self, final_width, final_height):
        while True:
            frame1, frame2 = self.get_frames()
            composed_frame = stack_frames_vertically(frame1, frame2, final_width, final_height)
            if composed_frame is not None:
                cv2.imshow("Pressione espaco para continuar...", composed_frame)

            if cv2.waitKey(1) & 0xFF == ord(' '):
                break

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


if __name__ == "__main__":
    test_dual_camera()

if __name__ == "__main__1":
    dual_cam = DualCamera(0, 1, (1280, 720), (1280, 720))

    try:
        while True:
            frame0, frame1 = dual_cam.get_frames()
            cv2.imshow("Camera 1", frame0)
            cv2.imshow("Camera 2", frame1)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        dual_cam.release()
