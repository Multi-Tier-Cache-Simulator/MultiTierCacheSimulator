import sys
import os
import time
import simpy
import pandas as pd
import matplotlib.pyplot as plt
from simulation import Simulation
from traces.ndn_trace import NDNTrace
from forwarder_structures import Tier, Forwarder, Index, PIT
from policies.arcpolicy import ARCPolicy
from policies.dram_lru_policy import DRAMLRUPolicy
from policies.dram_random_policy import DRAMRandPolicy
from policies.dram_lfu_cache import DRAMLFUPolicy
from policies.lru_policy import LRUPolicy
from policies.random_policy import RandPolicy
from policies.lfu_policy import LFUPolicy

# time is in nanos
# size is in byte

# verify if the version of python is >3
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

# slot size allocation in dram and nvme
slot_size = 9000

# create the trace using
# zipf = 1.2
# poisson = 0.1 --> 1 request every 1ms
# size in range 100 and 8000 octets
# data rtt in range 10ms to 200ms
# interest lifetime = 10ms
# traffic period = 2880m = 48h
# traceCreator = TraceCreator(NUniqueItems=3000, HighPriorityContentPourcentage=0.5,
#                             ZipfAlpha=1.2, PoissonLambda=0.1, LossProbability=0.0,
#                             MinDataSize=100, MaxDataSize=8000,
#                             MinDataRTT=10000000, MaxDataRTT=200000000,
#                             InterestLifetime=1000000,
#                             traffic_period=2880)

# turn the trace into packets
trace = NDNTrace()
trace.gen_data(trace_len_limit=2000)

# number of requests on high priority content
nb_high_priority = [line for line in trace.data if line[4] == 'h'].__len__()
# number of requests on low priority content
nb_low_priority = [line for line in trace.data if line[4] == 'l'].__len__()
# number of requests
nb_interests = len(trace.data)

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

# plots
# CS config
plot_content_store_config = []  # Content Store config str
# ram
plot_cache_hit_ratio_ram = []  # chr
plot_cache_hit_ratio_hpc_ram = []  # chr high priority content
plot_cache_hit_ratio_lpc_ram = []  # chr low priority content
plot_used_size_ram = []  # used size
plot_waisted_size_ram = []  # waisted size
# disk
plot_cache_hit_ratio_disk = []  # chr
plot_cache_hit_ratio_hpc_disk = []  # chr high priority content
plot_cache_hit_ratio_lpc_disk = []  # chr low priority content
plot_used_size_disk = []  # used size
plot_waisted_size_disk = []  # waisted size
plot_number_write_disk = []  # number of write to disk
# time
plot_local_average_reading_time = []  # local average reading time
plot_local_average_writing_time = []  # local average writing time
plot_high_p_data_retrieval_time = []
plot_low_p_data_retrieval_time = []

# available policies
dramTierPolicies = [ARCPolicy, DRAMLRUPolicy, DRAMLFUPolicy, DRAMRandPolicy]
diskTierPolicies = [LRUPolicy, LFUPolicy, RandPolicy]
# dramTierPolicies = [DRAMLFUPolicy]
# diskTierPolicies = [LRUPolicy]
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
        # Create the Content Store tiers
        # dram: max_size=100kB, latency = 100ns, read_throughput = 40GBPS, write_throughput = 20GBPS
        dram = Tier(name="DRAM", max_size=100000, granularity=1, latency=100, read_throughput=40,
                    write_throughput=20, target_occupation=0.6)
        # nvme: max_size=1000kB, latency = 10000ns, read_throughput = 3GBPS = 3BPNS write_throughput = 1GBPS = 1BPNS
        nvme = Tier(name="NVMe", max_size=1000000, granularity=512, latency=10000, read_throughput=3,
                    write_throughput=1, target_occupation=1.0)
        tiers = [dram, nvme]
        # Create the PIT
        pit = PIT()
        # Create the forwarder
        forwarder = Forwarder(env, index, tiers, pit, slot_size)
        # Assign the policies
        dramPolicy(env, forwarder, dram)
        diskPolicy(env, forwarder, nvme)

        latest_filename = "latest" + name + ".log"
        sim = Simulation([trace], forwarder, env, log_file=os.path.join(output_folder, latest_filename),
                         logs_enabled=True)
        print("Starting simulation")
        last_results_filename = "last_results" + name + ".txt"
        last_results = sim.run()
        last_results = f'{"#" * 10} Run {"#" * 10}\n{last_results}\n'

        try:
            with open(os.path.join(output_folder, last_results_filename), "w") as f:
                f.write(last_results)
        except:
            print(f'Error trying to write into a new file in output folder "{output_folder}"')

        local_average_time_reading = 0.0
        local_average_time_writing = 0.0
        total_number_read = 0.0
        total_number_write = 0.0
        high_p_data_retrieval_time = 0
        low_p_data_retrieval_time = 0
        for oneTier in tiers:
            total_number_read += oneTier.number_of_reads
            total_number_write += oneTier.number_of_write
            local_average_time_reading += oneTier.time_spent_reading
            local_average_time_writing += oneTier.time_spent_writing
            low_p_data_retrieval_time += oneTier.low_p_data_retrieval_time
            high_p_data_retrieval_time += oneTier.high_p_data_retrieval_time

        # Plotting time
        # CS config
        plot_content_store_config.append(name)

        # ram
        plot_cache_hit_ratio_ram.append(0.0) if nb_interests == 0 else plot_cache_hit_ratio_ram.append(
            dram.chr / nb_interests)  # chr
        plot_cache_hit_ratio_hpc_ram.append(0.0) if nb_high_priority == 0 else plot_cache_hit_ratio_hpc_ram.append(
            dram.chrhpc / nb_high_priority)  # chr high priority content
        plot_cache_hit_ratio_lpc_ram.append(0.0) if nb_low_priority == 0 else plot_cache_hit_ratio_lpc_ram.append(
            dram.chrlpc / nb_low_priority)  # chr low priority content
        plot_used_size_ram.append(dram.used_size)  # used size
        plot_waisted_size_ram.append(dram.number_of_packets * slot_size - dram.used_size)  # waisted size

        # disk
        plot_cache_hit_ratio_disk.append(0.0) if nb_interests == 0 else plot_cache_hit_ratio_disk.append(
            nvme.chr / nb_interests)  # chr
        plot_cache_hit_ratio_hpc_disk.append(0.0) if nb_high_priority == 0 else plot_cache_hit_ratio_hpc_disk.append(
            nvme.chrhpc / nb_high_priority)  # chr high priority content
        plot_cache_hit_ratio_lpc_disk.append(0.0) if nb_low_priority == 0 else plot_cache_hit_ratio_lpc_disk.append(
            nvme.chrlpc / nb_low_priority)  # chr low priority content
        plot_used_size_disk.append(nvme.used_size)  # used size
        plot_waisted_size_disk.append(nvme.number_of_packets * slot_size - nvme.used_size)  # waisted size
        plot_number_write_disk.append(nvme.number_of_write)
        # time
        plot_local_average_reading_time.append(
            0.0) if total_number_read == 0 else plot_local_average_reading_time.append(
            dram.time_spent_reading / total_number_read)  # reading plot
        plot_local_average_writing_time.append(
            0.0) if dram.number_of_write == 0 else plot_local_average_writing_time.append(
            dram.time_spent_writing / total_number_write)  # writing plot
        plot_high_p_data_retrieval_time.append(0.0) if nb_high_priority == 0 else plot_high_p_data_retrieval_time.append(
            high_p_data_retrieval_time / nb_high_priority)  # average high priority data retrieval time
        plot_low_p_data_retrieval_time.append(0.0) if nb_low_priority == 0 else plot_low_p_data_retrieval_time.append(
            low_p_data_retrieval_time / nb_low_priority)  # average low priority data retrieval time

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
    # Create the Content Store tiers
    # dram: max_size=100kB, latency = 100ns, read_throughput = 40GBPS, write_throughput = 20GBPS
    dram = Tier(name="DRAM", max_size=100000, granularity=1, latency=100, read_throughput=40,
                write_throughput=20, target_occupation=0.6)
    tiers = [dram]
    # Create the PIT
    pit = PIT()
    # Create the forwarder
    forwarder = Forwarder(env, index, tiers, pit, slot_size)
    # Assign the policy
    dramPolicy(env, forwarder, dram)

    latest_filename = "latest" + name + ".log"
    sim = Simulation([trace], forwarder, env, log_file=os.path.join(output_folder, latest_filename),
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

    # Plotting time
    # CS config
    plot_content_store_config.append(name)

    # ram
    plot_cache_hit_ratio_ram.append(0.0) if nb_interests == 0 else plot_cache_hit_ratio_ram.append(
        dram.chr / nb_interests)  # chr
    plot_cache_hit_ratio_hpc_ram.append(0.0) if nb_low_priority == 0 else plot_cache_hit_ratio_hpc_ram.append(
        dram.chrhpc / nb_high_priority)  # chr high priority content
    plot_cache_hit_ratio_lpc_ram.append(0.0) if nb_low_priority == 0 else plot_cache_hit_ratio_lpc_ram.append(
        dram.chrlpc / nb_low_priority)  # chr low priority content
    plot_used_size_ram.append(dram.used_size)  # used size
    plot_waisted_size_ram.append(dram.number_of_packets * slot_size - dram.used_size)  # waisted size

    # disk
    plot_cache_hit_ratio_disk.append(0.0)  # chr
    plot_cache_hit_ratio_hpc_disk.append(0.0)  # chr high priority content
    plot_cache_hit_ratio_lpc_disk.append(0.0)  # chr low priority content
    plot_used_size_disk.append(0.0)  # used size
    plot_waisted_size_disk.append(0.0)  # waisted size
    plot_number_write_disk.append(0)

    # time
    plot_local_average_reading_time.append(
        0.0) if dram.number_of_reads == 0 else plot_local_average_reading_time.append(
        dram.time_spent_reading / dram.number_of_reads)  # reading plot

    plot_local_average_writing_time.append(
        0.0) if dram.number_of_write == 0 else plot_local_average_writing_time.append(
        dram.time_spent_writing / dram.number_of_write)  # writing plot
    plot_high_p_data_retrieval_time.append(0.0) if nb_high_priority == 0 else plot_high_p_data_retrieval_time.append(
        dram.high_p_data_retrieval_time / nb_high_priority)  # average high priority data retrieval time
    plot_low_p_data_retrieval_time.append(0.0) if nb_low_priority == 0 else plot_low_p_data_retrieval_time.append(
        dram.low_p_data_retrieval_time / nb_low_priority)  # average low priority data retrieval time

# chr
df = pd.DataFrame(data={'DRAM': plot_cache_hit_ratio_ram, 'DISK': plot_cache_hit_ratio_disk})
df.index = plot_content_store_config
ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
             ylabel='Cache Hit Ratio')

for c in ax.containers:
    labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "chr.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# chr per priority per tier
df = pd.DataFrame({'RAM_L': plot_cache_hit_ratio_lpc_ram, 'RAM_H': plot_cache_hit_ratio_hpc_ram,
                   'DISK_L': plot_cache_hit_ratio_lpc_disk, 'DISK_H': plot_cache_hit_ratio_hpc_disk})

ax = df[['RAM_L', 'RAM_H']].plot.bar(stacked=True, figsize=(17, 6), xlabel='Content Store configuration',
                                     ylabel='Cache Hit Ratio', position=0, color=['green', 'red'], width=0.3)
df[['DISK_L', 'DISK_H']].plot.bar(stacked=True, sharex=True, ax=ax, position=1, width=0.3)

ax.set_xticklabels(plot_content_store_config, rotation=0)

for c in ax.containers:
    labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "chrlhpcdr.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# Reading Time
plot_local_average_reading_time = [float(plot_local_average_reading_time[i]) / 6 ** 10 for i in
                                   range(plot_local_average_reading_time.__len__())]
df = pd.DataFrame(data={'Reading Time': plot_local_average_reading_time})
df.index = plot_content_store_config

ax = df.plot(kind='bar', figsize=(17, 6), rot=0, xlabel='Content Store configuration',
             ylabel='Time (m)')
for c in ax.containers:
    labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "reading_time.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# Writing Time
plot_local_average_writing_time = [float(plot_local_average_writing_time[i]) / 10 ** 6 for i in
                                   range(plot_local_average_writing_time.__len__())]
df = pd.DataFrame(data={'Writing Time': plot_local_average_writing_time})
df.index = plot_content_store_config

ax = df.plot(kind='bar', figsize=(17, 6), rot=0, xlabel='Content Store configuration',
             ylabel='Time (ms)')
for c in ax.containers:
    labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "writing_time.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# Used size per tier
plot_used_size_ram = [float(plot_used_size_ram[i]) / 10 ** 3 for i in
                      range(plot_used_size_ram.__len__())]
plot_used_size_disk = [float(plot_used_size_disk[i]) / 10 ** 3 for i in
                       range(plot_used_size_disk.__len__())]
df = pd.DataFrame(data={'DRAM': plot_used_size_ram, 'DISK': plot_used_size_disk})
df.index = plot_content_store_config

ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration', ylabel='Used Size (ko)')
for c in ax.containers:
    labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "used_size.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# waisted size
plot_waisted_size_ram = [float(plot_waisted_size_ram[i]) / 10 ** 3 for i in
                         range(plot_waisted_size_ram.__len__())]
plot_waisted_size_disk = [float(plot_waisted_size_disk[i]) / 10 ** 3 for i in
                          range(plot_waisted_size_disk.__len__())]
df = pd.DataFrame(data={'DRAM': plot_waisted_size_ram, 'DISK': plot_waisted_size_disk})
df.index = plot_content_store_config
ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
             ylabel='Waisted size (ko)')

for c in ax.containers:
    labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "waisted_size.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# Number of write to disk
df = pd.DataFrame(data={'Number of Write to Disk': plot_number_write_disk})
df.index = plot_content_store_config

ax = df.plot(kind='bar', figsize=(17, 6), rot=0, xlabel='Content Store configuration',
             ylabel='Number of Write to Disk')
for c in ax.containers:
    labels = [v.get_height() if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "disk_writing_number.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# Low and high priority data retrieval time
plot_high_p_data_retrieval_time = [float(plot_high_p_data_retrieval_time[i]) / 10 ** 6 for i in
                                   range(plot_high_p_data_retrieval_time.__len__())]
plot_low_p_data_retrieval_time = [float(plot_low_p_data_retrieval_time[i]) / 10 ** 6 for i in
                                  range(plot_low_p_data_retrieval_time.__len__())]

df = pd.DataFrame(data={'Low': plot_low_p_data_retrieval_time, 'High': plot_high_p_data_retrieval_time})
df.index = plot_content_store_config

ax = df.plot(kind='bar', stacked=False, figsize=(17, 6), rot=0, xlabel='Content Store configuration', ylabel='Time (ms)')
for c in ax.containers:
    labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "data_retrieval_time.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')
