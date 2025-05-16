import cv2
import numpy as np


def draw_cross(frame, center, size=10, color=(0, 255, 0), thickness=2):
    """
    Draws a cross on the frame at the specified center point.

    Parameters:
        frame (np.ndarray): The image/frame to draw on.
        center (tuple): (x, y) coordinates of the cross center.
        size (int): Half-length of the cross arms.
        color (tuple): BGR color (default: green).
        thickness (int): Line thickness.
    """
    x, y = center
    # Draw horizontal line
    cv2.line(frame, (x - size, y), (x + size, y), color, thickness)
    # Draw vertical line
    cv2.line(frame, (x, y - size), (x, y + size), color, thickness)


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


def stack_frames_horizontally(frame1, frame2, final_width, final_height):

    if frame1 is None or frame2 is None:
        print("Could not retrieve frames from both cameras.")
        return None

    # Calculate individual target heights
    half_width = final_width // 2

    # Resize frames to target width and half height
    frame1_resized = cv2.resize(frame1, (half_width, final_height))
    frame2_resized = cv2.resize(frame2, (half_width, final_height))

    # Stack frames horizontally
    composed = np.hstack((frame1_resized, frame2_resized))

    return composed
