import sys
import os
import time
import pandas as pd
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
from traces.trace_creator import TraceCreator

# time is in s
# size is in byte

# verify if the version of python is >3
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

slot_size = 9000
# create the trace using zipf law
# traceCreator = TraceCreator(N=34646, alpha=1.2, traffic_period=1460)

# turn the trace into packets
trace = NDNTrace()
trace.gen_data(trace_len_limit=20000)

remote_average_time_reading = 0
for line in trace.data:
    remote_average_time_reading += float(line[5])
remote_average_time_reading = remote_average_time_reading / 10 ** 9

nb_interests = len([line for line in trace.data if line[0] == 'i'])

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
plot_chr1 = []  # chr firt tier
plot_chr2 = []  # chr second tier
plot_yrl = []  # local average_reading_time
plot_ywl = []  # local average_writing_time
plot_yrr = []  # remote average_reponseTime_reading
plot_used_size_tier_1 = []
plot_used_size_tier_2 = []
plot_number_of_packets = []
plot_waisted_size_1 = []
plot_waisted_size_2 = []

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
        # dram : max_size=100 kilobytes, latency= 100ns, read_throughput= 40gbps write_throughput = 20gbps
        dram = Tier(name="DRAM", max_size=100000, granularity=1, latency=100e-7, read_throughput=5e9,
                    write_throughput=2.5e9, target_occupation=0.6)
        # nvme : max_size=1000 kilobytes, latency= 10000ns, read_throughput = 3gb/s write_throughput = 1gb/s
        nvme = Tier(name="NVMe", max_size=1000000, granularity=512, latency=100e-6, read_throughput=3.75e8,
                    write_throughput=1.25e8, target_occupation=1.0)
        # The storage manager is a utility object giving info on the tier ordering & default tier
        tiers = [dram, nvme]
        storage = StorageManager(index, tiers, env, slot_size)
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
        local_average_time_reading = 0.0
        local_average_time_writing = 0.0
        total_number_read = 0.0
        total_number_write = 0.0
        nb_packets = 0
        for onetier in tiers:
            nb_packets += onetier.number_of_packets
            total_number_read += onetier.number_of_reads
            total_number_write += onetier.number_of_write
            local_average_time_reading += onetier.time_spent_reading
            local_average_time_writing += onetier.time_spent_writing
        # number of packets plot
        plot_number_of_packets.append(nb_packets)
        # reading plot
        plot_yrl.append(0.0) if total_number_read == 0 else plot_yrl.append(dram.time_spent_reading / total_number_read)
        plot_yrr.append(0.0) if total_number_read == 0 else plot_yrr.append(
            remote_average_time_reading / total_number_read)
        # writing plot
        plot_ywl.append(0.0) if dram.number_of_write == 0 else plot_ywl.append(
            dram.time_spent_writing / total_number_write)
        # used size plots
        plot_used_size_tier_1.append(dram.used_size)
        plot_used_size_tier_2.append(nvme.used_size)
        # chr plots
        plot_chr1.append(0.0) if nb_interests == 0 else plot_chr1.append(dram.chr / nb_interests)
        plot_chr2.append(0.0) if nb_interests == 0 else plot_chr2.append(nvme.chr / nb_interests)
        # waisted size
        plot_waisted_size_1.append(dram.number_of_packets * slot_size - dram.used_size)
        plot_waisted_size_2.append(nvme.number_of_packets * slot_size - nvme.used_size)

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
    # dram : max_size=200 kilobytes, latency= 100ns, read_throughput= 40gbps write_throughput = 20gbps
    dram = Tier(name="DRAM", max_size=200000, granularity=1, latency=100e-7, read_throughput=5e9,
                write_throughput=2.5e9, target_occupation=0.6)
    # The storage manager is a utility object giving info on the tier ordering & default tier
    tiers = [dram]

    storage = StorageManager(index, tiers, env, slot_size)

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
    # number of packets plot
    plot_number_of_packets.append(dram.number_of_packets)
    # reading plot
    plot_yrl.append(0.0) if dram.number_of_reads == 0 else plot_yrl.append(
        dram.time_spent_reading / dram.number_of_reads)
    plot_yrr.append(0.0) if dram.number_of_reads == 0 else plot_yrr.append(
        remote_average_time_reading / dram.number_of_reads)
    # writing plot
    plot_ywl.append(0.0) if dram.number_of_write == 0 else plot_ywl.append(
        dram.time_spent_writing / dram.number_of_write)
    # used size plots
    plot_used_size_tier_1.append(dram.used_size)
    plot_used_size_tier_2.append(0.0)
    # chr plots
    plot_chr1.append(0.0) if nb_interests == 0 else plot_chr1.append(dram.chr / nb_interests)
    plot_chr2.append(0.0)
    # waisted size
    plot_waisted_size_1.append(dram.number_of_packets * slot_size - dram.used_size)
    plot_waisted_size_2.append(0.0)

# chr
df = pd.DataFrame(data={'DRAM': plot_chr1, 'DISK': plot_chr2})
df.index = plot_x
ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Storage configuration',
             ylabel='Cache Hit Ration')

for c in ax.containers:
    labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "chr.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# Reading Time
df = pd.DataFrame(data={'plot_x': plot_x, 'Local Time': plot_yrl, 'Remote Time': plot_yrr})
df = df[['plot_x', 'Local Time', 'Remote Time']]
df.set_index(['plot_x'], inplace=True)

ax = df.plot(kind='bar', figsize=(17, 6), rot=0, xlabel='Storage configuration',
             ylabel='Time (s)')
for c in ax.containers:
    labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "reading_time.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# Writing Time
df = pd.DataFrame(data={'Writing Time': plot_ywl})
df.index = plot_x

ax = df.plot(kind='bar', figsize=(17, 6), rot=0, xlabel='Storage configuration',
             ylabel='Time (s)')
for c in ax.containers:
    labels = [round(v.get_height() * 10 ** 5, 3) if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "writing_time.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# Used size per tier
df = pd.DataFrame(data={'DRAM': plot_used_size_tier_1, 'DISK': plot_used_size_tier_2})
df.index = plot_x

ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Storage configuration', ylabel='Used Size')
for c in ax.containers:
    labels = [v.get_height() if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "used_size.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# Number of packets
df = pd.DataFrame(data={'Number of Packets': plot_number_of_packets})
df.index = plot_x

ax = df.plot(kind='bar', figsize=(17, 6), rot=0, xlabel='Storage configuration',
             ylabel='Number of packets')
for c in ax.containers:
    labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "number_of_packets.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# waisted size
df = pd.DataFrame(data={'DRAM': plot_waisted_size_1, 'DISK': plot_waisted_size_2})
df.index = plot_x
ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Storage configuration',
             ylabel='Waisted size')

for c in ax.containers:
    labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "waisted_size.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')