import csv

import numpy as np

# IBM trace column names = ("timestamp", "request type", "object id", "start offset", "end offset", "total object size")
# timestamps in milliseconds
# request type GET (used) PUT HEAD DELETE (won't be used)
# NDN trace column names = ("data_back", "timestamp", "name", "size", "priority", "InterestLifetime", "responseTime")

trace_len_limit = 20000000

with open('../../resources/dataset_ibm/IBMObjectStoreTrace000Part0') as f:
    with open('../../resources/ibm.csv', 'w', encoding="utf-8", newline='') as trace_file:
        for line in f:
            split = line.split(' ')
            try:
                timestamp, request_type, object_id, start_offset, end_offset, total_object_size = line
                print(request_type)
                timestamp = int(timestamp)
                if request_type == "REST.GET.OBJECT":
                    response_time = np.random.uniform(10, 200)
                    interest_lifetime = 1000
                    trace_file.write(
                        "{},{},{},{},{},{},{}\n".format("d", timestamp, object_id, total_object_size,
                                                        "h", interest_lifetime, response_time))
            except Exception as e:
                print(line)
                print(e)
                continue
