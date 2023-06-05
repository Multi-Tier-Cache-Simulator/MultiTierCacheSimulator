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
last_timestamp = 0.0

with open('../../resources/raw_dataset/raw/cluster01.000') as f:
    with open('../../resources/raw_dataset/stats/cluster01.000-0.2-last0.5.csv', 'w', encoding="utf-8",
              newline='') as trace_file:
        for line in f:

            # print("line : %s" % line)
            split = line.split(',')
            # print("split: %s" % split)
            try:
                timestamp, anonymized_key, key_size, value_size, client_id, operation, ttl = split[:7]
                timestamp = int(timestamp)
                timestamp /= 100000
                if anonymized_key not in object_priority.keys():
                    object_priority[anonymized_key] = "h" if random.random() < high_priority_content_percentage else "l"
                    object_response_time[anonymized_key] = np.random.uniform(0.01, 0.2)
                # if request_type == "REST.GET.OBJECT":
                interest_lifetime = 4
                if last_timestamp >= timestamp:
                    timestamp = last_timestamp + np.random.uniform(0.01, 0.2)
                i += 1

                if i == trace_len_limit:
                    break
                trace_file.write(
                    "{},{},{},{},{},{},{}\n".format("d", timestamp, anonymized_key, value_size,
                                                    object_priority[anonymized_key], interest_lifetime,
                                                    object_response_time[anonymized_key]))
                last_timestamp = timestamp
            except Exception as e:
                print("Exception e %s" % e)
                continue
