import numpy as np


def penalty_by_priority():
    alpha = 3
    if 1 / alpha < np.random.uniform():
        return True
    else:
        return False


def get_alpha():
    return 1.5


def get_penalty(response_time, priority) -> int:
    if priority == "h":
        if response_time < 0.1:
            return 0
        elif response_time < 0.15:
            return 6
        elif response_time >= 0.15:
            return 9

    elif priority == "l":
        if response_time < 0.1:
            return 0
        elif response_time < 0.15:
            return 2
        elif response_time >= 0.15:
            return 3
