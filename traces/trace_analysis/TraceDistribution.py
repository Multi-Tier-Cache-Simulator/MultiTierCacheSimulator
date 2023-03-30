import csv


# 'data_back', 'timestamp', 'name', 'size', 'priority', 'InterestLifetime', 'response_time'


class CSVTraceDistributions:
    def __init__(self, file_name: str, name: str, trace_len_limit:int):
        self.file_name = file_name
        self.name = name
        self.trace_len_limit = trace_len_limit

    def distributions(self):
        # for line in gzip.open(self.file_name, "r"):
        #     lines.append(json.loads(line))

        with open(self.file_name, encoding='utf8') as read_obj:
            csv_reader = csv.reader(read_obj, delimiter=',')
            lines = list(csv_reader)

        lines = lines[:min(len(lines), self.trace_len_limit)]

        # trace length
        trace_len = len(lines)

        timestamp = [float(line[1]) for line in lines]
        t_start = timestamp[0]
        t_end = timestamp[len(timestamp) - 1]
        traffic_period = t_end - t_start

        objects = [line[2] for line in lines]

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

        # number_of_packets = []
        # i = 0
        # h = 0
        # for line in lines:
        #     if i == 0:
        #         h = float(line[1])
        #     diff = float(line[1]) - h
        #     if diff < 1000000000:  # 1 second
        #         i += 1
        #     else:
        #         number_of_packets.append(i)
        #         i = 0
        # nb_req_per_s = sum(number_of_packets) / len(number_of_packets)

        with open('../../multi_tier_cache_simulator/resources/raw_dataset/stats/' + self.name
                  + '_Stats',
                  'w', encoding="utf-8",
                  newline='') as trace_file:
            trace_file.write("trace length : {}\n".format(trace_len))
            trace_file.write("trace volume (req/s) : \n".format())
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
            # trace_file.write("objects frequency : {}\n".format(frequency))
            # trace_file.write("minimum time before event occurrence : {}\n".format(min_period))
            # trace_file.write("maximum time before event occurrence : {}\n".format(max_period))
            # trace_file.write("average time before event occurrence : {}\n".format(moy))
            # trace_file.write("nb requests/s : {}\n".format(nb_req_per_s))
