import math
from simpy.core import Environment
from traces.trace import Trace
from forwarder_structures import Forwarder
import sys
import os
import time


class Simulation:
    def __init__(self, traces: "list[Trace]", forwarder: Forwarder, env: Environment,
                 log_file="logs/last_run.txt", logs_enabled=True):
        self._env = env
        self._forwarder = forwarder
        self._log_file = log_file
        self._logs_enabled = logs_enabled

        # Adding traces to env as processes
        for trace in traces:
            self._env.process(self._read_trace(trace))

    def run(self):
        """Start the simpy simulation loop. At the end of the simulation, print the results"""
        t0 = time.time()
        self._env.run()
        print(f'Simulation finished after {round(time.time() - t0, 3)} seconds! Printing results:')
        s = f'\n{" " * 4}>> '
        s2 = f'\n{" " * 8}>> '
        output = ""
        for tier in self._forwarder.tiers:
            output += (f'Tier "{tier.name}":'
                       f'{s}Total size {math.trunc(tier.max_size * tier.target_occupation)} o '
                       f'{s}Used size {tier.used_size} o '
                       f'{s}Waisted size {tier.number_of_packets * self._forwarder.slot_size - tier.used_size} o '
                       f'{s2}{tier.number_of_prefetching_to_this_tier} prefetching to this tier'
                       f'{s2}{tier.number_of_prefetching_from_this_tier} prefetching from this tier'
                       f'{s2}{tier.number_of_eviction_to_this_tier} eviction to this tier'
                       f'{s2}{tier.number_of_eviction_from_this_tier} eviction from this tier'
                       f'{s}{tier.number_of_write} total write'
                       f'{s}{tier.number_of_reads} total reads'
                       f'{s}Time spent reading {tier.time_spent_reading} ns'
                       f'{s}Time spent writing {tier.time_spent_writing} ns'
                       f'{s}Cache hit ratio {tier.chr}'
                       f'{s}Cache miss ratio {tier.cmr}\n\n')
        return output

    def _read_trace(self, trace: Trace):
        last_ts = 0
        backup_stdout = sys.stdout
        if self._logs_enabled:
            os.makedirs(os.path.dirname(self._log_file), exist_ok=True)
            print(f'sys.stdout redirected to "./{self._log_file}".')
            sys.stdout = open(self._log_file, 'w')
        else:
            sys.stdout = open(os.devnull, "w+")
        for line in trace.data:
            tstart = int(line[1])
            yield self._env.timeout(max(0, tstart - last_ts))  # traces are sorted by tstart order.
            last_ts = tstart
            self._env.process(
                trace.read_data_line(self._env, self._forwarder, line, self._log_file, self._logs_enabled))

        log_stream = sys.stdout
        sys.stdout = backup_stdout
        log_stream.close()
        print(
            f'Done simulating! sys.stdout was restored. Check the log file if enabled for more details on the '
            f'simulation.')
