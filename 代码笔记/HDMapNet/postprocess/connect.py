import math
import random
import numpy as np
from copy import deepcopy

import torch


def sort_points_by_dist(coords):
    '''
    这个函数主要用于对二维点集进行排序，根据点到点的距离进行排序。实现原理是通过计算两点之间的距离矩阵，然后根据距离矩阵进行排序。
    1. 首先计算两点之间的距离矩阵。
    2. 初始化一个排序列表和索引列表，并将第一个点添加到排序列表中。
    3. 然后，它将不断地迭代，直到所有的点都添加到排序列表中。在每次迭代中，它会找到与当前点距离最短的下一个点，并将该点的索引添加到索引列表中
    4. 它会更新距离矩阵，将下一个点的距离设置为无穷大，以避免重复选择
    '''
    coords = coords.astype('float')
    num_points = coords.shape[0]
    # 在NumPy中, [:, None]的作用是将一个一维数组转换为一个二维列向量
    # diff_matrix[i, j]: 表示坐标 coords[i] 和 coords[j] 之间的差异
    # 这里的操作详见test_numpy.py 中 #repeat
    diff_matrix = np.repeat(coords[:, None], num_points, 1) - coords
    # shape num_points * num_points（表示长度）
    dist_matrix = np.sqrt(((diff_matrix) ** 2).sum(-1))
    # dist_matrix_full 后续对比使用
    dist_matrix_full = deepcopy(dist_matrix)
    # 差 / 方差： 表示从坐标 coords[i] 指向 coords[j] 的单位方向向量
    direction_matrix = diff_matrix / (dist_matrix.reshape(num_points, num_points, 1) + 1e-6)

    sorted_points = [coords[0]]
    sorted_indices = [0]
    #  在 dist_matrix 中将第一个点的距离设置为无穷大，以避免与自己比较
    dist_matrix[:, 0] = np.inf

    last_direction = np.array([0, 0])
    for i in range(num_points - 1):
        last_idx = sorted_indices[-1]
        dist_metric = dist_matrix[last_idx] - 0 * (last_direction * direction_matrix[last_idx]).sum(-1)
        idx = np.argmin(dist_metric) % num_points  # % num_points：防止溢出
        new_direction = direction_matrix[last_idx, idx] # 从坐标 last_idx 指向 idx 的单位方向向量

        # 检查所选点是否距离最后排序点大于 3 个单位的阈值内，但已经排序点中是否有比 5 个单位更近的其他点。
        if dist_metric[idx] > 3 and min(dist_matrix_full[idx][sorted_indices]) < 5:
            dist_matrix[:, idx] = np.inf
            continue
        # 如果该点距离已排序点的距离大于 10（这个条件在已排序点占比达到总点数的 90% 后生效），则终止排序
        if dist_metric[idx] > 10 and i > num_points * 0.9:
            break
        sorted_points.append(coords[idx])
        sorted_indices.append(idx)
        dist_matrix[:, idx] = np.inf
        last_direction = new_direction

    return np.stack(sorted_points, 0)


def connect_by_step(coords, direction_mask, sorted_points, taken_direction, step=5, per_deg=10):
    '''
    给定的坐标集合coords中, 按照一定的步骤和方向, 找出与起始点最近的点, 并将这些点按照顺序连接起来
    @ coords          : 坐标集合, 为一个二维numpy数组, 其中的每个元素都是一个坐标点
    @ direction_mask  : 方向掩码, 一个二维numpy数组, 用于指定每个坐标点可选择的方向
    @ sorted_points   : 已排序的点集合, 用于记录已经找到的点
    @ taken_direction : 一个记录每个坐标点已选择方向的字典, bool类型, 大小为direction_mask大小
    @ step            : 步长, 用于确定每一步查找下一个点时的搜索范围
    @ per_deg         : 每个方向的角度, 用于确定每个坐标点可选择的方向
    '''
    while True:
        # 取当前已找到的最后一个点，并翻转其坐标，用于后续查找
        last_point = tuple(np.flip(sorted_points[-1]))
        # 判断该点对应的方向是否已被选择，如果没有则选择该方向，并标记为已选择。如果两个方向都已被选择，则跳出循环。
        if not taken_direction[last_point][0]:
            direction = direction_mask[last_point][0]
            taken_direction[last_point][0] = True
        elif not taken_direction[last_point][1]:
            direction = direction_mask[last_point][1]
            taken_direction[last_point][1] = True
        else:
            break

        if direction == -1:
            continue

        deg = per_deg * direction
        vector_to_target = step * np.array([np.cos(np.deg2rad(deg)), np.sin(np.deg2rad(deg))])
        last_point = deepcopy(sorted_points[-1])

        # NMS 对坐标集合coords进行筛选，只保留距离当前目标点大于 step - 1 的点
        coords = coords[np.linalg.norm(coords - last_point, axis=-1) > step-1]

        if len(coords) == 0:
            break

        target_point = np.array([last_point[0] + vector_to_target[0], last_point[1] + vector_to_target[1]])
        dist_metric = np.linalg.norm(coords - target_point, axis=-1)
        idx = np.argmin(dist_metric)

        if dist_metric[idx] > 50:
           continue

        sorted_points.append(deepcopy(coords[idx]))

        # 根据角度和方向掩码，确定下一个点可能的方向，并标记为已选择。
        vector_to_next = coords[idx] - last_point
        deg = np.rad2deg(math.atan2(vector_to_next[1], vector_to_next[0]))
        inverse_deg = (180 + deg) % 360
        target_direction = per_deg * direction_mask[tuple(np.flip(sorted_points[-1]))]
        # 计算当前点推理角度(inverse_deg)与目标点预测向量方向(target_direction)之间的差异，并选择最小差异的方向
        tmp = np.abs(target_direction - inverse_deg)
        tmp = torch.min(tmp, 360 - tmp)
        taken = np.argmin(tmp)
        taken_direction[tuple(np.flip(sorted_points[-1]))][taken] = True


def connect_by_direction(coords, direction_mask, step=5, per_deg=10):
    sorted_points = [deepcopy(coords[random.randint(0, coords.shape[0]-1)])]
    taken_direction = np.zeros_like(direction_mask, dtype=np.bool)

    connect_by_step(coords, direction_mask, sorted_points, taken_direction, step, per_deg)
    sorted_points.reverse() # 反向再来一次
    connect_by_step(coords, direction_mask, sorted_points, taken_direction, step, per_deg)
    return np.stack(sorted_points, 0)
