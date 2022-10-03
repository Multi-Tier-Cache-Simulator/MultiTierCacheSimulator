import gzip
import json
import os
import time
from collections import OrderedDict
import matplotlib.pyplot as plt
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
class TraceDistributions:
    def __init__(self):
        distributions_folder = "C:/Users/lna11/Documents/multi_tier_cache_simulator/distributions/<timestamp>"
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

        # Use only lines that have packetType, timestamp, size and name
        lines = [line for line in lines if 't' in line and 'ts' in line and 'size2' in line and 'name' in line]

        if trace_len_limit != -1:
            lines = lines[0:trace_len_limit]

        # Remove unused fields
        for element in lines:
            if 't' in element:
                del element['t']
            if 'size2' in element:
                del element['size2']
            if 'name' in element:
                del element['name']
            if 'size3' in element:
                del element['size3']
            if 'nackReason' in element:
                del element['nackReason']
            if 'cbp' in element:
                del element['cbp']
            if 'mbf' in element:
                del element['mbf']
            if 'fwHint' in element:
                del element['fwHint']
            if 'lifetime' in element:
                del element['lifetime']
            if 'hopLimit' in element:
                del element['hopLimit']
            if 'contentType' in element:
                del element['contentType']
            if 'freshness' in element:
                del element['freshness']
            if 'finalBlock' in element:
                del element['finalBlock']

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

        print(plot_x)
        print(plot_y)
        f = Fitter(plot_x)
        f.fit()
        f.summary()
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

        plot_interestSizes = []
        plot_dataSizes = []
        plot_numberOfDataPackets = []
        plot_numberOfInterestPackets = []

        for line in gzip.open(fileName, "r"):
            lines.append(json.loads(line))

        # Use only lines that have packetType, timestamp, size and name
        lines = [line for line in lines if 't' in line and 'ts' in line and 'size2' in line and 'name' in line]

        if trace_len_limit != -1:
            lines = lines[0:trace_len_limit]

        # remove unused fields
        for element in lines:
            if 'size3' in element:
                del element['size3']
            if 'nackReason' in element:
                del element['nackReason']
            if 'cbp' in element:
                del element['cbp']
            if 'mbf' in element:
                del element['mbf']
            if 'fwHint' in element:
                del element['fwHint']
            if 'lifetime' in element:
                del element['lifetime']
            if 'hopLimit' in element:
                del element['hopLimit']
            if 'contentType' in element:
                del element['contentType']
            if 'freshness' in element:
                del element['freshness']
            if 'finalBlock' in element:
                del element['finalBlock']

        # remove duplicates
        seen = []
        for line in lines:
            if line not in seen:
                seen.append(line)

        dataLines = [line for line in seen if 'D' in line['t']]
        interestLines = [line for line in seen if 'I' in line['t']]
        dataSizes = OrderedDict()
        interestSizes = OrderedDict()
        for line in dataLines:
            if line['size2'] in dataSizes.keys():
                dataSizes[line['size2']] = dataSizes[line['size2']] + 1
            else:
                dataSizes[line['size2']] = 1

        for line in interestLines:
            if line['size2'] in interestSizes.keys():
                interestSizes[line['size2']] = interestSizes[line['size2']] + 1
            else:
                interestSizes[line['size2']] = 1

        for key, value in dataSizes.items():
            plot_dataSizes.append(key)
            plot_numberOfDataPackets.append(value)

        for key, value in interestSizes.items():
            plot_interestSizes.append(key)
            plot_numberOfInterestPackets.append(value)

        data_first_key = next(iter(dataLines))['ts']
        data_last_key = next(reversed(dataLines))['ts']
        data_period = round((data_last_key - data_first_key) / 6e10, 0)
        interest_first_key = next(iter(interestLines))['ts']
        interest_last_key = next(reversed(interestLines))['ts']
        interest_period = round((interest_last_key - interest_first_key) / 6e10, 0)
        fig, axs = plt.subplots(2)
        axs[0].bar(plot_interestSizes, plot_numberOfInterestPackets)
        axs[0].set_title('Number Of Interest Packets per size for ' + data_period.__str__() + ' minutes')
        axs[1].bar(plot_dataSizes, plot_numberOfDataPackets, color='tab:orange')
        axs[1].set_title('Number Of Data Packets per size for ' + interest_period.__str__() + ' minutes')
        fig.tight_layout()
        try:
            plt.savefig(os.path.join(self.distributions_folder, "number_of_packets_per_size.png"))
        except:
            print(f'Error trying to write into a new file in output folder "{self.distributions_folder}"')

    def event_distribution(self, fileName: str, trace_len_limit=-1):
        lines = []
        for line in gzip.open(fileName, "r"):
            lines.append(json.loads(line))

        # Use only lines that have packetType, timestamp, size and name
        lines = [line for line in lines if 't' in line and 'ts' in line and 'size2' in line and 'name' in line]

        if trace_len_limit != -1:
            lines = lines[0:trace_len_limit]

        # Remove unused fields
        for element in lines:
            if 'size2' in element:
                del element['size2']
            if 'name' in element:
                del element['name']
            if 'size3' in element:
                del element['size3']
            if 'nackReason' in element:
                del element['nackReason']
            if 'cbp' in element:
                del element['cbp']
            if 'mbf' in element:
                del element['mbf']
            if 'fwHint' in element:
                del element['fwHint']
            if 'lifetime' in element:
                del element['lifetime']
            if 'hopLimit' in element:
                del element['hopLimit']
            if 'contentType' in element:
                del element['contentType']
            if 'freshness' in element:
                del element['freshness']
            if 'finalBlock' in element:
                del element['finalBlock']

        linesWithIncomingTraffic = [line for line in lines if line['t'] == '>D' or line['t'] == '>I']
        xi_1 = 0
        diff = 0
        min_period = 0
        max_period = 0
        for line in linesWithIncomingTraffic:
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

        moy = diff / trace_len_limit
        print(moy)
        print(min_period)
        print(max_period)
