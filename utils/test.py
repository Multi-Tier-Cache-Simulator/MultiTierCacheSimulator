from traces.trace_analysis.TraceDistribution import CSVTraceDistributions

filename = "../resources/dataset_snia/IBMObjectStoreTrace000Part0.csv"
cSVTraceDistributions = CSVTraceDistributions(filename, "IBMObjectStoreTrace000Part0", 30000)
cSVTraceDistributions.distributions()

#
# import csv
# import os
#
# import numpy as np
# from matplotlib import pyplot as plt
#
# from utils.q_learning_arc_policy import Cache
# from utils.arc_policy import ARC
#
# path = "../resources/dataset_synthetic/synthetic-200_10_1.2_0.5_30.csv"
# # path = "../resources/dataset_synthetic/synthetic-200_10_1.2_0.5_30.csv"
# with open(path, encoding='utf8') as read_obj:
#     csv_reader = csv.reader(read_obj, delimiter=',')
#     data = list(csv_reader)
#
# # if 0 the Q-values are never updated, hence nothing is learned. if high value like 0.9 learning can occur quickly
# learning_rate_table = [1.0]
# # learning_rate_table = [1.0,0.9]
# # determines how much the RL agents cares about rewards in the distant future relative to those in the immediate future
# discount_factor_table = [0.1, 0.2]
# # discount_factor_table = [0.1]
# # if 0 pure greedy always selecting the highest q value for a specific state --> more exploitation
# # if very high select different actions --> more exploration
# epsilon_table = [0.1, 0.2]
# # epsilon_table = [0.1]
# # cache size
# # c = 5154
# c = 10
#
# for learning_rate in learning_rate_table:
#     for discount_factor in discount_factor_table:
#         for epsilon in epsilon_table:
#             with open(os.path.join(os.path.abspath(""),
#                                    learning_rate.__str__() + discount_factor.__str__() + epsilon.__str__() +
#                                    'results.csv'),
#                       'w', encoding="utf-8", newline='') as f:
#                 q_arc = Cache(c, learning_rate, discount_factor, epsilon)
#                 arc = ARC(c)
#                 for line in data:
#                     q_arc.on_packet_access(line[2])
#                     arc.on_packet_access(line[2])
#
#                 f.write("{},{},{},{},{}\n".format(learning_rate, discount_factor, epsilon,
#                                                   round(q_arc.cache_hit / q_arc.request, 2),
#                                                   round(arc.cache_hit / arc.request, 2)))
#                 plt.plot(np.convolve(q_arc.q_learning_agent.rewards, np.ones(1000) / 1000, mode='valid'))
#                 plt.savefig(os.path.join(os.path.abspath(""),
#                                          learning_rate.__str__() + discount_factor.__str__() + epsilon.__str__() + ".png"))
#
#                 # q_chr = round(q_arc.cache_hit / q_arc.request, 2)
#                 # print("q_arc cache hit ratio = %s" % q_chr)
#                 # # print("q_table = %s" % q_arc.q_learning_agent.q_table)
#                 # chr = round(arc.cache_hit / arc.request, 2)
#                 # print("arc cache hit ratio = %s" % chr)
#
# # plt.plot(q_arc.p_table[:1000])
# # plt.show()
# from traces.trace_creating_and_parsing.synthetic_trace import TraceCreator
# traceCreator = TraceCreator(n_unique_items=10, high_priority_content_percentage=0.2, zipf_alpha=2.0,
#                             poisson_lambda=1000, min_data_size=100, max_data_size=8000, min_data_rtt=0.01,
#                             max_data_rtt=0.2, interest_lifetime=2, traffic_period=10)
