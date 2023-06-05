import random

import numpy as np

# IBM trace column names = ("timestamp", "request type", "object id", "object size", "start offset", "end offset")
# timestamps in milliseconds
# request type GET (used) PUT HEAD DELETE (won't be used)
# NDN trace column names = ("data_back", "timestamp", "name", "size", "priority", "InterestLifetime", "responseTime")
# http://iotta.snia.org/traces/block-io/388

trace_len_limit = 100000
object_priority = dict()
object_response_time = dict()
high_priority_content_percentage = 0.2
i = 0

with open('../../resources/raw_dataset/raw/IBMObjectStoreTrace001Part0') as f:
    with open('../../resources/datasets/IBMObjectStoreTrace001Part0-2.0.csv', 'w', encoding="utf-8",
              newline='') as trace_file:
        for line in f:

            # print("line : %s" % line)
            split = line.split(' ')
            # print("split: %s" % split)
            try:
                timestamp, request_type, object_id, total_object_size, start_offset, end_offset = (split + [0, 0, 0])[
                                                                                                  :6]
                timestamp = int(timestamp)
                timestamp /= 100000
                if object_id not in object_priority.keys():
                    object_priority[object_id] = "h" if random.random() < high_priority_content_percentage else "l"
                    object_response_time[object_id] = np.random.uniform(0.01, 0.2)
                if request_type == "REST.GET.OBJECT":
                    interest_lifetime = 4
                    i += 1
                    if i == trace_len_limit:
                        break
                    trace_file.write(
                        "{},{},{},{},{},{},{}\n".format("d", timestamp, object_id, total_object_size,
                                                        object_priority[object_id], interest_lifetime,
                                                        object_response_time[object_id]))
            except:
                continue
