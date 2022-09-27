import csv
import gzip
import json

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


class JsonToCSVTrace:
    def __init__(self, fileName: str):
        self.nb_interests = 0
        self.gen_trace(fileName)

    def gen_trace(self, fileName: str):
        # 'packetType', 'timestamp', 'name', 'size', 'priority', 'responseTime'
        # gather the catalog of items from the trace
        lines = []
        # turn the json file to list
        for line in gzip.open(fileName, "r"):
            lines.append(json.loads(line))

        # Use only lines that have packetType, timestamp, size and name
        linesForSimu = [line for line in lines if 't' in line and 'ts' in line and 'size2' in line and 'name' in line]

        # Remove unused fields
        for line in linesForSimu:
            if 'size3' in line:
                del line['size3']
            if 'nackReason' in line:
                del line['nackReason']
            if 'mbf' in line:
                del line['mbf']
            if 'fwHint' in line:
                del line['fwHint']
            if 'lifetime' in line:
                del line['lifetime']
            if 'hopLimit' in line:
                del line['hopLimit']
            if 'contentType' in line:
                del line['contentType']
            if 'freshness' in line:
                del line['freshness']
            if 'finalBlock' in line:
                del line['finalBlock']

        # calculate the Response Times
        responseTimes = {}
        linesWithDataPackets = [line for line in linesForSimu if line['t'] == '>D']

        for line in linesWithDataPackets:
            if line['name'] in responseTimes.keys():
                continue
            s = list(filter(lambda x: (x['t'] == '<I' and x["flow"] == line['flow']) and (
                        (line['name'] == x['name']) or ('cbp' in x and x['name'] in line['name'])),
                            linesForSimu[linesForSimu.index(line)::-1]))
            if s:
                responseTimes.update({k['name']: (line["ts"] - s[0]["ts"]) * 10**(-6) for k in s})

        print(linesForSimu.__sizeof__())
        linesWithIncomingTraffic = [line for line in linesForSimu if line['t'] == '>D' or line['t'] == '>I']
        print(linesWithIncomingTraffic.__len__())
        with open('resources/dataset_ndn/ndn6trace.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            for line in linesWithIncomingTraffic:
                if line['t'] == '>D':
                    traceline = ['d', line['ts'], line['name'], line['size2'], 'h', responseTimes.get(line['name'])]
                    # write the datas
                    writer.writerow(traceline)
                if line['t'] == '>I':
                    traceline = ['i', line['ts'], line['name'], line['size2'], 'h', responseTimes.get(line['name'])]
                    # write the datas
                    writer.writerow(traceline)
                    self.nb_interests += 1

