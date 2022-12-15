import numpy as np


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
