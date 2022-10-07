import csv
import random
import pandas as pd
import numpy as np
from random_word import RandomWords
import time


# time is in nanosecond
# size is in byte

class TraceCreator:
    # N: catalogue size
    # alpha: Zipf Law
    # traffic_period: in minutes
    def __init__(self, N: int, alpha: float, traffic_period: int):
        self.gen_trace(N, alpha, traffic_period)

    def gen_trace(self, N: int, alpha: float, traffic_period: int):
        # generate a catalog of items
        words = []
        random_words = RandomWords()
        while len(words) <= N:
            x = random_words.get_random_words()
            if type(x) == list:
                df = pd.Series(x)
                d = df.str.encode('ascii', 'ignore').str.decode('ascii')
                words += d.tolist()
            else:
                continue

        unique_words = [*set(words)]
        unique_words = unique_words[0: N]

        # generate current timestamp
        t = int(round(time.time_ns(), 0))
        lines_in_cs = []
        words_in_cs = []
        with open('resources/dataset_ndn/synthetic-trace.csv', 'w', encoding="utf-8",
                  newline='') as f:
            writer = csv.writer(f)
            # run for 1min and 30s
            end = t + traffic_period * 60000000000
            while t < end:
                # create requests on the words following a zipf's law
                index = np.random.zipf(alpha)
                while index >= len(unique_words):
                    index = np.random.zipf(alpha)
                # in ms turn to nanosecond
                responseTime = int(round(random.randrange(1000000, 10000000), 0))
                datasize = int(round(np.random.uniform(100, 8000), 0))
                # if unique_words[index] in node_words:
                if unique_words[index] in words_in_cs:
                    # 50% retransmission interest packet 50% retransmission data packet
                    p1 = 0.5
                    x = np.random.uniform(low=0.0, high=1.0, size=None)
                    if x < p1:
                        for line in lines_in_cs:
                            if line[2] == unique_words[index]:
                                l = ["i", t, unique_words[index], line[3], line[4], line[5]]
                                break
                    else:
                        for line in lines_in_cs:
                            if line[2] == unique_words[index]:
                                l = ["d", t, unique_words[index], line[3], line[4], line[5]]
                                break
                else:
                    # 50% high priority packets 50% low priority packets
                    p1 = 0.5
                    x = np.random.uniform(low=0.0, high=1.0, size=None)
                    if x < p1:
                        l = ["d", t, unique_words[index], datasize, "h", responseTime]
                    else:
                        l = ["d", t, unique_words[index], datasize, "l", responseTime]
                # write the data
                writer.writerow(l)
                # add nanoseconds
                t += int(round(random.uniform(489, 1000000000), 0))
                lines_in_cs.append(l)
                words_in_cs.append(unique_words[index])
