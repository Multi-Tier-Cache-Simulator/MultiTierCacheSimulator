import os

import simpy
import importlib
from forwarder_structures.content_store.index import Index
from forwarder_structures.content_store.tier import Tier
from forwarder_structures.forwarder import Forwarder
from forwarder_structures.pit import PIT
from simulation import Simulation


def arc_main(name, policies: list[str], fromlist: list[str], slot_size, size_proportion, total_size, throughput, trace,
             output_folder, logs_enabled):
    for i in size_proportion:
        for j in throughput:
            for k in total_size:
                print("=====================================")
                print(name)

                # Init simpy env
                env = simpy.Environment()

                # create the index
                index = Index(env)

                # Create the Content Store tiers
                boss = Tier(name="BOSS", max_size=0, granularity=0, latency=0,
                            read_throughput=0, write_throughput=0, target_occupation=0)

                # dram: max_size=100kB, latency = 100ns = 1e-7s, read_throughput = 40GBPS, write_throughput = 20GBPS
                dram = Tier(name="DRAM", max_size=int(k * i), granularity=1, latency=1e-7,
                            read_throughput=40000000000, write_throughput=20000000000, target_occupation=1)

                # nvme: max_size=1000kB, latency = 10000ns, read_throughput = 3GBPS = 3Byte Per Nano Second
                # write_throughput = 1GBPS = 1Byte Per Nano Second
                ssd = Tier(name="SSD", max_size=int(k - k * i), granularity=512, latency=1e-5,
                           read_throughput=j * 1000000000, write_throughput=(j / 2) * 1000000000,
                           target_occupation=1.0)

                # disk = Tier(name="DISK", max_size=int(k - k * i - k*i/2), granularity=512, latency=1e-5,
                #             read_throughput=j * 1000000000, write_throughput=(j / 2) * 1000000000,
                #             target_occupation=1.0)

                tiers = [boss, dram, ssd]
                # tiers = [boss, dram, ssd, disk]

                # Create the PIT
                pit = PIT()

                # Create the forwarder
                forwarder = Forwarder(env, index, tiers, pit, slot_size, default_tier_index=1)

                # Assign the policies
                for module_name, policy, tier in zip(fromlist, policies, tiers):
                    module = importlib.import_module(module_name, package=None)
                    getattr(module, policy)(env, forwarder, tier)

                latest_filename = "latest" + name + ".log"
                sim = Simulation([trace], forwarder, env, log_file=os.path.join(output_folder, latest_filename),
                                 logs_enabled=logs_enabled)
                print("Starting simulation")
                last_results_filename = name + ".txt"
                last_results = sim.run()
                try:
                    with open(os.path.join(output_folder, last_results_filename), "a") as f:
                        f.write(last_results)
                except Exception as e:
                    print(
                        f'Error %s trying to write last_results into a new file in output folder "{output_folder}"' % e)


def policy_main(name, policy, slot_size, size_proportion, total_size, throughput, trace, output_folder, logs_enabled):
    for i in size_proportion:
        for j in throughput:
            for k in total_size:
                print("=====================================")
                print(name)

                # Init simpy env
                env = simpy.Environment()

                # create the index
                index = Index(env)

                # Create the Content Store tiers
                # dram: max_size=100kB, latency = 100ns = 1e-7s, read_throughput = 40GBPS, write_throughput = 20GBPS
                dram = Tier(name="DRAM", max_size=int(k * i), granularity=1, latency=1e-7,
                            read_throughput=40000000000, write_throughput=20000000000, target_occupation=1)

                # nvme: max_size=1000kB, latency = 10000ns, read_throughput = 3GBPS = 3Byte Per Nano Second
                # write_throughput = 1GBPS = 1Byte Per Nano Second
                ssd = Tier(name="SSD", max_size=int(k - k * i), granularity=512, latency=1e-5,
                           read_throughput=j * 1000000000, write_throughput=(j / 2) * 1000000000,
                           target_occupation=1.0)
                # disk = Tier(name="DISK", max_size=int(k - k * i - k*i/2), granularity=512, latency=1e-5,
                #             read_throughput=j * 1000000000, write_throughput=(j / 2) * 1000000000,
                #             target_occupation=1.0)

                tiers = [dram, ssd]
                # tiers = [dram, ssd, disk]

                # Create the PIT
                pit = PIT()

                # Create the forwarder
                forwarder = Forwarder(env, index, tiers, pit, slot_size, default_tier_index=0)

                # Assign the policies
                policy(env, forwarder, dram)
                policy(env, forwarder, ssd)
                # policy(env, forwarder, disk)

                latest_filename = "latest" + name + ".log"
                sim = Simulation([trace], forwarder, env, log_file=os.path.join(output_folder, latest_filename),
                                 logs_enabled=logs_enabled)
                print("Starting simulation")
                last_results_filename = name + ".txt"
                last_results = sim.run()
                try:
                    with open(os.path.join(output_folder, last_results_filename), "a") as f:
                        f.write(last_results)
                except Exception as e:
                    print(f'Error %s trying to write last_results into a new file in output folder "{output_folder}"' % e)
