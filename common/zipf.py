import numpy as np


def zip_f(alpha, store_size):
    if not hasattr(zip_f, "zip_f_first_call"):
        zip_f.zip_f_first_call = True
        zip_f.sum_c = 0.0
        zip_f.probInterval = []
        for i in range(1, store_size + 1):
            current_param = pow(i, -alpha)
            zip_f.sum_c += current_param
            zip_f.probInterval.append(zip_f.sum_c)
        zip_f.sum_c = 1 / zip_f.sum_c
        for i in range(1, store_size + 1):
            zip_f.probInterval[i - 1] *= zip_f.sum_c

    # Pull a uniform random number (0 < z < 1)
    z = np.random.random()
    while z == 0 or z == 1:
        z = np.random.random()

    # Map z to the value
    for i in range(1, store_size + 1):
        if zip_f.probInterval[i - 1] >= z:
            return i
    return store_size

