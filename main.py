import sys
import os
import time
import simpy
from traces.ndn_trace import NDNTrace
from simulation import Simulation
from storage_structures import Tier, StorageManager, Index
from policies.arcpolicy import ARCPolicy
from policies.lru_policy import LRUPolicy

# verify if the version of python is >3
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

# turn the trace into packets
trace = NDNTrace()
trace.gen_data()

# log files
output_folder = "logs/<timestamp>"
output_folder = output_folder.replace('/', os.path.sep).replace("<timestamp>",
                                                                time.strftime("%a_%d_%b_%Y_%H-%M-%S", time.localtime()))
output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), output_folder))
try:
    os.makedirs(output_folder, exist_ok=True)
except:
    print(f'Error trying to create output folder "{output_folder}"')

for i in range(2):
    # Init simpy env
    env = simpy.Environment()

    # create the index
    index = Index()
    if i == 0:
        # Create the storage tiers
        dram = Tier(name="DRAM", max_size=2 * 10 ** 9, granularity=1, latency=1e-7, throughput=1.25e10,
                    target_occupation=0.6)
        nvme = Tier(name="NVMe", max_size=2 * 10 ** 12, granularity=512, latency=1e-4, throughput=2e9,
                    target_occupation=0.9)

        # The storage manager is a utility object giving info on the tier ordering & default tier
        tiers = [dram, nvme]
        storage = StorageManager(index, tiers, env)

        # Creating the eviction policies
        policy_DRAM = ARCPolicy(dram, storage, env)
        policy_PMEM = LRUPolicy(nvme, storage, env)

        sim = Simulation([trace], storage, env, log_file=os.path.join(output_folder, "latest.log"),
                         progress_bar_enabled=False,
                         logs_enabled=True)

        print("Starting simulation")

        # start the simulation
        last_results = sim.run()
        last_results = f'{"#" * 10} Run {"#" * 10}\n{last_results}\n'
        for tier in tiers:
            for stat_name, stat_value in [("Number of io", tier.number_of_reads + tier.number_of_write),
                                          ("Number of migration io ", tier.number_of_prefetching_from_this_tier
                                                                      + tier.number_of_prefetching_to_this_tier
                                                                      + tier.number_of_eviction_from_this_tier
                                                                      + tier.number_of_eviction_to_this_tier),
                                          ("Time spent reading", round(tier.time_spent_reading, 3)),
                                          ("Time spent writing", round(tier.time_spent_writing, 3))]:
                line_name = f'{tier.name} - {stat_name}'
        try:
            with open(os.path.join(output_folder, "last_results.txt"), "w") as f:
                f.write(last_results)
        except:
            print(f'Error trying to write into a new file in output folder "{output_folder}"')

    if i == 1:
        # Create the storage tiers
        dram = Tier(name="DRAM", max_size=5.12 * 10 ** 11, granularity=1, latency=1e-7, throughput=1.25e10,
                    target_occupation=0.6)

        # The storage manager is a utility object giving info on the tier ordering & default tier
        tiers = [dram]
        storage = StorageManager(index, tiers, env)

        # Creating the eviction policies
        policy_DRAM = LRUPolicy(dram, storage, env)

        sim = Simulation([trace], storage, env, log_file=os.path.join(output_folder, "latest2.log"),
                         progress_bar_enabled=False,
                         logs_enabled=True)

        print("Starting simulation")

        # start the simulation
        last_results2 = sim.run()
        last_results2 = f'{"#" * 10} Run {"#" * 10}\n{last_results2}\n'
        for tier in tiers:
            for stat_name, stat_value in [("Number of io", tier.number_of_reads + tier.number_of_write),
                                          ("Number of migration io ", tier.number_of_prefetching_from_this_tier
                                                                      + tier.number_of_prefetching_to_this_tier
                                                                      + tier.number_of_eviction_from_this_tier
                                                                      + tier.number_of_eviction_to_this_tier),
                                          ("Time spent reading", round(tier.time_spent_reading, 3)),
                                          ("Time spent writing", round(tier.time_spent_writing, 3))]:
                line_name = f'{tier.name} - {stat_name}'
        try:
            with open(os.path.join(output_folder, "last_results2.txt"), "w") as f:
                f.write(last_results2)
        except:
            print(f'Error trying to write into a new file in output folder "{output_folder}"')
