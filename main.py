import sys
import os
import time
import numpy as np
import simpy
from traces.ndn_trace import NDNTrace
from simulation import Simulation
from storage_structures import Tier, StorageManager, Index
from policies.arcpolicy import ARCPolicy
from policies.lru_policy import LRUPolicy
from policies.lfu_policy import LFUPolicy
from policies.random_policy import RandPolicy
from policies.dram_lru_policy import DRAMLRUPolicy
from policies.dram_lfu_policy import DRAMLFUPolicy
from policies.dram_random_policy import DRAMRandPolicy
import matplotlib.pyplot as plt

# verify if the version of python is >3
from traces.trace_creator import TraceCreator

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

# create the trace using zipf law
traceCreator = TraceCreator("text.txt", 500, 1.2, 16777216)

# turn the trace into packets
trace = NDNTrace()
trace.gen_data()

remote_average_time_writing = 0
remote_average_time_reading = 0

for line in trace.data:
    if line[0] == 'd':
        remote_average_time_writing += int(line[5])
    else:
        remote_average_time_reading += int(line[5])

# log files
output_folder = "logs/<timestamp>"
output_folder = output_folder.replace('/', os.path.sep).replace("<timestamp>",
                                                                time.strftime("%a_%d_%b_%Y_%H-%M-%S", time.localtime()))
output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), output_folder))
try:
    os.makedirs(output_folder, exist_ok=True)
except:
    print(f'Error trying to create output folder "{output_folder}"')

# figure files
figure_folder = "figures/<timestamp>"
figure_folder = figure_folder.replace('/', os.path.sep).replace("<timestamp>",
                                                                time.strftime("%a_%d_%b_%Y_%H-%M-%S", time.localtime()))
figure_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), figure_folder))

try:
    os.makedirs(figure_folder, exist_ok=True)
except:
    print(f'Error trying to create output folder "{figure_folder}"')

plot_x = []  # 2tiers storage config str
plot_x1 = []  # 1tier storage config str
plot_y = []  # policy + chr -> value
plot_yrl = []  # local average_reading_time
plot_ywl = []  # local average_writing_time
plot_yrr = []  # remote average_reponseTime_reading
plot_ywr = []  # remote average_reponseTime_writing

dramTierPolicies = [ARCPolicy, DRAMLRUPolicy, DRAMLFUPolicy, DRAMRandPolicy]
diskTierPolicies = [LRUPolicy, LFUPolicy, RandPolicy]
# 2 tiers
for dramPolicy in dramTierPolicies:
    for diskPolicy in diskTierPolicies:
        name = dramPolicy.__name__ + "+" + diskPolicy.__name__
        name = name.replace('Policy', '')
        name = name.replace('DRAM', '')
        print("=====================================")
        print(name)
        # Init simpy env
        env = simpy.Environment()
        # create the index
        index = Index()
        # Create the storage tiers
        dram = Tier(name="DRAM", max_size=1 * 10 ** 9, granularity=1, latency=100e-6, throughput=1.25e10,
                    target_occupation=0.6)
        nvme = Tier(name="NVMe", max_size=1 * 10 ** 9, granularity=512, latency=1e-4, throughput=2e9,
                    target_occupation=0.9)
        # The storage manager is a utility object giving info on the tier ordering & default tier
        tiers = [dram, nvme]
        storage = StorageManager(index, tiers, env)
        dramPolicy(dram, storage, env)
        diskPolicy(nvme, storage, env)

        latest_filename = "latest" + name + ".log"
        sim = Simulation([trace], storage, env, log_file=os.path.join(output_folder, latest_filename),
                         progress_bar_enabled=False,
                         logs_enabled=True)
        print("Starting simulation")
        # start the simulation
        last_results_filename = "last_results" + name + ".txt"
        last_results = sim.run()
        last_results = f'{"#" * 10} Run {"#" * 10}\n{last_results}\n'

        try:
            with open(os.path.join(output_folder, last_results_filename), "w") as f:
                f.write(last_results)
        except:
            print(f'Error trying to write into a new file in output folder "{output_folder}"')
        plot_x.append(name)
        cache_hit_ratio = 0.0
        local_average_time_reading = 0.0
        local_average_time_writing = 0.0
        total_number_read = 0.0
        total_number_write = 0.0
        for onetier in tiers:
            cache_hit_ratio += onetier.chr
            total_number_read += onetier.number_of_reads
            total_number_write += onetier.number_of_write
            local_average_time_reading += onetier.time_spent_reading
            local_average_time_writing += onetier.time_spent_writing
        plot_y.append(0.0) if traceCreator.nb_interests == 0 else plot_y.append(
            round(cache_hit_ratio / traceCreator.nb_interests, 3))
        # plot_y.append(round(cache_hit_ratio / 360, 3))
        plot_yrl.append(round(local_average_time_reading / total_number_read, 3))
        plot_yrr.append(round(remote_average_time_reading / total_number_read, 3))
        plot_ywl.append(round(local_average_time_writing / total_number_write, 3))
        plot_ywr.append(round(remote_average_time_writing / total_number_write, 3))

# 1 tier
for dramPolicy in dramTierPolicies:
    name = dramPolicy.__name__
    name = name.replace('Policy', '')
    name = name.replace('DRAM', '')
    print("=====================================")
    print(name)
    # Init simpy env
    env = simpy.Environment()
    # create the index
    index = Index()
    # Create the storage tiers
    dram = Tier(name="DRAM", max_size=1 * 10 ** 9, granularity=1, latency=100e-6, throughput=1.25e10,
                target_occupation=0.6)
    # The storage manager is a utility object giving info on the tier ordering & default tier
    tiers = [dram]

    storage = StorageManager(index, tiers, env)

    dramPolicy(dram, storage, env)
    latest_filename = "latest" + name + ".log"
    sim = Simulation([trace], storage, env, log_file=os.path.join(output_folder, latest_filename),
                     progress_bar_enabled=False,
                     logs_enabled=True)

    print("Starting simulation")
    # start the simulation
    last_results_filename = "last_results" + name + ".txt"
    last_results = sim.run()
    last_results = f'{"#" * 10} Run {"#" * 10}\n{last_results}\n'

    try:
        with open(os.path.join(output_folder, last_results_filename), "w") as f:
            f.write(last_results)
    except:
        print(f'Error trying to write into a new file in output folder "{output_folder}"')
    plot_x.append(name)
    plot_y.append(0.0) if traceCreator.nb_interests == 0 else plot_y.append(
        round(dram.chr / traceCreator.nb_interests, 3))
    # plot_y.append(round(dram.chr / 360, 3))
    plot_yrl.append(0.0) if dram.number_of_reads == 0 else plot_yrl.append(
        round(dram.time_spent_reading / dram.number_of_reads, 3))
    plot_yrr.append(0.0) if dram.number_of_reads == 0 else plot_yrr.append(
        round(remote_average_time_reading / dram.number_of_reads, 3))
    plot_ywl.append(0.0) if dram.number_of_write == 0 else plot_ywl.append(
        round(dram.time_spent_writing / dram.number_of_write, 3))
    plot_ywr.append(0.0) if dram.number_of_write == 0 else plot_ywr.append(
        round(remote_average_time_writing / dram.number_of_write, 3))

plt.figure(figsize=(20, 4))
plt.bar(plot_x, plot_y)
plt.suptitle('Cache Hit Ratio Plotting, Disk policy is with priority')
for a, b in zip(plot_x, plot_y):
    plt.text(a, b, str(b))
try:
    plt.savefig(os.path.join(figure_folder, "chr.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

N = len(dramTierPolicies) * len(diskTierPolicies) + len(diskTierPolicies) + 1
ind = np.arange(N)
width = 0.25

plt.figure(figsize=(20, 10))
plt.bar(ind, plot_yrl, color='b', width=width, edgecolor='black', label='Local Time Reading')
plt.bar(ind + width, plot_yrr, color='g', width=width, edgecolor='black', label='Remote Time Reading')

plt.xlabel("Policy")
plt.ylabel("Time")
plt.title("Response Time Reading vs Time Reading")

plt.xticks(ind + width / 2, plot_x)
plt.legend()

try:
    plt.savefig(os.path.join(figure_folder, "reading_time.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

plt.figure(figsize=(20, 10))
plt.bar(ind, plot_ywl, color='b', width=width, edgecolor='black', label='Local Time Writing')
plt.bar(ind + width, plot_ywr, color='g', width=width, edgecolor='black', label='Remote Time Writing')

plt.xlabel("Policy")
plt.ylabel("Time")
plt.title("Response Time Writing vs Time Writing")

plt.xticks(ind + width / 2, plot_x)
plt.legend()
try:
    plt.savefig(os.path.join(figure_folder, "writing_time.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')
