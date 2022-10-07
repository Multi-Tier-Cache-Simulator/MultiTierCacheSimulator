from traces.CSVTraceDistribution import CSVTraceDistributions
from traces.JsonTraceDistributions import JsonTraceDistributions
from traces.jsonToCSV import JsonToCSVTrace
from traces.trace_creator import TraceCreator

# traceCreator = TraceCreator(100000, 1.2)

jsonToCSV = JsonToCSVTrace("resources/ndn6dump.box1.json.gz", trace_len_limit=200000)

csvTraceD = CSVTraceDistributions("ndn6trace")
csvTraceD.event_distribution("resources/dataset_ndn/ndn6trace.csv")
csvTraceD.packets_distribution("resources/dataset_ndn/ndn6trace.csv")
csvTraceD.size_distribution("resources/dataset_ndn/ndn6trace.csv")

# csvTraceDistributions = CSVTraceDistributions("synthetic-trace")
# csvTraceDistributions.event_distribution("resources/dataset_ndn/synthetic-trace.csv",trace_len_limit=20000)
# csvTraceDistributions.packets_distribution("resources/dataset_ndn/synthetic-trace.csv",trace_len_limit=20000)
# csvTraceDistributions.size_distribution("resources/dataset_ndn/synthetic-trace.csv",trace_len_limit=20000)


