import sys
import os
import time

from mains import arc_main, policy_main
from plots.plot_creation import Plot
from policies.ARC.abstract_arc_policy import AbstractARCPolicy
from policies.ARC.dram_arc_policy import DRAMARCPolicy
from policies.ARC.disk_arc_policy import DISKARCPolicy
from policies.LRUorPriority.dram_lru_policy import DRAMLRUPolicy
from policies.LRUorPriority.lru_policy import DISKLRUPolicy
from policies.LFU.dram_lfu_policy import DRAMLFUPolicy
from policies.LFU.lfu_policy import DISKLFUPolicy

from traces.trace_creation_and_parsing.arc_trace import ARCTrace
from traces.trace_creation_and_parsing.priority_trace import PriorityTrace
from traces.trace_creation_and_parsing.ndn_trace import NDNTrace

# time is in nanos
# size is in byte

# verify if the version of python is >3
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

# slot size allocation in dram and nvme
slot_size = 8000

# turn the trace into packets
arcTrace = ARCTrace()
arcTrace.gen_data()

priorityTrace = PriorityTrace()
priorityTrace.gen_data()

trace = NDNTrace()
trace.gen_data()

# trace.gen_data(trace_len_limit=200)

# number of requests on high priority content
nb_high_priority = [line for line in trace.data if line[4] == 'h'].__len__()
# number of requests on low priority content
nb_low_priority = [line for line in trace.data if line[4] == 'l'].__len__()
# total number of requests
nb_interests = len(trace.data)

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

# total size 1000kB
total_size = slot_size * 10

# proportions
# size_proportion = [1 / 10, 2 / 10, 3 / 10, 4 / 10]
size_proportion = [2 / 10]

# modified ARC
arc_main(AbstractARCPolicy, DRAMARCPolicy, DISKARCPolicy, slot_size, size_proportion, total_size, arcTrace,
         output_folder)

# Priority
policy_main(DRAMLRUPolicy, DISKLRUPolicy, slot_size, size_proportion, total_size, priorityTrace, output_folder)

# LRU
policy_main(DRAMLRUPolicy, DISKLRUPolicy, slot_size, size_proportion, total_size, trace, output_folder)

# LFU
policy_main(DRAMLFUPolicy, DISKLFUPolicy, slot_size, size_proportion, total_size, trace, output_folder)

# output_folder = "C:/Users/lna11/Desktop/multi_tier_cache_simulator/logs/Sun_15_Jan_2023_22-50-53"
Plot(output_folder, slot_size, nb_interests, nb_high_priority, nb_low_priority)
