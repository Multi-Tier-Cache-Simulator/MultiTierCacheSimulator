from simpy.core import Environment
from traces.trace import Trace
from storage_structures import StorageManager
from tqdm import tqdm
import sys
import os
import time


class Simulation:
    def __init__(self, traces: "list[Trace]", storage: StorageManager, env: Environment,
                 log_file="logs/last_run.txt",
                 progress_bar_enabled=True, logs_enabled=True):
        self._env = env
        self._storage = storage
        self._log_file = log_file
        self._progress_bar_enabled = progress_bar_enabled
        self._logs_enabled = logs_enabled

        # Adding traces to env as processes
        for trace in traces:
            self._env.process(self._read_trace(trace, True))

    def run(self):
        """Start the simpy simulation loop. At the end of the simulation, prints the results"""
        t0 = time.time()
        self._env.run()
        print(f'Simulation finished after {round(time.time() - t0, 3)} seconds! Printing results:')
        s = f'\n{" " * 4}>> '
        s2 = f'\n{" " * 8}>> '
        output = ""
        for tier in self._storage.tiers:
            # tier_occupation = sum([file.size for file in tier.content.values()])
            # total_migration_count = tier.number_of_eviction_from_this_tier + tier.number_of_eviction_to_this_tier + \
            #                        tier.number_of_prefetching_from_this_tier + tier.number_of_prefetching_to_this_tier
            output += (f'Tier "{tier.name}":'
                       f'{s}Used size {tier.used_size / (10 ** 9)} Go '
                       # f'{s}{total_migration_count} migrations'
                       # f'{s2}{tier.number_of_prefetching_to_this_tier} due to prefetching to this tiers'
                       # f'{s2}{tier.number_of_prefetching_from_this_tier} due to prefetching from this tiers'
                       # f'{s2}{tier.number_of_eviction_to_this_tier} due to eviction to this tiers'
                       # f'{s2}{tier.number_of_eviction_from_this_tier} due to eviction from this tiers'
                       f'{s}{tier.number_of_write} total write'
                       f'{s2}{tier.number_of_write - tier.number_of_prefetching_to_this_tier - tier.number_of_eviction_to_this_tier} because of user activity '
                       # f'{s2}{tier.number_of_prefetching_to_this_tier + tier.number_of_eviction_to_this_tier} '
                       'because of migration'
                       f'{s}{tier.number_of_reads} total reads'
                       f'{s2}{tier.number_of_reads - tier.number_of_prefetching_from_this_tier - tier.number_of_eviction_from_this_tier} because of user activity'
                       # f'{s2}{tier.number_of_prefetching_from_this_tier + tier.number_of_eviction_from_this_tier} '
                       # 'because of migration'
                       f'{s}Time spent reading {round(tier.time_spent_reading, 3)} ms'
                       f'{s}Time spent writing {round(tier.time_spent_writing, 3)} ms\n\n')
        return output

    def _read_trace(self, trace: Trace, simulate_perfect_prefetch: bool = False):
        last_ts = 0
        backup_stdout = sys.stdout
        if self._logs_enabled:
            os.makedirs(os.path.dirname(self._log_file), exist_ok=True)
            print(f'sys.stdout redirected to "./{self._log_file}".')
            sys.stdout = open(self._log_file, 'w')
        else:
            sys.stdout = open(os.devnull, "w+")
        if self._progress_bar_enabled:
            pbar = tqdm(total=len(trace.data), file=backup_stdout)

        for line in trace.data:
            if self._progress_bar_enabled:
                pbar.update(1)
            tstart = trace.timestamp_from_line(line)
            print(tstart)
            print(last_ts)
            print(tstart - last_ts)
            yield self._env.timeout(max(0, tstart - last_ts))  # traces are sorted by tstart order.
            last_ts = tstart
            trace.read_data_line(self._env, self._storage, line, self._logs_enabled)

        if self._progress_bar_enabled:
            pbar.close()
        log_stream = sys.stdout
        sys.stdout = backup_stdout
        log_stream.close()
        print(
            f'Done simulating! sys.stdout was restored. Check the log file if enabled for more details on the '
            f'simulation.')
