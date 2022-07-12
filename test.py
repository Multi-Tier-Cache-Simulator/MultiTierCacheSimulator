from math import sqrt

unit = 10 ** 11
number_of_tested_config = 4
storage_config_list = [[['SSD', round(4 * unit / (sqrt(2) ** (number_of_tested_config - 1 - i * 3))), 100e-6,
                         2e9, 'commandline-policy'],
                        ['HDD', 8 * unit, 10e-3, 250e6, 'commandline-policy'],
                        ['Tapes', 50 * unit, 20, 315e6, 'no-policy']] for i in
                       range(number_of_tested_config)]

for storage_config in storage_config_list:
    for config in storage_config:
        print(config[:-1])
        print(config)
        print("======")
