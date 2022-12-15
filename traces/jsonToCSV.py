import csv
import gzip
import json


#   The json record struct

#   DirType   string `json:"t"`     // packet direction and type
# 	Timestamp int64  `json:"ts"`    // Unix epoch nanoseconds
# 	Flow      []byte `json:"flow"`  // flow key defines the interface
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
    def __init__(self, fileName: str, trace_len_limit=-1):
        self.nb_interests = 0
        self.gen_trace(fileName, trace_len_limit)

    def gen_trace(self, fileName: str, trace_len_limit=-1):
        # 'data_back', 'timestamp', 'name', 'size', 'priority', 'responseTime'
        # gather the catalog of items from the trace
        lines = []
        # turn the json file to list
        for line in gzip.open(fileName, "r"):
            lines.append(json.loads(line))

        # Use only lines that have data_back, timestamp, size and name
        lines_for_simu = [line for line in lines if 't' in line and 'ts' in line and 'size3' in line and 'name' in line]
        if trace_len_limit != -1:
            lines_for_simu = lines_for_simu[0:trace_len_limit]
        # Remove unused fields
        for line in lines_for_simu:
            if 'size2' in line:
                del line['size2']
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
        response_times = {}

        lines_with_incoming_traffic = [line for line in lines_for_simu if line['t'] == '>D' or line['t'] == '>I']
        lines_with_incoming_data = [line for line in lines_for_simu if line['t'] == '>D']

        # list containing only prefixes
        names_prefixes = {}
        prefixes = [line['name'] for line in lines_with_incoming_traffic if 'cbp' in line]
        for line in lines_with_incoming_data:
            for prefix in prefixes:
                if line['name'] == prefix or prefix in line['name']:
                    names_prefixes[line['name']] = prefix
                    break
            if line['name'] not in names_prefixes:
                names_prefixes[line['name']] = line['name']

        for line in lines_for_simu:
            if line['t'] == '>D':
                if line['name'] in response_times.keys():
                    continue
                s = list(filter(lambda x: (x['t'] == '<I' and x["flow"] == line['flow']) and (
                        (line['name'] == x['name']) or ('cbp' in x and x['name'] in line['name'])),
                                lines_for_simu[lines_for_simu.index(line)::-1]))
                if s:
                    response_times.update({k['name']: line['ts'] - s[0]['ts'] for k in s})

        with open('resources/dataset_ndn/ndn6trace.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            for line in lines_with_incoming_traffic:
                if line['t'] == '>D' and response_times.get(line['name']):
                    traceline = ['d', line['ts'], names_prefixes.get(line['name']), line['size3'], 'h',
                                 response_times.get(line['name'])]
                    # write the data
                    writer.writerow(traceline)
                if line['t'] == '>I' and response_times.get(line['name']):
                    traceline = ['i', line['ts'], line['name'], line['size3'], 'h', response_times.get(line['name'])]

                    # write the data
                    writer.writerow(traceline)
                    self.nb_interests += 1
