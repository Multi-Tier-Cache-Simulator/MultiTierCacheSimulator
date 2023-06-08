import os
import sys
import time

from plots.plot_creation import Plot
from experiments import arc_main, policy_main
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

# turn the trace into packets
arcTrace = ARCTrace()
arcTrace.gen_data()
# arcTrace.gen_data(trace_len_limit=99999)

priorityTrace = PriorityTrace()
priorityTrace.gen_data()
# priorityTrace.gen_data(trace_len_limit=99999)

trace = CommonTrace()
trace.gen_data()
# trace.gen_data(trace_len_limit=99999)


slot_size = max([int(line[3]) for line in trace.data])
nb_objects = len(list(set([line[2] for line in trace.data])))

total_size = [(slot_size * nb_objects * 10) / 100]

# proportions
# size_proportion = [1 / 10, 2 / 10, 3 / 10, 4 / 10]
size_proportion = [2 / 10]

# read throughput
throughput = [2]

# M_ARC
m_arc = ["AbstractMARCPolicy", "MARCPolicy", "MARCPolicy"]
m_arc_fromlist = ["policies.MARC.abstract_m_arc_policy", "policies.MARC.tier_m_arc_policy",
                  "policies.MARC.tier_m_arc_policy"]
arc_main("M_ARC", m_arc, m_arc_fromlist, slot_size, size_proportion, total_size, throughput,
         arcTrace, output_folder, False)

# QM_ARC
qm_arc = ["AbstractQMARCPolicy", "QMARCPolicy", "QMARCPolicy"]
qm_arc_fromlist = ["policies.QM_ARC.abstract_qm_arc_policy", "policies.QM_ARC.tier_qm_arc_policy",
                   "policies.QM_ARC.tier_qm_arc_policy"]
arc_main("QM_ARC", qm_arc, qm_arc_fromlist, slot_size, size_proportion, total_size,
         throughput, arcTrace, output_folder, False)

# QL_MQ_ARC
ql_qm_arc = ["AbstractQLQMARCPolicy", "QLQMARCPolicy", "QLQMARCPolicy"]
ql_qm_arc_fromlist = ["policies.QL_QM_ARC.abstract_ql_qm_arc_policy",
                      "policies.QL_QM_ARC.tier_ql_qm_arc_policy",
                      "policies.QL_QM_ARC.tier_ql_qm_arc_policy"]
arc_main("QL_QM_ARC", ql_qm_arc, ql_qm_arc_fromlist, slot_size, size_proportion, total_size,
         throughput, arcTrace, output_folder, False)

# Priority
policy_main("PriorityLRU", LRUPolicy, slot_size, size_proportion, total_size, throughput, priorityTrace, output_folder, False)

# LRU
policy_main("LRU", LRUPolicy, slot_size, size_proportion, total_size, throughput, trace, output_folder, False)

# LFU
policy_main("LFU", LFUPolicy, slot_size, size_proportion, total_size, throughput, trace, output_folder, False)

# RAND
policy_main("Rand", RandPolicy, slot_size, size_proportion, total_size, throughput, trace, output_folder, False)

# output_folder = "C:/Users/gl_ai/OneDrive/Documents/multi_tier_cache_simulator/logs/Mon_05_Jun_2023_09-01-52"
Plot(output_folder, slot_size)
