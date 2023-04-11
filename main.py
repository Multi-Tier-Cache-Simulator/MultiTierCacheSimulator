import os
import sys
import time

from experiments import arc_main, policy_main
from plots.plot_creation import Plot
from policies.ARC.abstract_arc_policy import AbstractARCPolicy
from policies.ARC.disk_arc_policy import DISKARCPolicy
from policies.ARC.dram_arc_policy import DRAMARCPolicy
# from policies.Q_learning_MQ_ARC.abstract_ql_mq_arc_policy import AbstractQLQoSARCPolicy
# from policies.Q_learning_MQ_ARC.disk_ql_mq_arc_policy import DISKQLQoSARCPolicy
# from policies.Q_learning_MQ_ARC.dram_ql_mq_arc_policy import DRAMQLQoSARCPolicy
from policies.MQ_ARC.abstract_mq_arc_policy import AbstractQoSARCPolicy
from policies.MQ_ARC.disk_mq_arc_policy import DISKQoSARCPolicy
from policies.MQ_ARC.dram_mq_arc_policy import DRAMQoSARCPolicy
from policies.lfu_policy import LFUPolicy
from policies.lru_policy import LRUPolicy
from policies.random_policy import RandPolicy
from traces.trace_reading.arc_trace import ARCTrace
from traces.trace_reading.common_trace import CommonTrace
from traces.trace_reading.priority_trace import PriorityTrace

# time is in nanos
# size is in byte

# verify if the version of python is >3
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

# slot size allocation in dram and nvme
slot_size = 8000
# slot_size = 1378116288

# turn the trace into packets
arcTrace = ARCTrace()
arcTrace.gen_data()
# arcTrace.gen_data(trace_len_limit=30000)

priorityTrace = PriorityTrace()
priorityTrace.gen_data()
# priorityTrace.gen_data(trace_len_limit=30000)

trace = CommonTrace()
trace.gen_data()
# trace.gen_data(trace_len_limit=30000)

# number of requests on high priority content
nb_high_priority = [line for line in trace.data if line[4] == 'h'].__len__()
# number of requests on low priority content
nb_low_priority = [line for line in trace.data if line[4] == 'l'].__len__()
# total number of requests
nb_interests = len(trace.data)
print("nb_high_priority %s, nb_low_priority %s, nb_interests %s" % (nb_high_priority, nb_low_priority, nb_interests))

# log files
output_folder = "logs/<timestamp>"
output_folder = output_folder.replace('/', os.path.sep).replace("<timestamp>",
                                                                time.strftime("%a_%d_%b_%Y_%H-%M-%S", time.localtime()))
output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), output_folder))
try:
    os.makedirs(output_folder, exist_ok=True)
except Exception as e:
    print(f'Error trying to create output folder "{output_folder}"')
    print(e)

# 401758 9552 9034 9677 5952
# total size 1000kB
# total_size = slot_size * 595
total_size = [slot_size * 10000 * 0.05]
#
# proportions
# size_proportion = [1 / 10, 2 / 10, 3 / 10, 4 / 10]
size_proportion = [2 / 10]

# read throughput
throughput = [2]
#
# # QL_QoS_ARC arc_main("QL_QoS_ARC", AbstractQLQoSARCPolicy, DRAMQLQoSARCPolicy, DISKQLQoSARCPolicy, slot_size,
# size_proportion, total_size, throughput, arcTrace, output_folder)

# MQ_ARC
arc_main("MQ_ARC", AbstractQoSARCPolicy, DRAMQoSARCPolicy, DISKQoSARCPolicy, slot_size, size_proportion, total_size,
         throughput, arcTrace, output_folder, True)

# ARC
arc_main("ARC", AbstractARCPolicy, DRAMARCPolicy, DISKARCPolicy, slot_size, size_proportion, total_size, throughput,
         arcTrace, output_folder, True)

# Priority
policy_main("PriorityLRU", LRUPolicy, slot_size, size_proportion, total_size, priorityTrace, output_folder, True)

# LRU
policy_main("LRU", LRUPolicy, slot_size, size_proportion, total_size, trace, output_folder, True)

# LFU
policy_main("LFU", LFUPolicy, slot_size, size_proportion, total_size, trace, output_folder, True)

# RAND
policy_main("Rand", RandPolicy, slot_size, size_proportion, total_size, trace, output_folder, True)

# output_folder = "multi_tier_cache_simulator/logs/Mon_13_Mar_2023_10-47-26"
Plot(output_folder, slot_size, nb_interests, nb_high_priority, nb_low_priority)
