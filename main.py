import argparse
import sys
import os
import time
import simpy


from traces.ndn_trace import NDNTrace
from simulation import Simulation
from storage_structures import Tier, StorageManager, Index
from policies.arcpolicy import ARCPolicy
from policies.lru_policy import LRUPolicy
from policies.lfu_policy import LFUPolicy
from policies.dram_lru_policy import DRAMLRUPolicy
from policies.dram_lfu_policy import DRAMLFUPolicy
import matplotlib.pyplot as plt

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

plot_x = []  # storage config str
plot_y = []  # policy + stat -> value

for i in range(9):  # from 0 to 4 it's 2 tiers, from 5 to 7 it's one tier
    # Init simpy env
    env = simpy.Environment()
    # create the index
    index = Index()
    if i == 0:  # 2 tiers: DRAM ARC, Disk LRU with priority
        cache_hit_ratio = 0
        plot_x.append("DRAM ARC Disk LRU")
        # Create the storage tiers
        dram = Tier(name="DRAM", max_size=2 * 10 ** 9, granularity=1, latency=100e-6, throughput=1.25e10,
                    target_occupation=0.6)
        nvme = Tier(name="NVMe", max_size=2 * 10 ** 12, granularity=512, latency=1e-4, throughput=2e9,
                    target_occupation=0.9)

        # The storage manager is a utility object giving info on the tier ordering & default tier
        tiers = [dram, nvme]
        storage = StorageManager(index, tiers, env)
        # Creating the eviction policies
        ARCPolicy(dram, storage, env)
        LRUPolicy(nvme, storage, env)

        sim = Simulation([trace], storage, env, log_file=os.path.join(output_folder, "latest.log"),
                         progress_bar_enabled=False,
                         logs_enabled=True)
        print("Starting simulation")
        # start the simulation
        last_results = sim.run()
        last_results = f'{"#" * 10} Run {"#" * 10}\n{last_results}\n'
        for tier in tiers:
            cache_hit_ratio += tier.chr
        plot_y.append(cache_hit_ratio)
        try:
            with open(os.path.join(output_folder, "last_results.txt"), "w") as f:
                f.write(last_results)
        except:
            print(f'Error trying to write into a new file in output folder "{output_folder}"')
    if i == 1:  # 2 tiers: DRAM LRU, Disk LRU with priority
        cache_hit_ratio = 0
        plot_x.append("DRAM LRU Disk LRU")
        # Create the storage tiers
        dram = Tier(name="DRAM", max_size=5.12 * 10 ** 11, granularity=1, latency=1e-7, throughput=1.25e10,
                    target_occupation=0.6)
        nvme = Tier(name="NVMe", max_size=2 * 10 ** 12, granularity=512, latency=1e-4, throughput=2e9,
                    target_occupation=0.9)

        # The storage manager is a utility object giving info on the tier ordering & default tier
        tiers = [dram, nvme]
        storage = StorageManager(index, tiers, env)
        # Creating the eviction policies
        DRAMLRUPolicy(dram, storage, env)
        LRUPolicy(nvme, storage, env)

        sim = Simulation([trace], storage, env, log_file=os.path.join(output_folder, "latest2.log"),
                         progress_bar_enabled=False,
                         logs_enabled=True)
        print("Starting simulation")
        # start the simulation
        last_results2 = sim.run()
        last_results2 = f'{"#" * 10} Run {"#" * 10}\n{last_results2}\n'
        for tier in tiers:
            cache_hit_ratio += tier.chr
        plot_y.append(cache_hit_ratio)
        try:
            with open(os.path.join(output_folder, "last_results2.txt"), "w") as f:
                f.write(last_results2)
        except:
            print(f'Error trying to write into a new file in output folder "{output_folder}"')
    if i == 2:  # 2 tiers: DRAM LFU, Disk LRU with priority
        cache_hit_ratio = 0
        plot_x.append("DRAM LFU Disk LRU")
        # Create the storage tiers
        dram = Tier(name="DRAM", max_size=5.12 * 10 ** 11, granularity=1, latency=1e-7, throughput=1.25e10,
                    target_occupation=0.6)
        nvme = Tier(name="NVMe", max_size=2 * 10 ** 12, granularity=512, latency=1e-4, throughput=2e9,
                    target_occupation=0.9)

        # The storage manager is a utility object giving info on the tier ordering & default tier
        tiers = [dram, nvme]
        storage = StorageManager(index, tiers, env)
        # Creating the eviction policies
        DRAMLFUPolicy(dram, storage, env)
        LRUPolicy(nvme, storage, env)

        sim = Simulation([trace], storage, env, log_file=os.path.join(output_folder, "latest3.log"),
                         progress_bar_enabled=False,
                         logs_enabled=True)
        print("Starting simulation")
        # start the simulation
        last_results3 = sim.run()
        last_results3 = f'{"#" * 10} Run {"#" * 10}\n{last_results3}\n'

        for tier in tiers:
            cache_hit_ratio += tier.chr
        plot_y.append(cache_hit_ratio)
        try:
            with open(os.path.join(output_folder, "last_results3.txt"), "w") as f:
                f.write(last_results3)
        except:
            print(f'Error trying to write into a new file in output folder "{output_folder}"')
    if i == 3:  # 2 tiers: DRAM LRU, Disk LFU with priority
        cache_hit_ratio = 0
        plot_x.append("DRAM LRU Disk LFU")
        # Create the storage tiers
        dram = Tier(name="DRAM", max_size=5.12 * 10 ** 11, granularity=1, latency=1e-7, throughput=1.25e10,
                    target_occupation=0.6)
        nvme = Tier(name="NVMe", max_size=2 * 10 ** 12, granularity=512, latency=1e-4, throughput=2e9,
                    target_occupation=0.9)

        # The storage manager is a utility object giving info on the tier ordering & default tier
        tiers = [dram, nvme]
        storage = StorageManager(index, tiers, env)
        # Creating the eviction policies
        DRAMLRUPolicy(dram, storage, env)
        LFUPolicy(nvme, storage, env)

        sim = Simulation([trace], storage, env, log_file=os.path.join(output_folder, "latest4.log"),
                         progress_bar_enabled=False,
                         logs_enabled=True)
        print("Starting simulation")
        # start the simulation
        last_results4 = sim.run()
        last_results4 = f'{"#" * 10} Run {"#" * 10}\n{last_results4}\n'

        for tier in tiers:
            cache_hit_ratio += tier.chr
        plot_y.append(cache_hit_ratio)
        try:
            with open(os.path.join(output_folder, "last_results4.txt"), "w") as f:
                f.write(last_results4)
        except:
            print(f'Error trying to write into a new file in output folder "{output_folder}"')
    if i == 4:  # 2 tiers: DRAM LFU, Disk LFU with priority
        cache_hit_ratio = 0
        plot_x.append("DRAM LFU Disk LFU")
        # Create the storage tiers
        dram = Tier(name="DRAM", max_size=5.12 * 10 ** 11, granularity=1, latency=1e-7, throughput=1.25e10,
                    target_occupation=0.6)
        nvme = Tier(name="NVMe", max_size=2 * 10 ** 12, granularity=512, latency=1e-4, throughput=2e9,
                    target_occupation=0.9)

        # The storage manager is a utility object giving info on the tier ordering & default tier
        tiers = [dram, nvme]
        storage = StorageManager(index, tiers, env)
        # Creating the eviction policies
        DRAMLFUPolicy(dram, storage, env)
        LFUPolicy(nvme, storage, env)

        sim = Simulation([trace], storage, env, log_file=os.path.join(output_folder, "latest5.log"),
                         progress_bar_enabled=False,
                         logs_enabled=True)
        print("Starting simulation")
        # start the simulation
        last_results5 = sim.run()
        last_results5 = f'{"#" * 10} Run {"#" * 10}\n{last_results5}\n'

        for tier in tiers:
            cache_hit_ratio += tier.chr
        plot_y.append(cache_hit_ratio)
        try:
            with open(os.path.join(output_folder, "last_results5.txt"), "w") as f:
                f.write(last_results5)
        except:
            print(f'Error trying to write into a new file in output folder "{output_folder}"')
    if i == 5:  # 1 tier: DRAM LRU
        cache_hit_ratio = 0
        plot_x.append("DRAM LRU")
        # Create the storage tiers
        dram = Tier(name="DRAM", max_size=5.12 * 10 ** 11, granularity=1, latency=1e-7, throughput=1.25e10,
                    target_occupation=0.6)

        # The storage manager is a utility object giving info on the tier ordering & default tier
        tiers = [dram]
        storage = StorageManager(index, tiers, env)
        # Creating the eviction policies
        DRAMLRUPolicy(dram, storage, env)

        sim = Simulation([trace], storage, env, log_file=os.path.join(output_folder, "latest6.log"),
                         progress_bar_enabled=False,
                         logs_enabled=True)
        print("Starting simulation")
        # start the simulation
        last_results6 = sim.run()
        last_results6 = f'{"#" * 10} Run LRU {"#" * 10}\n{last_results6}\n'

        for tier in tiers:
            cache_hit_ratio += tier.chr
        plot_y.append(cache_hit_ratio)
        try:
            with open(os.path.join(output_folder, "last_results6.txt"), "w") as f:
                f.write(last_results6)
        except:
            print(f'Error trying to write into a new file in output folder "{output_folder}"')
    if i == 6:  # 1 tier: DRAM LFU
        cache_hit_ratio = 0
        plot_x.append("DRAM LFU")
        # Create the storage tiers
        dram = Tier(name="DRAM", max_size=5.12 * 10 ** 11, granularity=1, latency=1e-7, throughput=1.25e10,
                    target_occupation=0.6)

        # The storage manager is a utility object giving info on the tier ordering & default tier
        tiers = [dram]
        storage = StorageManager(index, tiers, env)
        # Creating the eviction policies
        DRAMLFUPolicy(dram, storage, env)

        sim = Simulation([trace], storage, env, log_file=os.path.join(output_folder, "latest7.log"),
                         progress_bar_enabled=False,
                         logs_enabled=True)
        print("Starting simulation")
        # start the simulation
        last_results7 = sim.run()
        last_results7 = f'{"#" * 10} Run LFU {"#" * 10}\n{last_results7}\n'

        for tier in tiers:
            cache_hit_ratio += tier.chr
        plot_y.append(cache_hit_ratio)
        try:
            with open(os.path.join(output_folder, "last_results7.txt"), "w") as f:
                f.write(last_results7)
        except:
            print(f'Error trying to write into a new file in output folder "{output_folder}"')
    if i == 7:  # 1 tiers: DRAM ARC
        cache_hit_ratio = 0
        plot_x.append("DRAM ARC")
        # Create the storage tiers
        dram = Tier(name="DRAM", max_size=5.12 * 10 ** 11, granularity=1, latency=1e-7, throughput=1.25e10,
                    target_occupation=0.6)

        # The storage manager is a utility object giving info on the tier ordering & default tier
        tiers = [dram]
        storage = StorageManager(index, tiers, env)
        # Creating the eviction policies
        ARCPolicy(dram, storage, env)

        sim = Simulation([trace], storage, env, log_file=os.path.join(output_folder, "latest8.log"),
                         progress_bar_enabled=False,
                         logs_enabled=True)
        print("Starting simulation")
        # start the simulation
        last_results8 = sim.run()
        last_results8 = f'{"#" * 10} Run ARC {"#" * 10}\n{last_results8}\n'

        for tier in tiers:
            cache_hit_ratio += tier.chr
        plot_y.append(cache_hit_ratio)
        try:
            with open(os.path.join(output_folder, "last_results8.txt"), "w") as f:
                f.write(last_results8)
        except:
            print(f'Error trying to write into a new file in output folder "{output_folder}"')

plt.figure(figsize=(15, 3))
plt.bar(plot_x, plot_y)
plt.suptitle('Cache Hit Ratio Plotting, Disk policy is with priority')
for a, b in zip(plot_x, plot_y):
    plt.text(a, b, str(b))
plt.show()
