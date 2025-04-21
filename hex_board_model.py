import parameters as param
import cv2
import numpy as np
import math
from svg_parse import parse_svg_to_polylines


class HexBoardModel:
    def __init__(self, svg_file, center_offset):
        self.pers_polygons = None
        self.floor_quad = None
        self.hexagons = self.load_hexagons(svg_file, center_offset)

        ibw = 721/10
        ibh = 1868/10
        hibw = ibw / 2
        hibh = ibh / 2

        self.bounds = np.array([[[-hibw, -hibh],
                                 [ hibw, -hibh],
                                 [ hibw,  hibh],
                                 [-hibw,  hibh]]], dtype=np.float32)

    def set_calibration_points(self, floor_quad):
        self.floor_quad = floor_quad
        self.pers_polygons = HexBoardModel.create_perspective_polygons(self.floor_quad, self.bounds, self.hexagons)

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

        print(np_poly_transformed)

        # transform into a list of points
        poly_transformed = [(point[0], point[1]) for point in np_poly_transformed[0]]
        # poly_transformed = remove_consecutive_duplicates(poly_transformed)
        print(poly_transformed)

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
        for polygon in polygons:
            if HexBoardModel.is_point_in_polygon(point, polygon):
                return polygon
        return None

