import random

# Estrutura da matriz
matrix = {
    7: [0, 1, 2],
    6: [0, 1],
    5: [0, 1, 2],
    4: [0, 1],
    3: [0, 1, 2],
    2: [0, 1],
    1: [0, 1, 2],
    0: [0, 1],
}

def is_invalid_transition(current_y, current_x, next_y, next_x):
    current_row_len = len(matrix[current_y])
    next_row_len = len(matrix[next_y])

    # Regras de salto entre linhas
    if current_row_len == 2 and next_row_len == 3:
        if current_x == 0 and next_x in [1, 2]:
            return True
        if current_x == 1 and next_x in [0, 1]:
            return True

    if current_row_len == 3 and next_row_len == 2:
        if current_x == 0 and next_x == 1:
            return True
        if current_x == 2 and next_x == 0:
            return True
        if current_x == 1:
            return True

    return False

def get_next_positions(y, x, visited, linha_usada):
    if y + 1 not in matrix:
        return []

    next_level = matrix[y + 1]
    current_level = matrix[y]

    positions = []
    probs = []

    # Próximas posições candidatas
    if len(next_level) == 2:
        candidates = [(y + 1, next_level[0]), (y + 1, next_level[1])]
        weights = [0.45, 0.45]
    elif len(next_level) == 3:
        candidates = [(y + 1, next_level[0]), (y + 1, next_level[1]), (y + 1, next_level[2])]
        weights = [0.3, 0.3, 0.3]

    for pos, weight in zip(candidates, weights):
        ny, nx = pos
        if is_invalid_transition(y, x, ny, nx):
            continue
        if pos in visited:
            continue
        if len(matrix[ny]) == 3:
            if linha_usada.get(ny, set()) and len(linha_usada[ny]) >= 2 and nx not in linha_usada[ny]:
                continue  # bloqueia terceira casa
        positions.append(pos)
        probs.append(weight)

    # Movimento lateral
    if y != 0:
        if len(current_level) == 2:
            lateral = 1 - x
            lateral_pos = (y, lateral)
            if lateral_pos not in visited:
                positions.append(lateral_pos)
                probs.append(0.1)
        elif len(current_level) == 3:
            lateral = (y, 1 if x in [0, 2] else random.choice([0, 2]))
            if lateral not in visited:
                positions.append(lateral)
                probs.append(0.1)

    if not positions:
        return []

    total = sum(probs)
    probs = [p / total for p in probs]

    return random.choices(positions, weights=probs, k=1)

def generate_path():
    path_matrix = {y: {x: 'x' for x in xs} for y, xs in matrix.items()}
    start = random.choice([(0, 0), (0, 1)])
    current = start
    visited = {current}
    path_sequence = [current]
    path_matrix[current[0]][current[1]] = 'I'
    linha_usada = {current[0]: {current[1]}} if len(matrix[current[0]]) == 3 else {}

    while current[0] < max(matrix.keys()):
        next_candidates = get_next_positions(*current, visited, linha_usada)
        if not next_candidates:
            return None, None, None
        next_pos = next_candidates[0]
        current = next_pos
        if current in visited:
            return None, None, None
        path_sequence.append(current)
        visited.add(current)
        y, x = current
        if len(matrix[y]) == 3:
            if y not in linha_usada:
                linha_usada[y] = set()
            linha_usada[y].add(x)
        path_matrix[y][x] = 'B'

    return path_matrix, path_sequence, visited

# Tenta até conseguir
while True:
    path_matrix, path_sequence, visited_positions = generate_path()
    if path_matrix is not None:
        break

# Exibe resultados
print("Sequência do caminho percorrido:")
print(path_sequence)

print("\nMatriz com caminho marcado:\n")
for y in sorted(matrix.keys(), reverse=True):
    row = ";".join(f"{path_matrix[y][x]}:{y},{x}" for x in matrix[y])
    print(row)
