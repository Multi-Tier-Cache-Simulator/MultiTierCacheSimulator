import csv
import numpy as np
import time
from numpy import random
from common.packet import Packet
from common.zipf import zip_f


# time is in nanosecond
# size is in byte
# 'data_back', 'timestamp', 'name', 'size', 'priority', 'InterestLifetime', 'response_time'


class TraceCreator:
    def __init__(self, n_unique_items: int, high_priority_content_percentage: float,
                 zipf_alpha: float, poisson_lambda: float, loss_probability: float,
                 min_data_size: int, max_data_size: int,
                 min_data_rtt: int, max_data_rtt: int,
                 interest_lifetime: int, traffic_period: int):
        """"
        :param n_unique_items: number of unique items
        :param zipf_alpha: alpha of the distribution Zipf
        :param poisson_lambda: lambda of the poisson distribution
        :param loss_probability: interest loss in ]0, 1[
        :param min_data_size: minimum data size octets
        :param max_data_size: maximum data size octets
        :param min_data_rtt: minimum response time for an interest in ns
        :param max_data_rtt: maximum response time for an interest in ns
        :param interest_lifetime: interest life time in ns
        :param traffic_period: end - start timestamps of the trace in minutes
        """""
        start_time = time.time()
        print("Start creating the trace at: " + start_time.__str__())

        # generate a catalog of items. Assign each item a size
        unique_words = dict()
        n_hpc = int(round(n_unique_items * high_priority_content_percentage, 0))
        n_hpc_created = 0
        a = True
        for i in range(n_unique_items):
            size = int(round(np.random.uniform(min_data_size, max_data_size), 0))
            if a:
                priority = 'h'
                n_hpc_created += 1
                a = False
            else:
                priority = 'l'
                a = True
            if n_hpc_created >= n_hpc:
                priority = 'l'
                n_hpc_created -= 1
            packet = Packet("d", 0, i.__str__(), size, priority)
            unique_words[i] = packet

        # generate current timestamp in nanoseconds
        t = int(round(time.time_ns(), 0))
        print("Finished generation unique packets at: ", time.time().__str__())

        # run for traffic_period minutes
        end = t + traffic_period * 60000000000

        with open('resources/dataset_ndn/synthetic-trace-' + poisson_lambda.__str__() + "_" + n_unique_items.__str__()
                  + "_" + zipf_alpha.__str__() + "_" + high_priority_content_percentage.__str__()
                  + '.csv', 'w', encoding="utf-8",
                  newline='') as f:
            writer = csv.writer(f)
            while t < end:
                # create requests on the words following a Zipf law
                index = zip_f(zipf_alpha, len(unique_words))
                while index >= len(unique_words):
                    index = zip_f(zipf_alpha, len(unique_words))
                # index = np.random.zipf(zipf_alpha)
                # while index >= len(unique_words):
                #     index = np.random.zipf(zipf_alpha)
                # unique_words[index].__str__()
                # generate response time following
                response_time = int(round(np.random.uniform(min_data_rtt, max_data_rtt), 0))
                if np.random.uniform(low=0.0, high=1.0, size=None) < loss_probability:
                    # the data for this interest won't return
                    li = ["i", t, unique_words[index].name, unique_words[index].size, 'l',
                          interest_lifetime, response_time]

                    writer.writerow(li)
                else:
                    # the data for this interest will return
                    ld = ["d", t, unique_words[index].name, unique_words[index].size, unique_words[index].priority,
                          interest_lifetime, response_time]
                    writer.writerow(ld)
                t += int(round(random.exponential(poisson_lambda) * 10e6, 0))
        creation_time = time.time() - start_time
        print("Finished creating the trace at: " + time.time().__str__())
        with open(
                'resources/dataset_ndn/synthetic-trace-' + time.time().__str__() + "_" + n_unique_items.__str__()
                + "_" + zipf_alpha.__str__() + "_" + high_priority_content_percentage.__str__() + '.csv',
                'w', encoding="utf-8",
                newline='') as f:
            writer = csv.writer(f)
            writer.writerow("Trace creation took: " + creation_time.__str__())
