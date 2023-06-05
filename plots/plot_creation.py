import json
import os
import time

import pandas as pd
from matplotlib import pyplot as plt


class Plot:
    def __init__(self, output_folder, slot_size):
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
        plot_penalty_hpc = []  # penalty of cache miss high priority content
        plot_penalty_lpc = []  # penalty of cache miss low priority contetn

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

        # ssd
        plot_cache_hit_ratio_ssd = []  # chr
        plot_cache_hit_ratio_hpc_ssd = []  # chr high priority content
        plot_cache_hit_ratio_lpc_ssd = []  # chr low priority content
        plot_used_size_ssd = []  # used size
        plot_waisted_size_ssd = []  # waisted size
        plot_number_read_ssd = []  # number of read
        plot_number_write_ssd = []  # number of write
        plot_high_p_data_retrieval_time_ssd = []  # high priority data retrieval time
        plot_low_p_data_retrieval_time_ssd = []  # low priority data retrieval time
        plot_read_throughput_ssd = []  # read throughput of ssd
        plot_average_data_retrieval_time_ssd = []  # average data retrieval time

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
                # chr
                plot_cache_hit_ratio_ram.append(line['cache hit ratio'])
                # chr high priority content
                plot_cache_hit_ratio_hpc_ram.append(line['cache hit ratio hpc'])
                # chr low priority content
                plot_cache_hit_ratio_lpc_ram.append(line['cache hit ratio lpc'])
                # average data retrieval time
                plot_average_data_retrieval_time_ram.append(line['avg_v_retrieval_time'])
                # average high priority data retrieval time
                plot_high_p_data_retrieval_time_ram.append(line['avg_hpc_retrieval_time'])
                # average low priority data retrieval time
                plot_low_p_data_retrieval_time_ram.append(line['avg_lpc_retrieval_time'])
                # penalty
                plot_penalty_hpc.append(line['penalty_hpc'])
                plot_penalty_lpc.append(line['penalty_lpc'])
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

            if line['tier_name'] == 'SSD':
                # chr
                plot_cache_hit_ratio_ssd.append(line['cache hit ratio'])
                # chr high priority content
                plot_cache_hit_ratio_hpc_ssd.append(line['cache hit ratio hpc'])
                # chr low priority content
                plot_cache_hit_ratio_lpc_ssd.append(line['cache hit ratio lpc'])
                # average data retrieval time
                plot_average_data_retrieval_time_ssd.append(line['avg_v_retrieval_time'])
                # average high priority data retrieval time
                plot_high_p_data_retrieval_time_ssd.append(line['avg_hpc_retrieval_time'])
                # average low priority data retrieval time
                plot_low_p_data_retrieval_time_ssd.append(line['avg_lpc_retrieval_time'])
                # used size
                plot_used_size_ssd.append(line['used_size'] / (line['max_size'] * line['target_occupation']))
                # waisted size
                plot_waisted_size_ssd.append(
                    (line['number_of_packets'] * slot_size - line['used_size']) / (
                            line['max_size'] * line['target_occupation']))
                # number of read
                plot_number_read_ssd.append(line['number_of_reads'])
                # number of write
                plot_number_write_ssd.append(line['number_of_write'])
                # read throughput
                plot_read_throughput_ssd.append(line['read_throughput'])

        # ==================
        # chr total
        df = pd.DataFrame(
            data={'DRAM': plot_cache_hit_ratio_ram, 'SSD': plot_cache_hit_ratio_ssd})
        df.index = plot_content_store_config
        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='Cache Hit Ratio')

        for c in ax.containers:
            labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(os.path.join(figure_folder, "chr.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # ==================
        # chr high priority per tier
        df = pd.DataFrame({'DRAM_H': plot_cache_hit_ratio_hpc_ram, 'SSD_H': plot_cache_hit_ratio_hpc_ssd})
        df.index = plot_content_store_config

        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='High Priority Cache Hit Ratio')
        for c in ax.containers:
            labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(os.path.join(figure_folder, "chr_hpc.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # ==================
        # chr low priority per tier
        df = pd.DataFrame({'DRAM_L': plot_cache_hit_ratio_lpc_ram, 'SSD_L': plot_cache_hit_ratio_lpc_ssd})
        df.index = plot_content_store_config

        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='Low Priority Cache Hit Ratio')
        for c in ax.containers:
            labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(os.path.join(figure_folder, "chr_lpc.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # ==================
        # Used size per tier
        df = pd.DataFrame(data={'DRAM': plot_used_size_ram, 'SSD': plot_used_size_ssd})
        df.index = plot_content_store_config

        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='Ratio Used Size')
        for c in ax.containers:
            labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(os.path.join(figure_folder, "used_size.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # ==================
        # waisted size
        df = pd.DataFrame(
            data={'DRAM': plot_waisted_size_ram, 'SSD': plot_waisted_size_ssd})
        df.index = plot_content_store_config
        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='Waisted size (ko)')

        for c in ax.containers:
            labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(os.path.join(figure_folder, "waisted_size.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # ==================
        # Number of read
        df = pd.DataFrame(
            data={'DRAM': plot_number_read_ram, 'SSD': plot_number_read_ssd})
        df.index = plot_content_store_config

        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='Number of Read')
        for c in ax.containers:
            labels = [v.get_height() if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(os.path.join(figure_folder, "read_number.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # ==================
        # Number of write
        df = pd.DataFrame(
            data={'DRAM': plot_number_write_ram, 'SSD': plot_number_write_ssd})
        df.index = plot_content_store_config

        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='Number of Write')
        for c in ax.containers:
            labels = [v.get_height() if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(os.path.join(figure_folder, "write_number.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # ==================
        # high priority data retrieval time
        df = pd.DataFrame(
            data={'DRAM': plot_high_p_data_retrieval_time_ram, 'SSD': plot_high_p_data_retrieval_time_ssd})
        df.index = plot_content_store_config

        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='High Priority Data Retrieval Time (ns)')
        for c in ax.containers:
            labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(
                os.path.join(figure_folder, "high_priority_data_retrieval_time.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # ==================
        # low priority data retrieval time
        df = pd.DataFrame(
            data={'DRAM': plot_low_p_data_retrieval_time_ram, 'SSD': plot_low_p_data_retrieval_time_ssd})
        df.index = plot_content_store_config

        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='Low Priority Data Retrieval Time (ns)')
        for c in ax.containers:
            labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(
                os.path.join(figure_folder, "low_priority_data_retrieval_time.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # ==================
        # data retrieval time
        df = pd.DataFrame(
            data={'DRAM': plot_average_data_retrieval_time_ram, 'SSD': plot_average_data_retrieval_time_ssd})
        df.index = plot_content_store_config

        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='Data Retrieval Time (ns)')
        for c in ax.containers:
            labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(os.path.join(figure_folder, "data_retrieval_time_per_tier.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # ==================
        # penalty
        df = pd.DataFrame(
            data={'penalty_hpc': plot_penalty_hpc, 'penalty_lpc': plot_penalty_lpc})
        df.index = plot_content_store_config

        ax = df.plot(kind='bar', stacked=True, figsize=(17, 6), rot=0, xlabel='Content Store configuration',
                     ylabel='Penalty ($)')
        for c in ax.containers:
            labels = [v.get_height() if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        try:
            plt.savefig(os.path.join(figure_folder, "penalty.png"))
        except Exception as e:
            print(f'Error %s trying to write into a new file in output folder "{figure_folder}"' % e)

        # # ==================
        # # read throughput disk
        # df = pd.DataFrame(data={'Data Retrieval Time ': plot_average_data_retrieval_time,
        #                         'Average Network Response Time': [0.3] * len(plot_average_data_retrieval_time),
        #                         'Average Node Access Time': [0.001] * len(plot_average_data_retrieval_time)})
        # df.index = plot_read_throughput_disk
        #
        # ax = df.plot(fig_size=(17, 6), rot=0, x_label='Read Throughput Disk (GBPS)',
        #              y_label='Time (s)')
        # for c in ax.containers:
        #     labels = [v.get_height() if v.get_height() > 0 else '' for v in c
        #     ax.bar_label(c, labels=labels, label_type='center')
        #
        # try: plt.savefig(os.path.join(figure_folder, plot_content_store_config[
        # 0]+"_retrieval_time_per_read_throughput_disk.png")) except Exception as e: print(f'Error %s trying to write
        # into a new file in output folder "{figure_folder}"' % e)
