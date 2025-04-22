import random


class HexNode:
    def __init__(self, col, row):
        self.col = col
        self.row = row
        self.links = []  # list of tuples: (neighbor_node, weight)

    def add_link(self, neighbor, weight=1):
        self.links.append((neighbor, weight))

    def __repr__(self):
        return f"HexNode(col={self.col}, row={self.row})"


class HexGraph:
    def __init__(self):
        self.nodes = {}  # key: (col, row), value: HexNode
        self.build_graph()

    def add_node(self, col, row):
        node = HexNode(col, row)
        self.nodes[(col, row)] = node
        return node

    def get_node(self, col, row):
        return self.nodes.get((col, row))

    def connect_nodes(self, col1, row1, col2, row2, weight=1, bidirectional=False):
        node1 = self.get_node(col1, row1)
        node2 = self.get_node(col2, row2)

        if not node1 or not node2:
            raise ValueError("One or both nodes not found")

        node1.add_link(node2, weight)
        if bidirectional:
            node2.add_link(node1, weight)

    def build_graph(self):
        # build nodes
        for row in range(8):
            num_cols = 3 if row % 2 == 1 else 2
            for col in range(num_cols):
                self.add_node(col, row)

        even = [
            [(1, 0, .2), (0, 1, .4), (1, 1, .4)],
            [(-1, 0, .2), (0, 1, .4), (1, 1, .4)]]
        odd = [
            [(1, 0, .2), (0, 1, .8)],
            [(-1, 0, .1), (1, 0, .1), (-1, 1, .4), (0, 1, .4)],
            [(-1, 0, .2), (-1, 1, .8)]]

        for row in range(8-1):
            num_cols = 3 if row % 2 == 1 else 2
            for col in range(num_cols):
                source_node = (col, row)
                links = odd if row % 2 == 1 else even
                for idx, link in enumerate(links[col]):
                    # don't go to the side on the first row
                    if row == 0 and idx == 0:
                        continue
                    delta_col, delta_row, weight = link
                    neighbor_node = (col + delta_col, row + delta_row)
                    self.connect_nodes(*source_node, *neighbor_node, weight)

    def create_random_path(self, start_node_col):
        node = self.get_node(start_node_col, 0)

        if not node:
            raise ValueError("start node not found")

        visited_nodes = [node]

        while len(node.links) > 0:
            node = self.choose_next_node(node, visited_nodes)
            visited_nodes.append(node)

        result = [(node.col, node.row) for node in visited_nodes]

        return result

    def create_random_path_target_size(self, start_node_col, target_size):
        size = 0
        path = None
        while size != target_size:
            path = self.create_random_path(start_node_col)
            size = len(path)

        return path

    @staticmethod
    def choose_next_node(current_node, visited_nodes):
        unvisited_links = [
            (neighbor, weight)
            for neighbor, weight in current_node.links
            if neighbor not in visited_nodes
        ]

        if not unvisited_links:
            return None

        neighbors, weights = zip(*unvisited_links)
        return random.choices(neighbors, weights=weights, k=1)[0]

    def __repr__(self):
        return f"HexGraph with {len(self.nodes)} nodes"


if __name__ == "__main__":
    graph = HexGraph()

    for _ in range(10):
        path = graph.create_random_path_target_size(random.randint(0, 1), 13)
        print(f"== {len(path):2d} ====")
        for hex in path:
            print(hex)
