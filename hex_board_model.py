import parameters as param
import cv2
import numpy as np
import math
import logging
from svg_parse import parse_svg_to_polylines

logger = logging.getLogger(__name__)


class HexBoardModel:
    def __init__(self, svg_file, center_offset, cam_pos):
        self.pers_polygons = None
        self.floor_quad = None
        self.cam_pos = cam_pos
        unsorted_hexagons = self.load_hexagons(svg_file, center_offset)
        self.hexagons = self.sort_hexes(unsorted_hexagons, 5)
        self.hex_coordinates = self.create_hex_coordinates()

        ibw = 721/10
        ibh = 1868/10
        hibw = ibw / 2
        hibh = ibh / 2

        self.bounds = np.array([[[-hibw, -hibh],
                                 [ hibw, -hibh],
                                 [ hibw,  hibh],
                                 [-hibw,  hibh]]], dtype=np.float32)

    def get_polygon_under_ball(self, ball_bbox):
        #x1, y1, x2, y2 = ball_bbox
        #ball_pos = ((x1+x2) / 2, y2)
        #ball_pos = (x1, y2)
        ball_pos = self.ellipse_line_intersection(ball_bbox, self.cam_pos)

        idx, enabled_polygon = self.find_polygon_contains_point(self.pers_polygons, ball_pos)
        return idx, enabled_polygon, ball_pos

    def get_hex_under_ball(self, ball_bbox):
        idx, enabled_polygon, _ = self.get_polygon_under_ball(ball_bbox)
        if enabled_polygon is None:
            return None

        hex = self.hex_coordinates[idx]

        return hex

    def set_calibration_points(self, floor_quad):
        self.floor_quad = floor_quad
        self.pers_polygons = HexBoardModel.create_perspective_polygons(self.floor_quad, self.bounds, self.hexagons)
        for i in range(len(self.pers_polygons)):
            logger.debug(f"{i:02d} - {self.hex_coordinates[i]} - Pers:{len(self.pers_polygons[i])}:{self.pers_polygons[i]} - Hex:{len(self.hexagons[i])}:{self.hexagons[i]}")

    def draw_hexagons(self, frame, color=(255, 0, 0)):
        self.draw_perspective_polygons(frame, self.floor_quad, self.bounds, self.hexagons, color)

    @staticmethod
    def load_hexagons(svg_file, center_offset):
        result = parse_svg_to_polylines(svg_file, offset=center_offset)
        result = [HexBoardModel.remove_consecutive_duplicates(polygon) for polygon in result]
        return result

    @staticmethod
    def calculate_floor_quad(bboxes):
        result = []
        for bbox in bboxes:
            x1, y1, x2, y2 = bbox
            result.append(((x1+x2)/2, (y1+y2)/2))

        return result

    @staticmethod
    def draw_polylines(frame, points, color=(255, 0, 0), thickness=2):
        points = np.array([points], np.int32)
        cv2.polylines(frame, points, isClosed=True, color=color, thickness=thickness)

    @staticmethod
    def draw_polygons(frame, polygons, color=(255, 0, 0), thickness=2):
        for polygon in polygons:
            HexBoardModel.draw_polylines(frame, polygon, color, thickness)

    @staticmethod
    def remove_consecutive_duplicates(points):
        """
        Removes consecutive duplicate tuples from a list.

        Parameters:
            points (list): A list of tuples, e.g. [(x1, y1), (x2, y2), ...]

        Returns:
            list: A new list with consecutive duplicates removed.
        """
        if not points:
            return []

        cleaned = [points[0]]
        for point in points[1:]:
            if point != cleaned[-1]:
                cleaned.append(point)
        return cleaned

    @staticmethod
    def create_perspective_polygon(floor_quad, bounds, polygon):
        # format used in the transform
        np_polygon = np.array([polygon], dtype=np.float32)

        # Define where that box should map to in the image (the floor quad)
        np_floor_quad = np.array([floor_quad], dtype=np.float32)

        # Compute homography to warp flat polygon to the floor quad
        H = cv2.getPerspectiveTransform(bounds[0], np_floor_quad[0])

        # Apply the same transform to the polygon points
        np_poly_transformed = cv2.perspectiveTransform(np_polygon, H).astype(int)

        #print(np_poly_transformed)

        # transform into a list of points
        poly_transformed = [(point[0], point[1]) for point in np_poly_transformed[0]]
        # poly_transformed = remove_consecutive_duplicates(poly_transformed)
        #print(poly_transformed)

        return poly_transformed

    @staticmethod
    def create_perspective_polygons(floor_quad, bounds, polygons):
        result = []
        for polygon in polygons:
            result.append(HexBoardModel.create_perspective_polygon(floor_quad, bounds, polygon))

        return result

    @staticmethod
    def draw_perspective_polygon(frame, floor_quad, bounds, polygon, color=(255, 255, 0), thickness=2):
        # format used in the transform
        np_polygon = np.array([polygon], dtype=np.float32)

        # Define where that box should map to in the image (the floor quad)
        np_floor_quad = np.array([floor_quad], dtype=np.float32)

        # Compute homography to warp flat polygon to the floor quad
        H = cv2.getPerspectiveTransform(bounds[0], np_floor_quad[0])

        # Apply the same transform to the polygon points
        poly_transformed = cv2.perspectiveTransform(np_polygon, H).astype(int)

        # Draw hexagon on the frame
        cv2.polylines(frame, poly_transformed, isClosed=True, color=color, thickness=thickness)

    @staticmethod
    def draw_perspective_polygons(frame, floor_quad, bounds, polygons, color=(255, 255, 0), thickness=2):
        for polygon in polygons:
            HexBoardModel.draw_perspective_polygon(frame, floor_quad, bounds, polygon, color, thickness)

    @staticmethod
    def is_point_in_polygon(point, polygon):
        """
        Determines if a 2D point is inside a polygon using the ray casting algorithm.

        Parameters:
            point (tuple): (x, y) coordinates of the point to test.
            polygon (list): List of (x, y) tuples defining the polygon vertices.

        Returns:
            bool: True if the point is inside the polygon, False otherwise.
        """
        x, y = point
        inside = False

        n = len(polygon)
        px1, py1 = polygon[0]

        for i in range(n + 1):
            px2, py2 = polygon[i % n]

            if y > min(py1, py2):
                if y <= max(py1, py2):
                    if x <= max(px1, px2):
                        if py1 != py2:
                            xinters = (y - py1) * (px2 - px1) / (py2 - py1) + px1
                        if px1 == px2 or x <= xinters:
                            inside = not inside
            px1, py1 = px2, py2

        return inside

    @staticmethod
    def find_polygon_contains_point(polygons, point):
        for idx, polygon in enumerate(polygons):
            if HexBoardModel.is_point_in_polygon(point, polygon):
                return idx, polygon
        return -1, None

    @staticmethod
    def get_avg_point(hex):
        sum_points_x = 0
        sum_points_y = 0
        for point_idx in range(len(hex)-1):
            points = hex[point_idx]
            sum_points_x += points[0]
            sum_points_y += points[1]
        avg_point = (math.trunc(sum_points_x/len(hex)), math.floor(sum_points_y/len(hex)))
        return avg_point

    @staticmethod
    def sort_hexes(hexes, t):
        def sort_key(hex):
            x, y = HexBoardModel.get_avg_point(hex)
            return (y // t, -x)

        return sorted(hexes, key=sort_key)

    @staticmethod
    def create_hex_coordinates():
        result = []
        for row in range(8):
            num_cols = 3 if row % 2 == 1 else 2
            for col in range(num_cols):
                result.append((col, row))

        # add the goal
        result.append((0, 8))

        return result

    @staticmethod
    def ellipse_line_intersection(bbox, external_point):
        x_min, y_min, x_max, y_max = bbox
        px, py = external_point

        # Compute ellipse center and radii
        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) / 2
        rx = (x_max - x_min) / 2
        ry = (y_max - y_min) / 2

        # Direction vector from center to point
        dx = px - cx
        dy = py - cy

        if dx == 0 and dy == 0:
            raise ValueError("The external point cannot be the center of the ellipse.")

        # Normalize direction vector for intersection with ellipse
        scale = 1.0 / np.sqrt((dx ** 2) / rx ** 2 + (dy ** 2) / ry ** 2)

        # Intersection point
        ix = cx + dx * scale
        iy = cy + dy * scale

        return ix, iy


if __name__ == "__main__":
    import parameters as param
    hex_model = HexBoardModel(param.HEXAGONS_SVG_FILE, center_offset=param.HEXAGONS_SVG_OFFSET, cam_pos=(0, 0))

    hex_model

