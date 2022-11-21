# import time
# from traces.CSVTraceDistribution import CSVTraceDistributions
# from traces.JsonTraceDistributions import JsonTraceDistributions
# from traces.jsonToCSV import JsonToCSVTrace
from traces.trace_creator import TraceCreator

# poisson = 0.1 --> 1 request every 1ms
# data rtt in range 10ms to 200ms
# interest lifetime = 1ms
for i in range(11):
    traceCreator = TraceCreator(NUniqueItems=3000, HighPriorityContentPourcentage=i * 0.1,
                                ZipfAlpha=1.2, PoissonLambda=i * 1.0, LossProbability=0.0,
                                MinDataSize=100, MaxDataSize=8000,
                                MinDataRTT=10000000, MaxDataRTT=200000000,
                                InterestLifetime=1000000,
                                traffic_period=2880)


# jsonToCSV = JsonToCSVTrace("resources/ndn6dump.box1.json.gz", trace_len_limit=200000)

# csvTraceD = CSVTraceDistributions("ndn6trace")
# csvTraceD.event_distribution("resources/dataset_ndn/ndn6trace.csv")
# csvTraceD.packets_distribution("resources/dataset_ndn/ndn6trace.csv")
# csvTraceD.size_distribution("resources/dataset_ndn/ndn6trace.csv")

# jsonTraceD = JsonTraceDistributions()
# jsonTraceD.event_distribution("resources/dataset_ndn/ndn6dump.box1.json.gz")
# jsonTraceD.packets_distribution("resources/dataset_ndn/ndn6dump.box1.json.gz")
# jsonTraceD.size_distribution("resources/dataset_ndn/ndn6dump.box1.json.gz")

# csvTraceDistributions = CSVTraceDistributions("synthetic-trace")
# csvTraceDistributions.event_distribution("resources/dataset_ndn/synthetic-trace.csv")
# csvTraceDistributions.packets_distribution("resources/dataset_ndn/synthetic-trace.csv")
# csvTraceDistributions.size_distribution("resources/dataset_ndn/synthetic-trace.csv")

# # import random
# import math
#
# _lambda = 0.0000001
# _num_arrivals = 100
# _arrival_time = int(round(time.time_ns(), 0))
#
# print('RAND,INTER_ARRV_T,ARRV_T')
# # generate current timestamp
# # run for traffic_period minutes
# end = _arrival_time + 10 * 60000000000
# while _arrival_time < end:
#     # Get the next probability value from Uniform(0,1)
#     p = random.random()
#     # Plug it into the inverse of the CDF of Exponential(_lamnbda)
#     _inter_arrival_time = -math.log(1.0 - p) / _lambda
#     # Add the inter-arrival time to the running sum
#     _arrival_time = _arrival_time + _inter_arrival_time
#
#     # print it all out
#     # print(str(_inter_arrival_time))
#     print(str(int(_arrival_time)))
