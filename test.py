# import time
# from traces.CSVTraceDistribution import CSVTraceDistributions
# from traces.JsonTraceDistributions import JsonTraceDistributions
# from traces.jsonToCSV import JsonToCSVTrace
from traces.trace_creator import TraceCreator

# poisson = 0.1 --> 1 request every 1ms
# data rtt in range 10ms to 200ms
# interest lifetime = 1ms
traceCreator = TraceCreator(n_unique_items=3000, high_priority_content_percentage=0.5,
                            zipf_alpha=1.2, poisson_lambda=10.0, loss_probability=0.0,
                            min_data_size=100, max_data_size=8000,
                            min_data_rtt=10000000, max_data_rtt=200000000,
                            interest_lifetime=1000000,
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
