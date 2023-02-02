# import random
# from scipy.stats import zipf
# import pandas as pd
#
# num_requests = 1000  # change this to generate more or fewer requests
# poisson_lambda = 5  # change this to adjust the rate of request arrival average of 5 events/s
#
# # Zipf distribution
# zipf_alpha = 1.5
# zipf_x = list(range(1, num_requests + 1))
# zipf_dist = zipf.pmf(zipf_x, zipf_alpha)
#
# # Create a list of names based on Zipf distribution
# names = []
# for i in range(num_requests):
#     names.append(random.choices(zipf_x, zipf_dist)[0])
#
# # Create a list of priorities, high and low
# priorities = ["h"] * (num_requests // 2) + ["l"] * (num_requests // 2)
# random.shuffle(priorities)
#
# trace_data = []
#
# time_counter = 0
# for i in range(num_requests):
#     req_time = time_counter + random.expovariate(poisson_lambda)
#     time_counter = req_time
#     name = names[i]
#     size = random.randint(10, 100)
#     priority = priorities[i]
#     lifetime = random.randint(1, 5)
#     response_time = random.randint(1, 5) / 10
#
#     trace_data.append(["d", req_time, name, size, priority, lifetime, response_time])
#
# trace_df = pd.DataFrame(trace_data)
# trace_df.to_csv("ndn_trace.csv", index=False)
#
# print("Trace file 'ndn_trace.csv' generated successfully with {} requests.".format(num_requests))
# # =============================
# import random
#
# # Zipf distribution generator
# from typing import Any
#
# # import pandas as pd
# # from matplotlib import pyplot as plt
#
#
# def zipf_distribution(alpha: float, n: int) -> int:
#     denom = 0
#     denom_list = []
#     cum_prob = 0
#     cum_prob_list = []
#     for i in range(1, n + 1):
#         denom += 1 / (i ** alpha)
#         denom_list.append(denom)
#     denom = 1 / denom
#     for i in range(1, n + 1):
#         prob = denom / (i ** alpha)
#         cum_prob += prob
#         cum_prob_list.append(cum_prob)
#     rand = random.random()
#     for i in range(1, n + 1):
#         if rand < cum_prob_list[i - 1]:
#             return i
#     return n
#
#
# # generating the trace file
# def generate_trace(num_requests: int, alpha: float, poisson_lambda: float, n: int) -> tuple[
#     list[float | Any], list[int]]:
#     with open("ndn_trace.csv", "w") as trace_file:
#         time_counter = 0
#         names = []
#         tmsp = []
#         for i in range(num_requests):
#             request_time = time_counter + random.expovariate(poisson_lambda)
#             time_counter = request_time
#             name = zipf_distribution(alpha, n)
#             names.append(name)
#             tmsp.append(request_time)
#             size = random.randint(10, 100)
#             priority = random.choice(["h", "l"])
#             lifetime = random.randint(1, 5)
#             response_time = random.randint(1, 5) / 10
#             trace_file.write(
#                 "{},{},{},{},{},{},{}\n".format("d", request_time, name, size, priority, lifetime, response_time))
#         return tmsp, names
#
#
# poisson_lambda = 10
# n = 100
# num_requests = 10000
# alpha = 0.8
#
# generate_trace(num_requests, alpha, poisson_lambda, n)
#
# # python_indices = []
# #
# # for i in range(len(names)):
# #     if names[i] == names[0]:
# #         python_indices.append(i)
# #
# # tmsp = list(map(tmsp.__getitem__, python_indices))
# # names = [names[0]] * len(tmsp)
# #
# # df = pd.DataFrame(data={'NAME': names})
# # df.index = tmsp
# #
# # ax = df.plot(xlabel='Time', ylabel='DataName', marker='o', markerfacecolor='blue', markersize=5)
# # for c in ax.containers:
# #     labels = [v.get_height() if v.get_height() > 0 else '' for v in c]
# #     ax.bar_label(c, labels=labels, label_type='center')
# # plt.show()

# import random
#
#
# def zipf_distribution(alpha: float, n: int) -> int:
#     denom = 0
#     denom_list = []
#     cum_prob = 0
#     cum_prob_list = []
#     for i in range(1, n + 1):
#         denom += 1 / (i ** alpha)
#         denom_list.append(denom)
#     denom = 1 / denom
#     for i in range(1, n + 1):
#         prob = denom / (i ** alpha)
#         cum_prob += prob
#         cum_prob_list.append(cum_prob)
#     rand = random.random()
#     for i in range(1, n + 1):
#         if rand < cum_prob_list[i - 1]:
#             return i
#     return n
#
#
# def generate_trace(num_requests: int, num_content: int, poisson_lambda: float, alpha: float, high_priority: float,
#                    low_priority: float):
#     # create the trace file
#     with open("ndn_trace.csv", "w") as trace_file:
#         time_counter=0
#         for i in range(num_requests):
#             # randomly select a request time
#             req_time = time_counter + random.expovariate(poisson_lambda)
#             time_counter = req_time
#             # randomly select a size between 100 and 10000
#             size = random.randint(100, 10000)
#             # randomly select a priority
#             priority = "h" if random.random() < high_priority else "l"
#             # randomly select a lifetime between 1 and 10
#             lifetime = random.randint(1, 10)
#             # randomly select a response time between 1 and 100
#             response_time = random.randint(1, 100)
#             # choose an item using the zipf distribution
#             item = zipf_distribution(alpha, num_content)
#             # write the request to the trace file
#             trace_file.write("{},{},{},{},{},{},{}\n".format("d", req_time, item, size, priority, lifetime, response_time))
#
#
# # generate trace with 1000 requests, 50 content, alpha = 1.5 high priority 10% and low priority 90%
# generate_trace(1000, 50, 5, 1.2, 0.1, 0.9)
