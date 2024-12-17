import numpy as np
import skfmm
from numpy import around, array, ma

def fmm_path_planning(obstacle_map, start, end):
    """
    Plans a path from start to end using the Fast Marching Method.

    Parameters:
    - obstacle_map: 2D numpy array where 0 is free space and 1 is occupied.
    - start: tuple (x, y) representing the starting position.
    - end: tuple (x, y) representing the ending position.

    Returns:
    - path: List of tuples [(x1, y1), (x2, y2), ..., (xn, yn)] representing the path.
    """

    # Create a mask for obstacles
    traversible_ma = ma.masked_values(obstacle_map , 1) 
    traversible_ma[obstacle_map == 0] = 1
    traversible_ma[end] = 0

    # Compute the distance map using the signed distance function
    distance = skfmm.distance(traversible_ma, dx=1)
    print(np.max(distance))
    distance = ma.filled(distance, np.max(distance) + 1)
    
    # return distance

    # Path initialization
    path = [start]
    current_pos = start
    max_iterations = obstacle_map.size  # To prevent infinite loops
    iteration = 0

    while current_pos != end and iteration < max_iterations:
        x, y = current_pos
        # Compute the gradient at the current position
        grad_x, grad_y = np.gradient(distance)
        grad = np.array([grad_x[x, y], grad_y[x, y]])
        if np.linalg.norm(grad) == 0:
            print("Zero gradient encountered; cannot proceed further.")
            return None
        # Move in the direction opposite to the gradient
        grad = -grad / np.linalg.norm(grad)
        # Compute the next position
        next_x = x + grad[0]
        next_y = y + grad[1]
        # Round to the nearest integer coordinates
        next_y = int(round(next_y))
        next_x = int(round(next_x))
        # Ensure the next position is within bounds
        if (0 <= next_x < obstacle_map.shape[0]) and (0 <= next_y < obstacle_map.shape[1]):
            # Check if the next position is free
            if obstacle_map[next_x, next_y] == 1:
                next_pos = (next_x, next_y)
            else:
                # Try neighboring positions in order of increasing distance from the gradient direction
                neighbors = []
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0:
                            continue
                        ny, nx = y + dy, x + dx
                        if (0 <= ny < obstacle_map.shape[0]) and (0 <= nx < obstacle_map.shape[1]):
                            if obstacle_map[nx, ny] == 0:
                                distance_to_grad = np.hypot(grad[0] - dx, grad[1] - dy)
                                neighbors.append((distance_to_grad, (nx, ny)))
                if not neighbors:
                    print("No valid moves; path is blocked.")
                    return None
                # Select the neighbor closest to the gradient direction
                neighbors.sort()
                next_pos = neighbors[0][1]
        else:
            print("Next position is out of bounds.")
            return None

        if next_pos == current_pos:
            # No progress can be made
            print("Stuck at position", current_pos)
            return None
        current_pos = next_pos
        path.append(current_pos)
        iteration += 1

    if iteration >= max_iterations:
        print("Max iterations reached; no path found.")
        return None

    # Swap back the positions in the path to (x, y)
    path = [(p[0], p[1]) for p in path]
    return path