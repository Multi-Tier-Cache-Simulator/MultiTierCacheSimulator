from traces.TraceDistributions import TraceDistributions
# from traces.jsonToCSV import JsonToCSVTrace
#
# jsonToCSV = JsonToCSVTrace("resources/ndn6dump.box1.json.gz",trace_len_limit=20000)
traceDistribution = TraceDistributions()
traceDistribution.event_distribution("resources/ndn6dump.box1.json.gz",trace_len_limit=20000)
traceDistribution.packets_distribution("resources/ndn6dump.box1.json.gz",trace_len_limit=20000)
traceDistribution.size_distribution("resources/ndn6dump.box1.json.gz",trace_len_limit=20000)

# average_packet_size = 400
# create the trace using zipf law
# from traces.trace_creator import TraceCreator
#
# traceCreator = TraceCreator(10, 1.2)

