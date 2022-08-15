import csv
import random
import numpy as np

# in this class we :
#   1. generate a catalog of items
#   2. a consumer requests an item selected from the catalog according to a Zipf distribution with parameter 1.2.


class TraceCreator:
    _COLUMN_NAMES = ('packetType', 'timestamp', 'name', 'size', 'priority', 'responseTime')

    # N: catalogue size
    # alpha: Zipf Law
    # size: size of the content
    def __init__(self, fileName: str, N: int, alpha: float, size: int):
        self.nb_interests = 0
        self.gen_trace(fileName, N, alpha, size)

    def gen_trace(self, fileName: str, N: int, alpha: float, size: int):
        words = []
        words_in = []
        t = 128166385295514000
        fileObj = open(fileName, "r")  # opens the file in read mode
        lines = fileObj.read().splitlines()
        for line in lines:
            words.extend(line.split())

        with open('C:/Users/lna11/PycharmProjects/multi_tier_cache_simulator/resources/dataset_ndn/trace.csv', 'w',
                  newline='') as f:
            writer = csv.writer(f)
            # create the data
            for i in range(N):
                index = np.random.zipf([alpha, alpha])
                for idx in index:
                    if idx < len(words):
                        responseTime = random.randrange(713, 3438)
                        if words[idx] in words_in:
                            line = ["i", t, words[idx], size, "h", responseTime]
                            self.nb_interests += 1
                        else:
                            line = ["d", t, words[idx], size, "h", responseTime]
                        # write the data
                        writer.writerow(line)
                        t += 1000
                        words_in.append(words[idx])
