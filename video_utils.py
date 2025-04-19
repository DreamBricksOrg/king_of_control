from pygrabber.dshow_graph import FilterGraph


def get_available_cameras():
    result = {}
    graph = FilterGraph()
    cameras = graph.get_input_devices()
    for i, cam in enumerate(cameras):
        print(f"Camera {i}: {cam}")
        result[i] = cam

    return result


if __name__ == "__main__":
    _ = get_available_cameras()

