import os
import numpy as np

if not os.path.exists('./npydata'):
    os.makedirs('./npydata')

# Your dataset path
shanghai_root = 'd:/Crowd-Counting-Platform/ShanghaiTech'

try:
    # Shanghai Part A - your structure uses 'part_A' not 'part_A_final'
    shanghaiAtrain_path = shanghai_root + '/part_A/train_data/images/'
    shanghaiAtest_path = shanghai_root + '/part_A/test_data/images/'

    train_list = []
    for filename in os.listdir(shanghaiAtrain_path):
        if filename.split('.')[1] == 'jpg':
            train_list.append(shanghaiAtrain_path + filename)

    train_list.sort()
    np.save('./npydata/ShanghaiA_train.npy', train_list)

    test_list = []
    for filename in os.listdir(shanghaiAtest_path):
        if filename.split('.')[1] == 'jpg':
            test_list.append(shanghaiAtest_path + filename)
    test_list.sort()
    np.save('./npydata/ShanghaiA_test.npy', test_list)

    print(f"Generated ShanghaiA image lists:")
    print(f"  Train: {len(train_list)} images")
    print(f"  Test: {len(test_list)} images")

except Exception as e:
    print(f"Error generating ShanghaiA lists: {e}")