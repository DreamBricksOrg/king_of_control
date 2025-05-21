import cv2
import numpy as np
import logging
from typing import Tuple, List, Union

# Simple color palette (same as Ultralytics default)
_PALETTE = np.array(
    [
        (220,  20,  60),  (  0, 165, 255), (  0, 255, 255), (  0, 128,   0),
        (255, 128,   0),  (255,  51, 255), (  0,   0, 255), (255, 255,   0),
        (255,  99,  71),  (  0, 255,  51), (255,   0,   0), (  0,  51, 255)
    ],
    dtype=np.uint8,
)


logger = logging.getLogger(__name__)


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
    x, y = int(center[0]), int(center[1])

    # Draw horizontal line
    cv2.line(frame, (x - size, y), (x + size, y), color, thickness)
    # Draw vertical line
    cv2.line(frame, (x, y - size), (x, y + size), color, thickness)


def stack_frames_vertically(frame1, frame2, final_width, final_height):

    if frame1 is None or frame2 is None:
        logger.warning("Could not retrieve frames from both cameras.")
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
        logger.warning("Could not retrieve frames from both cameras.")
        return None

    # Calculate individual target heights
    half_width = final_width // 2

    # Resize frames to target width and half height
    frame1_resized = cv2.resize(frame1, (half_width, final_height))
    frame2_resized = cv2.resize(frame2, (half_width, final_height))

    # Stack frames horizontally
    composed = np.hstack((frame1_resized, frame2_resized))

    return composed


def get_color(class_id: int) -> Tuple[int, int, int]:
    """Return a distinct BGR color for a class id."""
    return tuple(int(c) for c in _PALETTE[class_id % len(_PALETTE)])


def draw_yolo_box(
    img: np.ndarray,
    box: Union[List[int], Tuple[int, int, int, int]],
    label: str = "",
    conf: float = None,
    class_id: int = 0,
    thickness: int = 2,
):
    """
    Draw a YOLO‑style bounding box with label and confidence on `img`.

    Args:
        img:        BGR image (modified in place).
        box:        (x1, y1, x2, y2) corner coordinates.
        label:      Class name to display.
        conf:       Confidence (0‑1) – optional.
        class_id:   Used only for color selection.
        thickness:  Rectangle thickness.
    """
    x1, y1, x2, y2 = map(int, box)
    color = get_color(class_id)

    # Draw rectangle
    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)

    # Compose label text
    if conf is not None:
        text = f"{label} {conf:.2f}" if label else f"{conf:.2f}"
    else:
        text = label

    if text:
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        txt_th = 1

        # Text size
        (tw, th), _ = cv2.getTextSize(text, font, font_scale, txt_th)
        th += 3  # a bit of padding

        # Label background (filled rectangle)
        cv2.rectangle(img, (x1, y1 - th), (x1 + tw, y1), color, -1)

        # Put text (white)
        cv2.putText(
            img,
            text,
            (x1, y1 - 2),
            font,
            font_scale,
            (255, 255, 255),
            txt_th,
            lineType=cv2.LINE_AA,
        )


def put_text_centered(img, text, center, font=cv2.FONT_HERSHEY_SIMPLEX,
                      font_scale=1.0, color=(0, 0, 0), thickness=2, line_type=cv2.LINE_AA):
    """
    Draws text centered at the given (x, y) coordinate on the image.

    Parameters:
        img: The image (NumPy array).
        text: Text string to draw.
        center: Tuple (x, y) specifying the center point.
        font: OpenCV font (default: FONT_HERSHEY_SIMPLEX).
        font_scale: Font scale factor.
        color: Text color (B, G, R).
        thickness: Thickness of the text strokes.
        line_type: Type of the line (default: cv2.LINE_AA).
    """
    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    x = int(center[0] - text_width / 2)
    y = int(center[1] + text_height / 2)
    cv2.putText(img, text, (x, y), font, font_scale, color, thickness, line_type)


if __name__ == "__main__":
    img = cv2.imread(r"images/img_calibration_01.jpg")  # your image here
    boxes = [
        ([50, 40, 200, 180], "cat", 0.92, 0),
        ([250, 60, 400, 200], "dog", 0.88, 1),
    ]

    for b, lbl, cf, cid in boxes:
        draw_yolo_box(img, b, label=lbl, conf=cf, class_id=cid)

    draw_cross(img, (70.5, 70))
    cv2.imshow("YOLO‑style boxes", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
