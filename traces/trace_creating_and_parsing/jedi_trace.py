# import random
#
# import numpy as np
#
# # trace_len_limit = 20000000
# object_priority = dict()
# high_priority_content_percentage = 0.5
# last_timestamp = 0.0
# # timestamp, object_id, object_size (Kb)
#
# with open('../../resources/raw_dataset/jedi_eu') as f:
#     with open('../../resources/dataset_jedi/eu.csv', 'w', encoding="utf-8",
#               newline='') as trace_file:
#         for line in f:
#             split = line.split(',')
#             split[2] = split[2][:-1]
#             try:
#                 timestamp, object_id, total_object_size = split
#                 if object_id not in object_priority.keys():
#                     object_priority[object_id] = "h" if random.random() < high_priority_content_percentage else "l"
#                 response_time = np.random.uniform(10, 200)
#                 interest_lifetime = 1000
#                 timestamp = int(timestamp)
#                 if last_timestamp >= timestamp:
#                     timestamp = last_timestamp + 0.5
#                 trace_file.write(
#                     "{},{},{},{},{},{},{}\n".format("d", timestamp, object_id, total_object_size,
#                                                     object_priority[object_id], interest_lifetime, response_time))
#                 last_timestamp = timestamp
#             except Exception as e:
#                 print(e)
#                 continue

import csv
import random
import numpy as np

object_priority = {}
object_response_time = {}
high_priority_content_percentage = 0.2
last_timestamp = 0.0
trace_len_limit = 100000
i = 0

with open('../../resources/raw_dataset/raw/jedi_w') as f, open(
        '../../resources/datasets/w_0.2.csv', 'w', encoding="utf-8", newline='') as trace_file:
    writer = csv.writer(trace_file)
    for line in f:
        split = line.strip().split(',')
        timestamp, object_id, total_object_size = map(int, split[:3])
        timestamp /= 1000
        if object_id not in object_response_time.keys():
            object_priority[object_id] = "h" if random.random() < high_priority_content_percentage else "l"
            object_response_time[object_id] = np.random.uniform(0.01, 0.2)
        interest_lifetime = 4
        if last_timestamp >= timestamp:
            timestamp = last_timestamp + np.random.uniform(0.01, 0.2)
        writer.writerow(["d", timestamp, object_id, total_object_size, object_priority[object_id], interest_lifetime,
                         object_response_time[object_id]])
        i += 1
        if i == trace_len_limit:
            break
        last_timestamp = timestamp
