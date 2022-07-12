import os

PATH = os.path.dirname(__file__)

NDN_PACKETS = [f'{PATH}/dataset_ndn/{path}' for path in os.listdir(os.path.join(PATH, "dataset_ndn"))
               if path.split('.')[-1] not in ["tgz", "sh", "bat", "gz"]]