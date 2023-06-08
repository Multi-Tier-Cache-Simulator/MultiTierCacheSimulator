min_high_prio_penalty = 0
mid_high_prio_penalty = 50
max_high_prio_penalty = 75

min_low_prio_penalty = 0
mid_low_prio_penalty = 10
max_low_prio_penalty = 15

low_prio_disk_penalty = 0
high_prio_disk_penalty = 5


def get_alpha():
    alpha = max_low_prio_penalty / max_high_prio_penalty
    # alpha = 0.5
    return alpha


def get_penalty(response_time, priority) -> int:
    if priority == "h":
        if response_time == 0.0:
            return high_prio_disk_penalty
        if response_time < 0.02:
            return min_high_prio_penalty
        if response_time < 0.15:
            return mid_high_prio_penalty
        elif response_time >= 0.15:
            return max_high_prio_penalty

    elif priority == "l":
        if response_time == 0.0:
            return low_prio_disk_penalty
        if response_time < 0.02:
            return min_low_prio_penalty
        if response_time < 0.15:
            return mid_low_prio_penalty
        elif response_time >= 0.15:
            return max_low_prio_penalty
