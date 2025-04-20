from xml.etree import ElementTree as ET
from svg.path import parse_path
import numpy as np


def parse_svg_to_polylines(svg_file, offset=(0.0, 0.0), sample_interval=100000.0):
    """ Parses an SVG file and returns a list of polylines (each a list of (x, y) points).
        Curves are approximated using sampling. """

    tree = ET.parse(svg_file)
    root = tree.getroot()
    ns = {'svg': 'http://www.w3.org/2000/svg'}

    width = float(root.attrib.get('width', '1').replace('cm', ''))
    height = float(root.attrib.get('height', '1').replace('cm', ''))

    polylines = []
    for path_elem in root.findall('.//{http://www.w3.org/2000/svg}path'):

        d = path_elem.attrib.get('d', '')
        transform = path_elem.attrib.get('transform', '')
        if not d:
            continue

        path = parse_path(d)

        # Sample the path into discrete points
        points = []
        for seg in path:
            seg_len = seg.length()
            num_samples = max(int(seg_len / sample_interval), 1)
            for i in range(num_samples + 1):
                pt = seg.point(i / num_samples)
                points.append((pt.real+offset[0], pt.imag+offset[1]))

        # Apply transformation if present (basic support for "matrix(a,b,c,d,e,f)")
        if transform.startswith("matrix"):
            values = transform[7:-1].split(',')
            if len(values) == 6:
                a, b, c, d, e, f = map(float, values)
                matrix = np.array([[a, c, e],
                                   [b, d, f],
                                   [0, 0, 1]])
                transformed_points = []
                for x, y in points:
                    p = np.array([x, y, 1])
                    p_trans = matrix @ p
                    transformed_points.append((p_trans[0], p_trans[1]))
                points = transformed_points

        polylines.append(points)

    return polylines
