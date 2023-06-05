import json
import math
import os
import sys
import time

import simpy
from simpy.core import Environment
from common import penalty
from forwarder_structures.forwarder import Forwarder
from resources import NDN_PACKETS
from traces.trace_reading.trace import Trace


class Simulation:
    def __init__(self, traces: "list[Trace]", forwarder: Forwarder, env: Environment,
                 log_file="logs/last_run.txt", logs_enabled=True):
        self._env = env
        self._forwarder = forwarder
        self._log_file = log_file
        self._logs_enabled = logs_enabled
        self._res = [simpy.Resource(env, capacity=1)
                     for _ in range(forwarder.tiers.__len__())]
        self._name_lock = simpy.Resource(env, capacity=1)
        for trace in traces:
            self._env.process(self._read_trace(trace))
            # number of requests on high priority content
            self.nb_high_priority = [line for line in trace.data if line[4] == 'h'].__len__()
            # number of requests on low priority content
            self.nb_low_priority = [line for line in trace.data if line[4] == 'l'].__len__()
            # total number of requests
            self.nb_interests = len(trace.data)
            # total number of objects
            self.nb_objects = len(list(set([line[2] for line in trace.data])))

    def run(self):
        """Start the simpy simulation loop. At the end of the simulation, print the results"""
        t0 = time.time()
        self._env.run()
        print(f'Simulation finished after {round(time.time() - t0, 3)} seconds! Printing results:')
        data = []
        all_size = 0
        for tier in self._forwarder.tiers:
            all_size += tier.max_size
            data.append({'tier_name': tier.name,
                         'policy name': tier.strategies.__str__(),
                         'trace name': NDN_PACKETS.__str__(),
                         'cache hit ratio': tier.chr / self.nb_interests,
                         'cache hit ratio hpc': tier.chr_hpc / self.nb_high_priority,
                         'cache hit ratio lpc': tier.chr_lpc / self.nb_low_priority,

                         'penalty_hpc': tier.penalty_hpc,
                         'penalty_lpc': tier.penalty_lpc,

                         'avg_hpc_retrieval_time': float(tier.high_p_data_retrieval_time) / self.nb_high_priority,
                         'avg_lpc_retrieval_time': float(tier.low_p_data_retrieval_time) / self.nb_low_priority,
                         'avg_v_retrieval_time': (float(tier.low_p_data_retrieval_time) + float(
                             tier.high_p_data_retrieval_time)) / 2,

                         'high_p_data_retrieval_time': float(tier.high_p_data_retrieval_time),
                         'low_p_data_retrieval_time': float(tier.low_p_data_retrieval_time),

                         'nb_objects': self.nb_objects,

                         'all_size': all_size,
                         'max_size': tier.max_size,
                         'read_throughput': tier.read_throughput,
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

                         'chr': tier.chr,
                         'chr_hpc': tier.chr_hpc,
                         'chr_lpc': tier.chr_lpc,
                         'nb_interests': self.nb_interests,
                         'nb_low_priority': self.nb_low_priority,
                         'nb_high_priority': self.nb_high_priority,
                         'cmr': tier.cmr,
                         'cmr_hpc': tier.cmr_hpc,
                         'cmr_lpc': tier.cmr_lpc,
                         'alpha': penalty.get_alpha()
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
                max(0.0, t_start - last_ts))  # trace_reading are sorted by t_start order.
            last_ts = t_start
            data_back, timestamp, name, size, priority, interest_life_time, response_time = line
            print("=========")
            print('interest on %s arrived at %s ' % (name, timestamp))

            self._env.process(
                trace.read_data_line(self._env, self._name_lock, self._res, self._forwarder, line, self._log_file,
                                     self._logs_enabled))

        log_stream = sys.stdout
        sys.stdout = backup_stdout
        log_stream.close()
        print(
            f'Done simulating! sys.stdout was restored. Check the log file if enabled for more details on the '
            f'simulation.')
