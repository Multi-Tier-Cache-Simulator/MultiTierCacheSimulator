# import json
# import os
import os
import time
from traces.trace_creator import TraceCreator
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
# log files


#change in zipf
# TraceCreator(n_unique_items=50000, high_priority_content_percentage=0.5,
#              zipf_alpha=0.8, poisson_lambda=1.0, loss_probability=0.0,
#              min_data_size=100, max_data_size=8000,
#              min_data_rtt=10000000, max_data_rtt=200000000,
#              interest_lifetime=1000000000,
#              traffic_period=1440)
TraceCreator(n_unique_items=50000, high_priority_content_percentage=0.5,
             zipf_alpha=1.2, poisson_lambda=1.0, loss_probability=0.0,
             min_data_size=100, max_data_size=8000,
             min_data_rtt=10000000, max_data_rtt=200000000,
             interest_lifetime=1000000,
             traffic_period=1440)

# change in HPC percentage
TraceCreator(n_unique_items=50000, high_priority_content_percentage=0.0,
             zipf_alpha=1.2, poisson_lambda=1.0, loss_probability=0.0,
             min_data_size=100, max_data_size=8000,
             min_data_rtt=10000000, max_data_rtt=200000000,
             interest_lifetime=1000000,
             traffic_period=1440)
TraceCreator(n_unique_items=50000, high_priority_content_percentage=0.1,
             zipf_alpha=1.2, poisson_lambda=1.0, loss_probability=0.0,
             min_data_size=100, max_data_size=8000,
             min_data_rtt=10000000, max_data_rtt=200000000,
             interest_lifetime=1000000,
             traffic_period=1440)
TraceCreator(n_unique_items=50000, high_priority_content_percentage=0.2,
             zipf_alpha=1.2, poisson_lambda=1.0, loss_probability=0.0,
             min_data_size=100, max_data_size=8000,
             min_data_rtt=10000000, max_data_rtt=200000000,
             interest_lifetime=1000000,
             traffic_period=1440)
TraceCreator(n_unique_items=50000, high_priority_content_percentage=0.8,
             zipf_alpha=1.2, poisson_lambda=1.0, loss_probability=0.0,
             min_data_size=100, max_data_size=8000,
             min_data_rtt=10000000, max_data_rtt=200000000,
             interest_lifetime=1000000,
             traffic_period=1440)
TraceCreator(n_unique_items=50000, high_priority_content_percentage=1.0,
             zipf_alpha=1.2, poisson_lambda=1.0, loss_probability=0.0,
             min_data_size=100, max_data_size=8000,
             min_data_rtt=10000000, max_data_rtt=200000000,
             interest_lifetime=1000000,
             traffic_period=1440)

# change in number of requests per second
TraceCreator(n_unique_items=50000, high_priority_content_percentage=0.5,
             zipf_alpha=1.2, poisson_lambda=0.1, loss_probability=0.0,
             min_data_size=100, max_data_size=8000,
             min_data_rtt=10000000, max_data_rtt=200000000,
             interest_lifetime=1000000,
             traffic_period=1440)
TraceCreator(n_unique_items=50000, high_priority_content_percentage=0.5,
             zipf_alpha=1.2, poisson_lambda=0.25, loss_probability=0.0,
             min_data_size=100, max_data_size=8000,
             min_data_rtt=10000000, max_data_rtt=200000000,
             interest_lifetime=1000000,
             traffic_period=1440)
TraceCreator(n_unique_items=50000, high_priority_content_percentage=0.5,
             zipf_alpha=1.2, poisson_lambda=0.5, loss_probability=0.0,
             min_data_size=100, max_data_size=8000,
             min_data_rtt=10000000, max_data_rtt=200000000,
             interest_lifetime=1000000,
             traffic_period=1440)


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
