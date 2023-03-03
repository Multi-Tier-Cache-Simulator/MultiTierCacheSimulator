# import json
# import os
# import time
# from traces.trace_reading.trace_creator import TraceCreator
# from common.deque import Deque
# from plots.plot_creation import Plot
#
from traces.trace_analysis.CSVTraceDistribution import CSVTraceDistributions, event_distribution

csvTraceDistributions = CSVTraceDistributions("out")
csvTraceDistributions.size_distribution("C:/Users/gl_ai/OneDrive/Documents/multi_tier_cache_simulator/resources"
                                        "/dataset_snia/IBMObjectStoreTrace000Part0.csv")
# csvTraceDistributions.frequency_counter("../resources/dataset_jedi/out.csv", 2)
event_distribution("C:/Users/gl_ai/OneDrive/Documents/multi_tier_cache_simulator/resources"
                                         "/dataset_snia/IBMObjectStoreTrace000Part0.csv")
# output_folder = "C:/Users/gl_ai/OneDrive/Documents/multi_tier_cache_simulator/logs/Thu_16_Feb_2023_11-00-55"
# slot_size = 8000
# nb_interests = 18067
# nb_high_priority = 7544
# nb_low_priority = 10523
# Plot(output_folder, slot_size, nb_interests, nb_high_priority, nb_low_priority)
# import time
#
# import numpy as np

# constants:
# data size between 100 bytes and 8000 bytes
# data rtt between 10ms to 200ms
# interest lifetime = 1s
# traffic period = 24h = 1440min

# variables:
# n unique items
# percentage of high priority content
# alpha zipf
# requests/s, 1.0 --> 1000requests/s

# TraceCreator(n_unique_items=200, high_priority_content_percentage=0.5,
#              zipf_alpha=1.2, poisson_lambda=10, loss_probability=0.0,
#              min_data_size=100, max_data_size=8000,
#              min_data_rtt=0.01, max_data_rtt=0.2,
#              interest_lifetime=1,
#              traffic_period=30)

# jsonToCSV = JsonToCSVTrace("resources/ndn6dump.box1.json.gz", trace_len_limit=200000)
# jsonTraceD = JsonTraceDistributions()
# jsonTraceD.event_distribution("resources/dataset_jedi/ndn6dump.box1.json.gz")
# jsonTraceD.packets_distribution("resources/dataset_jedi/ndn6dump.box1.json.gz")
# jsonTraceD.size_distribution("resources/dataset_jedi/ndn6dump.box1.json.gz")
# def insert_into_lists(L, Dram, disk, value, index):
#     # insert the new value into the main list (L)
#     L.insert(index, value)
#
#     # determine which list (L1 or L2) the new value should be inserted into
#     if index <= 1:
#         Dram.insert(index, value)
#     else:
#         disk.insert(index - 2, value)
#
#     # if L2 has more than 2 elements, move an element from L2 to L1
#     if len(disk) > 2:
#         Dram.append(disk.pop(0))
#
#     print(L)
#     print(Dram)
#     print(disk)
#
#
# L = [2, 4, 1, 18]
# Dram = [2, 4]
# disk = [1, 18]
# insert_into_lists(L, Dram, disk, 25, 3)
# print(10 % 5)
# print(len([1,2,3]))

# my_list = [10, 20, 30 ]
# item = 20
#
# reversed_index = len(my_list) - my_list.index(item) - 1
# print(reversed_index) # Output: 2
