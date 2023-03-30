# CloudVPS http://visa.lab.asu.edu/web/resources/traces/
import random

import numpy as np

trace_len_limit = 20000000
object_priority = dict()
high_priority_content_percentage = 0.5
last_timestamp = 0.0
# timestamp, object_id, object_size (Kb)

with open('../../resources/raw_dataset/jedi_eu') as f:
    with open('../../resources/raw_dataset/w.csv', 'w', encoding="utf-8",
              newline='') as trace_file:
        for line in f:
            split = line.split(',')
            split[2] = split[2][:-1]
            try:
                timestamp, object_id, total_object_size = split
                if object_id not in object_priority.keys():
                    object_priority[object_id] = "h" if random.random() < high_priority_content_percentage else "l"
                response_time = np.random.uniform(10, 200)
                interest_lifetime = 1000
                timestamp = int(timestamp)
                if last_timestamp >= timestamp:
                    timestamp = last_timestamp + 0.5
                trace_file.write(
                    "{},{},{},{},{},{},{}\n".format("d", timestamp, object_id, total_object_size,
                                                    object_priority[object_id], interest_lifetime, response_time))
                last_timestamp = timestamp
                print(last_timestamp)
            except Exception:
                continue
