import os

PATH = os.path.dirname(__file__)

# NDN_PACKETS = [f'{PATH}/dataset_jedi/{path}' for path in os.listdir(os.path.join(PATH, "dataset_jedi"))
#                if path.split('.')[-1] not in ["tgz", "sh", "bat", "gz"]]
#
# NDN_PACKETS = [f'{PATH}/dataset_synthetic/{path}' for path in os.listdir(os.path.join(PATH, "dataset_synthetic"))
#                if path.split('.')[-1] not in ["tgz", "sh", "bat", "gz"]]

NDN_PACKETS = [f'{PATH}/dataset_snia/{path}' for path in os.listdir(os.path.join(PATH, "dataset_snia"))
               if path.split('.')[-1] not in ["tgz", "sh", "bat", "gz"]]
print(NDN_PACKETS)
