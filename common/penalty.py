min_high_prio_penalty = 100
max_high_prio_penalty = 1000

min_low_prio_penalty = 10
max_low_prio_penalty = 200

low_prio_disk_penalty = 1
high_prio_disk_penalty = 40


def get_alpha():
    alpha = max_low_prio_penalty / max_high_prio_penalty
    return alpha


def get_penalty(response_time, priority) -> int:
    if priority == "h":
        if response_time == 0.0:
            return high_prio_disk_penalty
        if response_time < 0.1:
            return min_high_prio_penalty
        elif response_time >= 0.1:
            return max_high_prio_penalty

    elif priority == "l":
        if response_time == 0.0:
            return low_prio_disk_penalty
        if response_time < 0.1:
            return min_low_prio_penalty
        elif response_time >= 0.1:
            return max_low_prio_penalty
