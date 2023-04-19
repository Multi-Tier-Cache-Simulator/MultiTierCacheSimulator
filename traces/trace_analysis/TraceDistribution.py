import collections
import csv

import numpy as np
from matplotlib import pyplot as plt


# 'data_back', 'timestamp', 'name', 'size', 'priority', 'InterestLifetime', 'response_time'


class CSVTraceDistributions:
    def __init__(self, file_name: str, name: str, trace_len_limit: int):
        self.file_name = file_name
        self.name = name
        self.trace_len_limit = trace_len_limit

    def distributions(self):
        # for line in gzip.open(self.file_name, "r"):
        #     lines.append(json.loads(line))

        with open(self.file_name, encoding='utf8') as read_obj:
            csv_reader = csv.reader(read_obj, delimiter=',')
            lines = list(csv_reader)

        if self.trace_len_limit != -1:
            lines = lines[:min(len(lines), self.trace_len_limit)]

        # trace length
        trace_len = len(lines)

        timestamp = [float(line[1]) for line in lines]
        t_start = timestamp[0]
        t_end = timestamp[len(timestamp) - 1]
        traffic_period = t_end - t_start

        objects = [line[2] for line in lines]

        # trace volume (req/s)
        event_count = 0
        last_timestamp = None
        timestamp = None
        for line in lines:
            timestamp = line[1]
            timestamp = float(timestamp)
            if last_timestamp is not None and timestamp != last_timestamp:
                event_count += 1
            last_timestamp = timestamp
        event_rate = event_count / (timestamp + 1)

        # frequency of objects
        # frequency = Counter(objects)

        objects = list(set(objects))

        # N unique objects
        nb_unique_obj = len(objects)

        sizes = [int(line[3]) for line in lines]

        # min object size
        min_obj_size = min(sizes)

        # max object size
        max_obj_size = max(sizes)

        # average object size
        average_obj_size = sum(sizes) / len(sizes)

        priority = [(line[2], line[4]) for line in lines]
        priority = list(set(priority))

        high_priority_percentage = len([line[1] for line in priority if line[1] == 'h']) / len(priority)

        response_time = [float(line[6]) for line in lines]

        # minimum response time
        min_response_time = min(response_time)

        # maximum response time
        max_response_time = max(response_time)

        # average response time
        average_response_time = sum(response_time) / len(response_time)

        interest_life_time = [float(line[5]) for line in lines]
        average_interest_life_time = sum(interest_life_time) / len(interest_life_time)

        # xi_1 = 0
        # diff = 0
        #
        # # minimum time before event occurrence
        # min_period = 0
        #
        # # maximum time before event occurrence
        # max_period = 0
        #
        # for line in lines:
        #     if xi_1 == 0:
        #         min_period = float(line[1])
        #         xi_1 = float(line[1])
        #     else:
        #         diff += float(line[1]) - xi_1
        #         xi_1 = float(line[1])
        #
        # # average time of event occurrence
        # moy = diff / len(lines)
        # Extract the object IDs from the trace data
        object_ids = [line[2] for line in lines]

        priority_map = {}
        freq_count = collections.Counter(object_ids)
        sorted_objects = sorted(freq_count.items(), key=lambda x: x[1], reverse=True)

        for line in lines:
            priority_map[line[2]] = line[4]

        with open('../../multi_tier_cache_simulator/resources/raw_dataset/stats/' + self.name
                  + '_Stats',
                  'w', encoding="utf-8",
                  newline='') as trace_file:
            trace_file.write("trace length : {}\n".format(trace_len))
            trace_file.write("trace volume (req/s) : {}\n".format(event_rate))
            trace_file.write("N unique objects : {}\n".format(nb_unique_obj))
            trace_file.write("average object size : {}\n".format(average_obj_size))
            trace_file.write("high priority percentage : {}\n".format(high_priority_percentage))
            trace_file.write("average response time : {}\n".format(average_response_time))
            trace_file.write("interest life time : {}\n".format(average_interest_life_time))
            trace_file.write("traffic period : {}\n".format(traffic_period))

            trace_file.write("min object size : {}\n".format(min_obj_size))
            trace_file.write("max object size : {}\n".format(max_obj_size))
            trace_file.write("minimum response time : {}\n".format(min_response_time))
            trace_file.write("maximum response time : {}\n".format(max_response_time))
            trace_file.write("low priority percentage : {}\n".format(1 - high_priority_percentage))
            for obj, freq in sorted_objects:
                trace_file.write(f"frequency: {freq}, priority: {priority_map[obj]}; ")
            # trace_file.write("objects frequency : {}\n".format(frequency))
            # trace_file.write("minimum time before event occurrence : {}\n".format(min_period))
            # trace_file.write("maximum time before event occurrence : {}\n".format(max_period))
            # trace_file.write("average time before event occurrence : {}\n".format(moy))

        object_counts = {}
        for event in lines:
            object_id = event[2]
            if object_id in object_counts:
                object_counts[object_id] += 1
            else:
                object_counts[object_id] = 1

        # Rank the objects in decreasing order of frequency
        object_freq = sorted(object_counts.values(), reverse=True)

        # Plot the frequency of each object against its rank on a log-log scale
        x = np.arange(1, len(object_freq) + 1)
        y = np.array(object_freq)
        plt.loglog(x, y, marker='o')

        # Fit a line to the plot using linear regression
        coef = np.polyfit(np.log(x), np.log(y), 1)
        poly1d_fn = np.poly1d(coef)
        plt.loglog(x, np.exp(poly1d_fn(np.log(x))), '--')

        # Check the goodness of fit by calculating the coefficient of determination (R-squared)
        r_squared = np.corrcoef(np.log(x), np.log(y))[0, 1] ** 2
        print("R-squared:", r_squared)

        plt.xlabel('Rank')
        plt.ylabel('Frequency')
        plt.show()
