import sys
import os
import time
import simpy
import pandas as pd
import matplotlib.pyplot as plt
from simulation import Simulation
from traces.ndn_trace import NDNTrace
from forwarder_structures import Tier, Forwarder, Index, PIT
from policies.DRAM.arcpolicy import ARCPolicy
from policies.DRAM.dram_lru_policy import DRAMLRUPolicy
from policies.DRAM.dram_lfu_cache import DRAMLFUPolicy
from policies.DRAM.dram_random_policy import DRAMRandPolicy
from policies.DISK.lru_policy import LRUPolicy
from policies.DISK.lfu_policy import LFUPolicy
from policies.DISK.random_policy import RandPolicy

# time is in nanos
# size is in byte

# verify if the version of python is >3
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

# slot size allocation in dram and nvme
slot_size = 9000

# turn the trace into packets
trace = NDNTrace()
trace.gen_data()
# trace.gen_data(trace_len_limit=2000)

# number of requests on high priority content
nb_high_priority = [line for line in trace.data if line[4] == 'h'].__len__()
# number of requests on low priority content
nb_low_priority = [line for line in trace.data if line[4] == 'l'].__len__()
# total number of requests
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
plot_number_read_ram = []  # number of read
plot_number_write_ram = []  # number of write
plot_high_p_data_retrieval_time_ram = []  # high priority data retrieval time
plot_low_p_data_retrieval_time_ram = []  # low priority data retrieval time
plot_local_average_reading_time_ram = []  # local average reading time
plot_local_average_writing_time_ram = []  # local average writing time

# disk
plot_cache_hit_ratio_disk = []  # chr
plot_cache_hit_ratio_hpc_disk = []  # chr high priority content
plot_cache_hit_ratio_lpc_disk = []  # chr low priority content
plot_used_size_disk = []  # used size
plot_waisted_size_disk = []  # waisted size
plot_number_read_disk = []  # number of read
plot_number_write_disk = []  # number of write
plot_high_p_data_retrieval_time_disk = []  # high priority data retrieval time
plot_low_p_data_retrieval_time_disk = []  # low priority data retrieval time
plot_local_average_reading_time_disk = []  # local average reading time
plot_local_average_writing_time_disk = []  # local average writing time

# available policies
dramTierPolicies = [ARCPolicy, DRAMLRUPolicy, DRAMLFUPolicy, DRAMRandPolicy]
diskTierPolicies = [LRUPolicy, LFUPolicy, RandPolicy]
# dramTierPolicies = [ARCPolicy]
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
        # nvme: max_size=1000kB, latency = 10000ns, read_throughput = 3GBPS = 3Byte Per Nano Second
        # write_throughput = 1GBPS = 1Byte Per Nano Second
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
        for oneTier in tiers:
            local_average_time_reading += oneTier.time_spent_reading
            local_average_time_writing += oneTier.time_spent_writing

        # Plotting time
        # CS config
        plot_content_store_config.append(name)

        # ram
        # chr
        plot_cache_hit_ratio_ram.append(0.0) if nb_interests == 0 else plot_cache_hit_ratio_ram.append(
            dram.chr / nb_interests)
        # chr high priority content
        plot_cache_hit_ratio_hpc_ram.append(0.0) if nb_high_priority == 0 else plot_cache_hit_ratio_hpc_ram.append(
            dram.chr_hpc / nb_high_priority)
        # chr low priority content
        plot_cache_hit_ratio_lpc_ram.append(0.0) if nb_low_priority == 0 else plot_cache_hit_ratio_lpc_ram.append(
            dram.chr_lpc / nb_low_priority)
        # used size
        plot_used_size_ram.append(dram.used_size / (dram.max_size * dram.target_occupation))
        # waisted size
        plot_waisted_size_ram.append(
            (dram.number_of_packets * slot_size - dram.used_size) / (dram.max_size * dram.target_occupation))
        # number of read
        plot_number_read_ram.append(dram.number_of_reads)
        # number of write
        plot_number_write_ram.append(dram.number_of_write)
        # average high priority data retrieval time
        plot_high_p_data_retrieval_time_ram.append(
            0.0) if nb_high_priority == 0 else plot_high_p_data_retrieval_time_ram.append(
            float(dram.high_p_data_retrieval_time / nb_high_priority))
        # average low priority data retrieval time
        plot_low_p_data_retrieval_time_ram.append(
            0.0) if nb_low_priority == 0 else plot_low_p_data_retrieval_time_ram.append(
            float(dram.low_p_data_retrieval_time / nb_low_priority))
        # local average reading time
        plot_local_average_reading_time_ram.append(
            0.0) if dram.number_of_reads == 0 else plot_local_average_reading_time_ram.append(
            dram.time_spent_reading / dram.number_of_reads)
        # local average writing time
        plot_local_average_writing_time_ram.append(
            0.0) if dram.number_of_write == 0 else plot_local_average_writing_time_ram.append(
            dram.time_spent_writing / dram.number_of_write)

        # disk
        # chr
        plot_cache_hit_ratio_disk.append(0.0) if nb_interests == 0 else plot_cache_hit_ratio_disk.append(
            nvme.chr / nb_interests)
        # chr high priority content
        plot_cache_hit_ratio_hpc_disk.append(0.0) if nb_high_priority == 0 else plot_cache_hit_ratio_hpc_disk.append(
            nvme.chr_hpc / nb_high_priority)
        # chr low priority content
        plot_cache_hit_ratio_lpc_disk.append(0.0) if nb_low_priority == 0 else plot_cache_hit_ratio_lpc_disk.append(
            nvme.chr_lpc / nb_low_priority)
        # used size
        plot_used_size_disk.append(nvme.used_size / (nvme.max_size * nvme.target_occupation))
        # waisted size
        plot_waisted_size_disk.append(
            (nvme.number_of_packets * slot_size - nvme.used_size) / (nvme.max_size * nvme.target_occupation))
        # number of read
        plot_number_read_disk.append(nvme.number_of_reads)
        # number of write
        plot_number_write_disk.append(nvme.number_of_write)
        # average high priority data retrieval time
        plot_high_p_data_retrieval_time_disk.append(
            0.0) if nb_high_priority == 0 else plot_high_p_data_retrieval_time_disk.append(
            float(nvme.high_p_data_retrieval_time / nb_high_priority))
        # average low priority data retrieval time
        plot_low_p_data_retrieval_time_disk.append(
            0.0) if nb_low_priority == 0 else plot_low_p_data_retrieval_time_disk.append(
            float(nvme.low_p_data_retrieval_time / nb_low_priority))
        # local average reading time
        plot_local_average_reading_time_disk.append(
            0.0) if nvme.number_of_reads == 0 else plot_local_average_reading_time_disk.append(
            nvme.time_spent_reading / nvme.number_of_reads)
        # local average writing time
        plot_local_average_writing_time_disk.append(
            0.0) if nvme.number_of_write == 0 else plot_local_average_writing_time_disk.append(
            nvme.time_spent_writing / nvme.number_of_write)

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
        dram.chr / nb_interests)
    # chr high priority content
    plot_cache_hit_ratio_hpc_ram.append(0.0) if nb_high_priority == 0 else plot_cache_hit_ratio_hpc_ram.append(
        dram.chr_hpc / nb_high_priority)
    # chr low priority content
    plot_cache_hit_ratio_lpc_ram.append(0.0) if nb_low_priority == 0 else plot_cache_hit_ratio_lpc_ram.append(
        dram.chr_lpc / nb_low_priority)
    # used size
    plot_used_size_ram.append(dram.used_size / (dram.max_size * dram.target_occupation))
    # waisted size
    plot_waisted_size_ram.append(
        (dram.number_of_packets * slot_size - dram.used_size) / (dram.max_size * dram.target_occupation))
    # number of read
    plot_number_read_ram.append(dram.number_of_reads)
    # number of write
    plot_number_write_ram.append(dram.number_of_write)
    # average high priority data retrieval time
    plot_high_p_data_retrieval_time_ram.append(
        0.0) if nb_high_priority == 0 else plot_high_p_data_retrieval_time_ram.append(
        float(dram.high_p_data_retrieval_time / nb_high_priority))
    # average low priority data retrieval time
    plot_low_p_data_retrieval_time_ram.append(
        0.0) if nb_low_priority == 0 else plot_low_p_data_retrieval_time_ram.append(
        float(dram.low_p_data_retrieval_time / nb_low_priority))
    # local average reading time
    plot_local_average_reading_time_ram.append(
        0.0) if nb_interests == 0 else plot_local_average_reading_time_ram.append(
        dram.time_spent_reading / dram.number_of_reads)
    # local average writing time
    plot_local_average_writing_time_ram.append(
        0.0) if nb_interests == 0 else plot_local_average_writing_time_ram.append(
        dram.time_spent_writing / dram.number_of_write)

    # disk
    # chr
    plot_cache_hit_ratio_disk.append(0.0)
    # chr high priority content
    plot_cache_hit_ratio_hpc_disk.append(0.0)
    # chr low priority content
    plot_cache_hit_ratio_lpc_disk.append(0.0)
    # used size
    plot_used_size_disk.append(0.0)
    # waisted size
    plot_waisted_size_disk.append(0.0)
    # number of read
    plot_number_read_disk.append(0)
    # number of writes
    plot_number_write_disk.append(0)
    # average high priority data retrieval time
    plot_high_p_data_retrieval_time_disk.append(0.0)
    # average low priority data retrieval time
    plot_low_p_data_retrieval_time_disk.append(0.0)
    # local average reading time
    plot_local_average_reading_time_disk.append(0.0)
    # local average writing time
    plot_local_average_writing_time_disk.append(0.0)

# ==================
# chr total
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

# ==================
# chr high priority per tier
df = pd.DataFrame({'DRAM_H': plot_cache_hit_ratio_hpc_ram, 'DISK_H': plot_cache_hit_ratio_hpc_disk})
df.index = plot_content_store_config

ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
             ylabel='High Priority Cache Hit Ratio')
for c in ax.containers:
    labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "chr_hpc.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# ==================
# chr low priority per tier
df = pd.DataFrame({'DRAM_L': plot_cache_hit_ratio_lpc_ram, 'DISK_L': plot_cache_hit_ratio_lpc_disk})
df.index = plot_content_store_config

ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
             ylabel='Low Priority Cache Hit Ratio')
for c in ax.containers:
    labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "chr_lpc.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# ==================
# Used size per tier
df = pd.DataFrame(data={'DRAM': plot_used_size_ram, 'DISK': plot_used_size_disk})
df.index = plot_content_store_config

ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
             ylabel='Ratio Used Size')
for c in ax.containers:
    labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "used_size.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# ==================
# waisted size
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

# ==================
# Number of read
df = pd.DataFrame(data={'DRAM': plot_number_read_ram, 'DISK': plot_number_read_disk})
df.index = plot_content_store_config

ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
             ylabel='Number of Read')
for c in ax.containers:
    labels = [v.get_height() if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "read_number.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# ==================
# Number of write
df = pd.DataFrame(data={'DRAM': plot_number_write_ram, 'DISK': plot_number_write_disk})
df.index = plot_content_store_config

ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
             ylabel='Number of Write')
for c in ax.containers:
    labels = [v.get_height() if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "write_number.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# ==================
# high priority data retrieval time
df = pd.DataFrame(data={'DRAM': plot_high_p_data_retrieval_time_ram, 'DISK': plot_high_p_data_retrieval_time_disk})
df.index = plot_content_store_config

ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
             ylabel='High Priority Data Retrieval Time (ns)')
for c in ax.containers:
    labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "high_priority_data_retrieval_time.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# ==================
# low priority data retrieval time
df = pd.DataFrame(data={'DRAM': plot_low_p_data_retrieval_time_ram, 'DISK': plot_low_p_data_retrieval_time_disk})
df.index = plot_content_store_config

ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
             ylabel='Low Priority Data Retrieval Time (ns)')
for c in ax.containers:
    labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "low_priority_data_retrieval_time.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# ==================
# Reading Time
df = pd.DataFrame(data={'DRAM': plot_local_average_reading_time_ram, 'DISK': plot_local_average_reading_time_disk})
df.index = plot_content_store_config

ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
             ylabel='Reading Time (ns)')
for c in ax.containers:
    labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "reading_time.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')

# ==================
# Writing Time
df = pd.DataFrame(data={'DRAM': plot_local_average_writing_time_ram, 'DISK': plot_local_average_writing_time_disk})
df.index = plot_content_store_config

ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
             ylabel='Writing Time (ns)')
for c in ax.containers:
    labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
    ax.bar_label(c, labels=labels, label_type='center')

try:
    plt.savefig(os.path.join(figure_folder, "writing_time.png"))
except:
    print(f'Error trying to write into a new file in output folder "{figure_folder}"')
