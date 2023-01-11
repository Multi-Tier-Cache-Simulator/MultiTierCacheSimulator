import numpy as np


# zip_f_first_call = True
# Sum_c = 0.0


def zip_f(alpha, store_size):
    if not hasattr(zip_f, "zip_f_first_call"):
        zip_f.zip_f_first_call = True

    if not hasattr(zip_f, "sum_c"):
        zip_f.sum_c = 0.0

    if zip_f.zip_f_first_call:
        for i in range(1, store_size + 1):
            zip_f.sum_c += (1.0 / pow(i, alpha))
        zip_f.sum_c = 1.0 / zip_f.sum_c
        zip_f.zip_f_first_call = False

    # Pull a uniform random number (0 < z < 1)
    z = np.random.random()
    while z == 0 or z == 1:
        z = np.random.random()

    # Map z to the value
    sum_prob = 0.0
    zip_f_value = 0
    for i in range(1, store_size + 1):
        sum_prob += zip_f.sum_c / pow(i, alpha)
        if sum_prob >= z:
            zip_f_value = i
            break

    assert 1 <= zip_f_value <= store_size
    return zip_f_value


def zip_f2(alpha, store_size):
    if not hasattr(zip_f, "zip_f_first_call"):
        zip_f.zip_f_first_call = True

    if not hasattr(zip_f, "sum_c"):
        zip_f.sum_c = 0.0

    if zip_f.zip_f_first_call:
        zip_f.zip_f_first_call = False
        for i in range(1, store_size + 1):
            zip_f.sum_c += pow(i, -alpha)

    # Pull a uniform random number (0 < z < 1)
    z = np.random.random()
    while z == 0 or z == 1:
        z = np.random.random()

    # Map z to the value
    sum_prob = 0.0
    zip_f_value = 0
    for i in range(1, store_size + 1):
        sum_prob += pow(i, -alpha) / zip_f.sum_c
        if sum_prob >= z:
            zip_f_value = i
            break

    assert 1 <= zip_f_value <= store_size
    return zip_f_value


def zip_f_opt(alpha, store_size):
    if not hasattr(zip_f, "zip_f_first_call"):
        zip_f.zip_f_first_call = True
        zip_f.sum_c = 0.0
        zip_f.probInterval = []
        for i in range(1, store_size + 1):
            currParam = pow(i, -alpha)
            zip_f.sum_c += currParam
            zip_f.probInterval.append(zip_f.sum_c)
        for i in range(1, store_size + 1):
            zip_f.probInterval[i - 1] = zip_f.probInterval[i - 1] / zip_f.sum_c

    # Pull a uniform random number (0 < z < 1)
    z = np.random.random()
    while z == 0 or z == 1:
        z = np.random.random()

    # Map z to the value
    for i in range(1, store_size + 1):
        if zip_f.probInterval[i - 1] >= z:
            zip_f.zip_f_value = i
            break

    assert 1 <= zip_f.zip_f_value <= store_size
    return zip_f.zip_f_value


# # Test the code
#
# import matplotlib.pyplot as plt
# import numpy as np
#
# freq = {}
# for i in range(1000):
#     tir = zip_f_opt(0.8, 10)
#     if not (tir in freq):
#         freq[tir] = 1
#     else:
#         freq[tir] += 1
#
# lists = sorted(freq.items())
# x, y = zip(*lists)
#
# y_pos = np.arange(len(x))
# # performance = [10,8,6,4,2,1]
#
# plt.bar(y_pos, y, align='center', alpha=0.5)
# plt.xticks(y_pos, x)
# plt.ylabel('frequency')
# plt.xlabel('Content rank')
#
# # plt.title('Programming language usage')
# plt.show()
