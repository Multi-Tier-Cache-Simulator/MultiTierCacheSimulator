import json
import os
import time

import pandas as pd
from matplotlib import pyplot as plt


class Plot:
    def __init__(self, output_folder, slot_size, nb_interests, nb_high_priority,
                 nb_low_priority):
        # figure files
        figure_folder = "figures/<timestamp>"
        figure_folder = figure_folder.replace('/', os.path.sep).replace("<timestamp>",
                                                                        time.strftime("%a_%d_%b_%Y_%H-%M-%S",
                                                                                      time.localtime()))
        figure_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), figure_folder))

        try:
            os.makedirs(figure_folder, exist_ok=True)
        except Exception as e:
            print(f'Error %s trying to create output folder "{figure_folder}"' % e)

        # plots
        plot_content_store_config = []
        plot_penalty = []  # penalty

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
        plot_average_data_retrieval_time_ram = []  # average data retrieval time

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
        plot_read_throughput_disk = []  # read throughput of disk
        plot_average_data_retrieval_time_disk = []  # average data retrieval time
        # plot_average_hit_response_time = []  # rh
        # plot_average_miss_response_time = []  # rm

        # change directory to json files
        os.chdir(output_folder)
        result = list()
        for file in os.listdir():
            # Check whether file is in text format or not
            if file.endswith(".txt"):
                name = file[:file.__len__() - 4]
                file_path = f"{output_folder}/{file}"
                with open(file_path, 'r') as f:
                    plot_content_store_config.append(name)
                    result.extend(json.load(f))

        for line in result:
            if line['tier_name'] == 'DRAM':
                # average data retrieval time
                plot_average_data_retrieval_time_ram.append(line['average_data_retrieval_time'])

                # chr
                plot_cache_hit_ratio_ram.append(0.0) if nb_interests == 0 else plot_cache_hit_ratio_ram.append(
                    line['chr'] / nb_interests)

                # chr high priority content
                plot_cache_hit_ratio_hpc_ram.append(
                    0.0) if nb_high_priority == 0 else plot_cache_hit_ratio_hpc_ram.append(
                    line['chr_hpc'] / nb_high_priority)

                # chr low priority content
                plot_cache_hit_ratio_lpc_ram.append(
                    0.0) if nb_low_priority == 0 else plot_cache_hit_ratio_lpc_ram.append(
                    line['chr_lpc'] / nb_low_priority)

                # used size
                plot_used_size_ram.append(line['used_size'] / (line['max_size'] * line['target_occupation']))

                # waisted size
                plot_waisted_size_ram.append(
                    (line['number_of_packets'] * slot_size - line['used_size']) / (
                            line['max_size'] * line['target_occupation']))

                # number of read
                plot_number_read_ram.append(line['number_of_reads'])

                # number of write
                plot_number_write_ram.append(line['number_of_write'])

                # average high priority data retrieval time
                plot_high_p_data_retrieval_time_ram.append(
                    0.0) if nb_high_priority == 0 else plot_high_p_data_retrieval_time_ram.append(
                    line['high_p_data_retrieval_time'] / nb_high_priority)

                # average low priority data retrieval time
                plot_low_p_data_retrieval_time_ram.append(
                    0.0) if nb_low_priority == 0 else plot_low_p_data_retrieval_time_ram.append(
                    line['low_p_data_retrieval_time'] / nb_low_priority)

                # penalty
                plot_penalty.append(line['penalty'])

            if line['tier_name'] == 'NVMe':
                # average data retrieval time
                plot_average_data_retrieval_time_disk.append(line['average_data_retrieval_time'])

                # # average data retrieval time
                # plot_average_data_retrieval_time[-1] = (plot_average_data_retrieval_time[-1] + line[
                #     'average_data_retrieval_time']) / 2

                # read throughput
                plot_read_throughput_disk.append(line['read_throughput'])

                # chr
                plot_cache_hit_ratio_disk.append(0.0) if nb_interests == 0 else plot_cache_hit_ratio_disk.append(
                    line['chr'] / nb_interests)

                # chr high priority content
                plot_cache_hit_ratio_hpc_disk.append(
                    0.0) if nb_high_priority == 0 else plot_cache_hit_ratio_hpc_disk.append(
                    line['chr_hpc'] / nb_high_priority)

                # chr low priority content
                plot_cache_hit_ratio_lpc_disk.append(
                    0.0) if nb_low_priority == 0 else plot_cache_hit_ratio_lpc_disk.append(
                    line['chr_lpc'] / nb_low_priority)

                # used size
                plot_used_size_disk.append(line['used_size'] / (line['max_size'] * line['target_occupation']))

                # waisted size
                plot_waisted_size_disk.append(
                    (line['number_of_packets'] * slot_size - line['used_size']) / (
                            line['max_size'] * line['target_occupation']))

                # number of read
                plot_number_read_disk.append(line['number_of_reads'])

                # number of write
                plot_number_write_disk.append(line['number_of_write'])

                # average high priority data retrieval time
                plot_high_p_data_retrieval_time_disk.append(
                    0.0) if nb_high_priority == 0 else plot_high_p_data_retrieval_time_disk.append(
                    line['high_p_data_retrieval_time'] / nb_high_priority)

                # average low priority data retrieval time
                plot_low_p_data_retrieval_time_disk.append(
                    0.0) if nb_low_priority == 0 else plot_low_p_data_retrieval_time_disk.append(
                    line['low_p_data_retrieval_time'] / nb_low_priority)

        # ==================
        # chr total
        df = pd.DataFrame(data={'DRAM': plot_cache_hit_ratio_ram, 'Others': plot_cache_hit_ratio_disk})
        df.index = plot_content_store_config
        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='Cache Hit Ratio')

        for c in ax.containers:
            labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(os.path.join(figure_folder, plot_content_store_config[0] + "_chr.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

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
            plt.savefig(os.path.join(figure_folder, plot_content_store_config[0] + "chr_hpc.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

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
            plt.savefig(os.path.join(figure_folder, plot_content_store_config[0] + "_chr_lpc.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # ==================
        # Used size per tier
        df = pd.DataFrame(data={'DRAM': plot_used_size_ram, 'Others': plot_used_size_disk})
        df.index = plot_content_store_config

        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='Ratio Used Size')
        for c in ax.containers:
            labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(os.path.join(figure_folder, plot_content_store_config[0] + "_used_size.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # ==================
        # waisted size
        df = pd.DataFrame(data={'DRAM': plot_waisted_size_ram, 'Others': plot_waisted_size_disk})
        df.index = plot_content_store_config
        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='Waisted size (ko)')

        for c in ax.containers:
            labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(os.path.join(figure_folder, plot_content_store_config[0] + "_waisted_size.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # ==================
        # Number of read
        df = pd.DataFrame(data={'DRAM': plot_number_read_ram, 'Others': plot_number_read_disk})
        df.index = plot_content_store_config

        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='Number of Read')
        for c in ax.containers:
            labels = [v.get_height() if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(os.path.join(figure_folder, plot_content_store_config[0] + "_read_number.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # ==================
        # Number of write
        df = pd.DataFrame(data={'DRAM': plot_number_write_ram, 'Others': plot_number_write_disk})
        df.index = plot_content_store_config

        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='Number of Write')
        for c in ax.containers:
            labels = [v.get_height() if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(os.path.join(figure_folder, plot_content_store_config[0] + "_write_number.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # ==================
        # high priority data retrieval time
        df = pd.DataFrame(
            data={'DRAM': plot_high_p_data_retrieval_time_ram, 'Others': plot_high_p_data_retrieval_time_disk})
        df.index = plot_content_store_config

        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='High Priority Data Retrieval Time (ns)')
        for c in ax.containers:
            labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(
                os.path.join(figure_folder, plot_content_store_config[0] + "_high_priority_data_retrieval_time.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # ==================
        # low priority data retrieval time
        df = pd.DataFrame(
            data={'DRAM': plot_low_p_data_retrieval_time_ram, 'Others': plot_low_p_data_retrieval_time_disk})
        df.index = plot_content_store_config

        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='Low Priority Data Retrieval Time (ns)')
        for c in ax.containers:
            labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(
                os.path.join(figure_folder, plot_content_store_config[0] + "_low_priority_data_retrieval_time.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # ==================
        # data retrieval time
        df = pd.DataFrame(
            data={'DRAM': plot_average_data_retrieval_time_ram, 'DISK': plot_average_data_retrieval_time_disk})
        df.index = plot_content_store_config

        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='Data Retrieval Time (ns)')
        for c in ax.containers:
            labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(os.path.join(figure_folder, plot_content_store_config[0] + "_data_retrieval_time_per_tier.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # ==================
        # penalty
        df = pd.DataFrame(data={'penalty': plot_penalty})
        df.index = plot_content_store_config

        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='Penalty ($)')
        for c in ax.containers:
            labels = [v.get_height() if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(os.path.join(figure_folder, plot_content_store_config[0] + "_penalty.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # # ==================
        # # read throughput disk
        # df = pd.DataFrame(data={'Data Retrieval Time ': plot_average_data_retrieval_time,
        #                         'Average Network Response Time': [0.3] * len(plot_average_data_retrieval_time),
        #                         'Average Node Access Time': [0.001] * len(plot_average_data_retrieval_time)})
        # df.index = plot_read_throughput_disk
        #
        # ax = df.plot(figsize=(17, 6), rot=0, xlabel='Read Throughput Disk (GBPS)',
        #              ylabel='Time (s)')
        # for c in ax.containers:
        #     labels = [v.get_height() if v.get_height() > 0 else '' for v in c]
        #     ax.bar_label(c, labels=labels, label_type='center')
        #
        # try: plt.savefig(os.path.join(figure_folder, plot_content_store_config[
        # 0]+"_retrieval_time_per_read_throughput_disk.png")) except Exception as e: print(f'Error %s trying to write
        # into a new file in output folder "{figure_folder}"' % e)
