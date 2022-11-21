import gzip
import json
import os
import time
from collections import OrderedDict
import matplotlib.pyplot as plt
import pandas as pd
from fitter import Fitter


#   The json record struct

#   DirType   string `json:"t"`     // packet direction and type
# 	Timestamp int64  `json:"ts"`    // Unix epoch nanoseconds
# 	Flow      []byte `json:"flow"`  // flow key
# 	Size2     int    `json:"size2"` // packet size at NDNLPv2 layer
# 	Size3       int        `json:"size3,omitempty"`       // packet size at L3
# 	NackReason  int        `json:"nackReason,omitempty"`  // Nack reason
# 	Name        ndn.Name   `json:"name,omitempty"`        // packet name
# 	CanBePrefix bool       `json:"cbp,omitempty"`         // Interest CanBePrefix
# 	MustBeFresh bool       `json:"mbf,omitempty"`         // Interest MustBeFresh
# 	FwHint      []ndn.Name `json:"fwHint,omitempty"`      // Interest ForwardingHint
# 	Lifetime    int        `json:"lifetime,omitempty"`    // Interest InterestLifetime (ms)
# 	HopLimit    int        `json:"hopLimit,omitempty"`    // Interest HopLimit
# 	ContentType int        `json:"contentType,omitempty"` // Data ContentType
# 	Freshness   int        `json:"freshness,omitempty"`   // Data FreshnessPeriod (ms)
# 	FinalBlock  bool       `json:"finalBlock,omitempty"`  // Data is final block
class JsonTraceDistributions:
    def __init__(self):
        distributions_folder = "json-distributions/<timestamp>"
        self.distributions_folder = distributions_folder.replace('/', os.path.sep).replace("<timestamp>",
                                                                                           time.strftime(
                                                                                               "%a_%d_%b_%Y_%H-%M-%S",
                                                                                               time.localtime()))
        distributions_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), self.distributions_folder))
        try:
            os.makedirs(self.distributions_folder, exist_ok=True)
        except:
            print(f'Error trying to create output folder "{distributions_folder}"')

    def packets_distribution(self, fileName: str, trace_len_limit=-1):
        plot_x = []
        plot_y = []
        lines = []
        for line in gzip.open(fileName, "r"):
            lines.append(json.loads(line))

        if trace_len_limit != -1:
            lines = lines[0:trace_len_limit]

        lines = [line for line in lines if 't' in line and 'ts' in line and 'size2' in line and 'name' in line]

        numberOfPackets = OrderedDict()
        i = 0
        h = 0
        for line in lines:
            if i == 0:
                h = line['ts']
            diff = line['ts'] - h
            if diff < 1000000000:  # 1second
                i += 1
            else:
                numberOfPackets[round(line['ts'] / 6e10, 0)] = i
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

    def size_distribution(self, fileName: str, trace_len_limit=-1):
        lines = []
        plot_dataSizes = []
        plot_numberOfDataPackets = []

        for line in gzip.open(fileName, "r"):
            lines.append(json.loads(line))
        lines = [line for line in lines if 't' in line and 'ts' in line and 'size2' in line and 'name' in line]

        if trace_len_limit != -1:
            lines = lines[0:trace_len_limit]

        dataLines = [line for line in lines if 'D' in line['t']]
        dataSizes = OrderedDict()
        min_size = int(dataLines[0]['size2'])
        max_size = int(dataLines[0]['size2'])
        for line in dataLines:
            if max_size < int(line['size2']):
                max_size = int(line['size2'])
            if min_size > int(line['size2']):
                min_size = int(line['size2'])
            if int(line['size2']) in dataSizes.keys():
                dataSizes[int(line['size2'])] = dataSizes[int(line['size2'])] + 1
            else:
                dataSizes[int(line['size2'])] = 1

        for key, value in dataSizes.items():
            plot_dataSizes.append(key)
            plot_numberOfDataPackets.append(value)

        data_first_key = next(iter(dataLines))['ts']
        data_last_key = next(reversed(dataLines))['ts']
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
        lines = []
        for line in gzip.open(fileName, "r"):
            lines.append(json.loads(line))

        if trace_len_limit != -1:
            lines = lines[0:trace_len_limit]

        lines = [line for line in lines if 't' in line and 'ts' in line and 'size2' in line and 'name' in line]

        xi_1 = 0
        diff = 0
        min_period = 0
        max_period = 0

        for line in lines:
            if xi_1 == 0:
                min_period = line['ts']
                xi_1 = line['ts']
            else:
                diff += line['ts'] - xi_1
                if max_period < line['ts'] - xi_1:
                    max_period = line['ts'] - xi_1
                if min_period > line['ts'] - xi_1:
                    min_period = line['ts'] - xi_1
                xi_1 = line['ts']

        # timestamp
        moy = diff / len(lines)
        print("average time of event occurrence = " + moy.__str__())
        print("minimum time before event occurrence = " + min_period.__str__())
        print("maximum time before event occurrence = " + max_period.__str__())
        # names
        names = [line['name'] for line in lines]
        names = list(set(names))
        print("number of content = " + len(names).__str__())