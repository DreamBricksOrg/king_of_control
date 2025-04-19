import cv2
import numpy as np


def stack_frames_vertically(frame1, frame2, final_width, final_height):

    if frame1 is None or frame2 is None:
        print("Could not retrieve frames from both cameras.")
        return None

    # Calculate individual target heights
    half_height = final_height // 2

    # Resize frames to target width and half height
    frame1_resized = cv2.resize(frame1, (final_width, half_height))
    frame2_resized = cv2.resize(frame2, (final_width, half_height))

    # Stack frames vertically
    composed = np.vstack((frame1_resized, frame2_resized))

    return composed


