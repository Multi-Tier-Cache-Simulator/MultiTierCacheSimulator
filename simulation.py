import json
import math
import simpy
from simpy.core import Environment

from resources import NDN_PACKETS

from forwarder import Forwarder
import sys
import os
import time

from traces.trace_creation_and_parsing.trace import Trace


class Simulation:
    def __init__(self, traces: "list[Trace]", forwarder: Forwarder, env: Environment,
                 log_file="logs/last_run.txt", logs_enabled=True):
        self._env = env
        self._forwarder = forwarder
        self._log_file = log_file
        self._logs_enabled = logs_enabled
        self._res = [simpy.Resource(env, capacity=1)
                     for _ in range(forwarder.tiers.__len__())]

        for trace in traces:
            self._env.process(self._read_trace(trace))

    def run(self):
        """Start the simpy simulation loop. At the end of the simulation, print the results"""
        t0 = time.time()
        self._env.run()
        print(f'Simulation finished after {round(time.time() - t0, 3)} seconds! Printing results:')
        data = []
        for tier in self._forwarder.tiers:
            data.append({'tier_name': tier.name,
                         'max_size': tier.max_size,
                         'target_occupation': tier.target_occupation,
                         'total_size': math.trunc(tier.max_size * tier.target_occupation),
                         'used_size': tier.used_size,
                         'waisted_size': tier.number_of_packets * self._forwarder.slot_size - tier.used_size,
                         'number_of_packets': tier.number_of_packets,
                         'number_of_prefetching_to_this_tier': tier.number_of_prefetching_to_this_tier,
                         'number_of_prefetching_from_this_tier': tier.number_of_prefetching_from_this_tier,
                         'number_of_eviction_to_this_tier': tier.number_of_eviction_to_this_tier,
                         'number_of_eviction_from_this_tier': tier.number_of_eviction_from_this_tier,
                         'number_of_write': tier.number_of_write,
                         'number_of_reads': tier.number_of_reads,
                         'time_spent_writing': tier.time_spent_writing,
                         'time_spent_reading': tier.time_spent_reading,
                         'high_p_data_retrieval_time': float(tier.high_p_data_retrieval_time),
                         'low_p_data_retrieval_time': float(tier.low_p_data_retrieval_time),
                         'chr': tier.chr,
                         'cmr': tier.cmr,
                         'chr_hpc': tier.chr_hpc,
                         'chr_lpc': tier.chr_lpc,
                         'penalty': tier.penalty,
                         'policy': tier.strategies.__str__(),
                         'trace': NDN_PACKETS.__str__()
                         })

        json_object = json.dumps(data, indent=4)
        return json_object

    def _read_trace(self, trace: Trace):
        last_ts = 0.0
        backup_stdout = sys.stdout
        if self._logs_enabled:
            os.makedirs(os.path.dirname(self._log_file), exist_ok=True)
            print(f'sys.stdout redirected to "./{self._log_file}".')
            sys.stdout = open(self._log_file, 'w')
        else:
            sys.stdout = open(os.devnull, "w+")
        for line in trace.data:
            t_start = float(line[1])
            yield self._env.timeout(
                max(0.0, t_start - last_ts))  # trace_creation_and_parsing are sorted by t_start order.
            last_ts = t_start
            self._env.process(
                trace.read_data_line(self._env, self._res, self._forwarder, line, self._log_file, self._logs_enabled))

        log_stream = sys.stdout
        sys.stdout = backup_stdout
        log_stream.close()
        print(
            f'Done simulating! sys.stdout was restored. Check the log file if enabled for more details on the '
            f'simulation.')
