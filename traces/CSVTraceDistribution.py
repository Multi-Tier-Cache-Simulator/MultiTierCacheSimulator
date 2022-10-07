import csv
import os
import time
from collections import OrderedDict
import matplotlib.pyplot as plt
import pandas as pd


# _COLUMN_NAMES = ("packetType", "timestamp", "name", "size", "priority", "responseTime ")

class CSVTraceDistributions:
    def __init__(self, fileName: str):
        distributions_folder = "csv-distributions/<timestamp>"
        self.distributions_folder = distributions_folder.replace('/', os.path.sep).replace("<timestamp>",
                                                                                           time.strftime(
                                                                                               "%a_%d_%b_%Y_%H-%M-%S",
                                                                                               time.localtime()) + fileName)

        distributions_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), self.distributions_folder))
        try:
            os.makedirs(self.distributions_folder, exist_ok=True)
        except:
            print(f'Error trying to create output folder "{distributions_folder}"')

    def packets_distribution(self, fileName: str, trace_len_limit=-1):
        plot_x = []
        plot_y = []

        with open(fileName, encoding='utf8') as read_obj:
            csv_reader = csv.reader(read_obj, delimiter=',')
            lines = list(csv_reader)

        if trace_len_limit != -1:
            lines = lines[0:trace_len_limit]

        numberOfPackets = OrderedDict()
        i = 0
        h = 0
        for line in lines:
            if i == 0:
                h = int(line[1])
            diff = int(line[1]) - h
            if diff < 1000000000:  # 1second
                i += 1
            else:
                numberOfPackets[round(int(line[1]) / 6e10, 0)] = i
                i = 0

        first_key = next(iter(numberOfPackets))
        last_key = next(reversed(numberOfPackets))

        for key, value in numberOfPackets.items():
            plot_x.append(round((key - first_key) / (last_key - first_key), 3))
            plot_y.append(value)

        # f = Fitter(plot_x)
        # f.fit()
        # f.summary()
        plt.figure()
        plt.plot(plot_x, plot_y)
        period = last_key - first_key
        plt.title("Number of packets in " + period.__str__() + " minutes")
        plt.xlabel("Time (normalized)")
        plt.ylabel("Number of packets")

        try:
            plt.savefig(os.path.join(self.distributions_folder, "number_of_packets_per_time.png"))
        except:
            print(f'Error trying to write into a new file in output folder "{self.distributions_folder}"')

        # number of data packet and number of interest packet

    def size_distribution(self, fileName: str, trace_len_limit=-1):
        # size
        plot_dataSizes = []
        plot_numberOfDataPackets = []

        with open(fileName, encoding='utf8') as read_obj:
            csv_reader = csv.reader(read_obj, delimiter=',')
            lines = list(csv_reader)

        if trace_len_limit != -1:
            lines = lines[0:trace_len_limit]

        dataLines = [line for line in lines if 'd' in line[0]]
        dataSizes = OrderedDict()
        min_size = int(dataLines[0][3])
        max_size = int(dataLines[0][3])
        for line in dataLines:
            if max_size < int(line[3]):
                max_size = int(line[3])
            if min_size > int(line[3]):
                min_size = int(line[3])
            if int(line[3]) in dataSizes.keys():
                dataSizes[int(line[3])] = dataSizes[int(line[3])] + 1
            else:
                dataSizes[int(line[3])] = 1

        for key, value in dataSizes.items():
            plot_dataSizes.append(key)
            plot_numberOfDataPackets.append(value)

        data_first_key = int(next(iter(dataLines))[1])
        data_last_key = int(next(reversed(dataLines))[1])
        data_period = round((data_last_key - data_first_key) / 6e10, 0)
        plt.figure()
        plt.bar(plot_numberOfDataPackets, plot_dataSizes)
        plt.title('Number Of Data Packets per size for ' + data_period.__str__() + ' minutes')
        plt.xlabel("Size (o)")
        plt.ylabel("Number of packets")
        try:
            plt.savefig(os.path.join(self.distributions_folder, "number_of_packets_per_size.png"))
        except:
            print(f'Error trying to write into a new file in output folder "{self.distributions_folder}"')

        df = pd.DataFrame(
            data={'Number_Of_Data_Packets_per_size': plot_dataSizes}, index=plot_numberOfDataPackets)

        df.plot.pie(y='Number_Of_Data_Packets_per_size', figsize=(5, 5))

        try:
            plt.savefig(os.path.join(self.distributions_folder, "number_of_data_packets_per_size.png"))
        except:

            print(f'Error trying to write into a new file in output folder "{self.distributions_folder}"')
        print("max_size = " + max_size.__str__())
        print("min size = " + min_size.__str__())

    def event_distribution(self, fileName: str, trace_len_limit=-1):
        print(fileName)
        with open(fileName, encoding='utf8') as read_obj:
            csv_reader = csv.reader(read_obj, delimiter=',')
            lines = list(csv_reader)

        if trace_len_limit != -1:
            lines = lines[0:trace_len_limit]

        xi_1 = 0
        diff = 0
        min_period = 0
        max_period = 0
        min_reponse_time = 0
        max_reponse_time = 0
        averageReponseTime = 0

        for line in lines:
            if xi_1 == 0:
                min_period = int(line[1])
                min_reponse_time = int(line[5])
                xi_1 = int(line[1])
            else:
                diff += int(line[1]) - xi_1
                averageReponseTime += int(line[5])

                if max_period < int(line[1]) - xi_1:
                    max_period = int(line[1]) - xi_1
                if min_period > int(line[1]) - xi_1:
                    min_period = int(line[1]) - xi_1

                if max_reponse_time < int(line[5]):
                    max_reponse_time = int(line[5])
                if min_reponse_time > int(line[5]):
                    min_reponse_time = int(line[5])

                xi_1 = int(line[1])

        # timestamp
        moy = diff / len(lines)
        print("average time of event occurrence = " + moy.__str__())
        print("minimum time before event occurrence = " + min_period.__str__())
        print("maximum time before event occurrence = " + max_period.__str__())
        # names
        names = [line[2] for line in lines]
        names = list(set(names))
        print("number of content = " + len(names).__str__())
        # response Time
        art = averageReponseTime / len(lines)
        print("average response time = " + art.__str__())
        print("minimum response time = " + min_reponse_time.__str__())
        print("maximum response time = " + max_reponse_time.__str__())
