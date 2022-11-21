import csv
import numpy as np
import time
from numpy import random
from forwarder_structures import Packet


# time is in nanosecond
# size is in byte
# 'data_back', 'timestamp', 'name', 'size', 'priority', 'InterestLifetime', 'response_time'

class TraceCreator:
    def __init__(self, NUniqueItems: int, HighPriorityContentPourcentage: float,
                 ZipfAlpha: float, PoissonLambda: float, LossProbability: float,
                 MinDataSize: int, MaxDataSize: int,
                 MinDataRTT: int, MaxDataRTT: int,
                 InterestLifetime: int, traffic_period: int):
        """"
        :param NUniqueItems: number of unique items
        :param ZipfAlpha: alpha of the distribution Zipf
        :param PoissonLambda: lambda of the poisson distribution
        :param LossProbability: interest loss in ]0, 1[
        :param MinDataSize: minimum data size octets
        :param MaxDataSize: maximum data size octets
        :param MinDataRTT: minimum response time for an interest in ns
        :param MaxDataRTT: maximum response time for an interest in ns
        :param InterestLifetime: interest life time in ns
        :param traffic_period: end - start timestamps of the trace in minutes
        """""

        # generate a catalog of items. Assign each item a size
        unique_words = dict()
        Nhpc = int(round(NUniqueItems * HighPriorityContentPourcentage, 0))
        nhpc = 0
        for i in range(NUniqueItems):
            size = int(round(np.random.uniform(MinDataSize, MaxDataSize), 0))
            priority = 'h'
            nhpc += 1
            if nhpc >= Nhpc:
                priority = 'l'
            packet = Packet("d", 0, i, size, priority)
            unique_words[i] = packet

        # generate current timestamp in nanoseconds
        t = int(round(time.time_ns(), 0))

        # run for traffic_period minutes
        end = t + traffic_period * 60000000000

        with open('resources/dataset_ndn/synthetic-trace-' + PoissonLambda.__str__() + '.csv', 'w', encoding="utf-8",
                  newline='') as f:
            writer = csv.writer(f)
            while t < end:
                # create requests on the words following a Zipf law
                index = np.random.zipf(ZipfAlpha)
                while index >= len(unique_words):
                    index = np.random.zipf(ZipfAlpha)
                # generate response time following
                response_time = int(round(np.random.uniform(MinDataRTT, MaxDataRTT), 0))
                if np.random.uniform(low=0.0, high=1.0, size=None) < LossProbability:
                    # the data for this interest won't return
                    li = ["i", t, unique_words[index].name, unique_words[index].size, 'l',
                          InterestLifetime, response_time]
                    writer.writerow(li)
                else:
                    # the data for this interest will return
                    ld = ["d", t, unique_words[index].name, unique_words[index].size, unique_words[index].priority,
                          InterestLifetime, response_time]
                    writer.writerow(ld)
                t += int(round(random.exponential(PoissonLambda) * 10e6, 0))
