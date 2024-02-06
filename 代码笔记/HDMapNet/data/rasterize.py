import cv2
import numpy as np

import torch

from shapely import affinity
from shapely.geometry import LineString, box


def get_patch_coord(patch_box, patch_angle=0.0):
    patch_x, patch_y, patch_h, patch_w = patch_box

    x_min = patch_x - patch_w / 2.0
    y_min = patch_y - patch_h / 2.0
    x_max = patch_x + patch_w / 2.0
    y_max = patch_y + patch_h / 2.0

    patch = box(x_min, y_min, x_max, y_max)
    patch = affinity.rotate(
        patch, patch_angle, origin=(patch_x, patch_y), use_radians=False
    )

    return patch


def get_discrete_degree(vec, angle_class=36):
    # np.mod: x % y
    deg = np.mod(np.degrees(np.arctan2(vec[1], vec[0])), 360)
    deg = (int(deg / (360 / angle_class) + 0.5) % angle_class) + 1
    return deg


def mask_for_lines(lines, mask, thickness, idx, type="index", angle_class=36):
    coords = np.asarray(list(lines.coords), np.int32)
    coords = coords.reshape((-1, 2))
    if len(coords) < 2:
        return mask, idx
    # 正向一次，反向一次，保证得到的结果从正向和反向都能验证
    if type == "backward":
        coords = np.flip(coords, 0)

    # 这个是同类合并，颜色一致，如果type是index，则idx++
    if type == "index":
        cv2.polylines(mask, [coords], False, color=idx, thickness=thickness)
        idx += 1
    else:
        # backward forward
        for i in range(len(coords) - 1):
            cv2.polylines(
                mask,
                [coords[i:]],
                False,
                # get_discrete_degree: 计算朝向
                color=get_discrete_degree(
                    coords[i + 1] - coords[i], angle_class=angle_class
                ),
                thickness=thickness,
            )
    return mask, idx


def line_geom_to_mask(
    layer_geom,
    confidence_levels,
    local_box,
    canvas_size,
    thickness,
    idx,
    type="index",
    angle_class=36,
):
    patch_x, patch_y, patch_h, patch_w = local_box

    patch = get_patch_coord(local_box)

    canvas_h = canvas_size[0]
    canvas_w = canvas_size[1]
    scale_height = canvas_h / patch_h
    scale_width = canvas_w / patch_w

    trans_x = -patch_x + patch_w / 2.0
    trans_y = -patch_y + patch_h / 2.0

    map_mask = np.zeros(canvas_size, np.uint8)

    # 遍历每个类别的所有line
    for line in layer_geom:
        if isinstance(line, tuple):
            line, confidence = line
        else:
            confidence = None
        new_line = line.intersection(patch)
        if not new_line.is_empty:
            new_line = affinity.affine_transform(
                new_line, [1.0, 0.0, 0.0, 1.0, trans_x, trans_y]
            )
            new_line = affinity.scale(
                new_line, xfact=scale_width, yfact=scale_height, origin=(0, 0)
            )
            confidence_levels.append(confidence)
            # type1  == 'index' , type2  == 'index', type3  == 'forward', type4  == 'backward'
            # index1 == idx++(1), index2 == 1      , index3 == 1        , index4 == 1
            # 上述index是初始值，mask_for_lines function 中 type == 'index' index会自动加1
            # instance_masks 和 filter_masks 区别在于 index 是每次从1开始还是继承下去
            if new_line.geom_type == "MultiLineString":
                for new_single_line in new_line:
                    map_mask, idx = mask_for_lines(
                        new_single_line, map_mask, thickness, idx, type, angle_class
                    )
            else:
                map_mask, idx = mask_for_lines(
                    new_line, map_mask, thickness, idx, type, angle_class
                )
    return map_mask, idx


def overlap_filter(mask, filter_mask):
    # C 是通道数
    C, _, _ = mask.shape
    for c in range(C - 1, -1, -1):
        ## 将重复操作施加到 维度‘axis=0’上，相当于增加行数，重复c次
        filter = np.repeat((filter_mask[c] != 0)[None, :], c, axis=0)
        # 将掩码 mask 中前 c 个通道中满足条件的区域（由 filter 控制）的值设为零
        # 这样就实现了根据 filter_mask 进行过滤的功能，只保留了满足条件的通道。
        mask[:c][filter] = 0
    return mask


def preprocess_map(
    vectors, patch_size, canvas_size, num_classes, thickness, angle_class
):
    confidence_levels = [-1]
    vector_num_list = {}
    # 清空历史
    for i in range(num_classes):
        vector_num_list[i] = []

    # 取出所有的点
    for vector in vectors:
        if vector["pts_num"] >= 2:
            vector_num_list[vector["type"]].append(
                LineString(vector["pts"][: vector["pts_num"]])
            )

    local_box = (0.0, 0.0, patch_size[0], patch_size[1])

    idx = 1
    instance_masks = []  # 每个实例的掩码，每个实例中也包含很多线
    filter_masks = []    # 每条线的掩码
    forward_masks = []   # 正向朝向的掩码
    backward_masks = []  # 逆向朝向的掩码
    # 注意，遍历的是类别
    for i in range(num_classes):
        map_mask, idx = line_geom_to_mask(
            vector_num_list[i],
            confidence_levels,
            local_box,
            canvas_size,
            thickness,
            idx,
        )
        instance_masks.append(map_mask)

        filter_mask, _ = line_geom_to_mask(
            vector_num_list[i],
            confidence_levels,
            local_box,
            canvas_size,
            thickness + 4,
            1,
        )
        filter_masks.append(filter_mask)

        forward_mask, _ = line_geom_to_mask(
            vector_num_list[i],
            confidence_levels,
            local_box,
            canvas_size,
            thickness,
            1,
            type="forward",
            angle_class=angle_class,
        )
        forward_masks.append(forward_mask)
        backward_mask, _ = line_geom_to_mask(
            vector_num_list[i],
            confidence_levels,
            local_box,
            canvas_size,
            thickness,
            1,
            type="backward",
            angle_class=angle_class,
        )
        backward_masks.append(backward_mask)

    filter_masks = np.stack(filter_masks)
    instance_masks = np.stack(instance_masks)
    forward_masks = np.stack(forward_masks)
    backward_masks = np.stack(backward_masks)

    instance_masks = overlap_filter(instance_masks, filter_masks)
    forward_masks = overlap_filter(forward_masks, filter_masks).sum(0).astype("int32")
    backward_masks = overlap_filter(backward_masks, filter_masks).sum(0).astype("int32")

    return (
        torch.tensor(instance_masks),
        torch.tensor(forward_masks),
        torch.tensor(backward_masks),
    )


def rasterize_map(vectors, patch_size, canvas_size, num_classes, thickness):
    confidence_levels = [-1]
    vector_num_list = {}
    for i in range(num_classes):
        vector_num_list[i] = []

    for vector in vectors:
        if vector["pts_num"] >= 2:
            vector_num_list[vector["type"]].append(
                (
                    LineString(vector["pts"][: vector["pts_num"]]),
                    vector.get("confidence_level", 1),
                )
            )

    local_box = (0.0, 0.0, patch_size[0], patch_size[1])

    idx = 1
    masks = []
    for i in range(num_classes):
        map_mask, idx = line_geom_to_mask(
            vector_num_list[i],
            confidence_levels,
            local_box,
            canvas_size,
            thickness,
            idx,
        )
        masks.append(map_mask)

    return np.stack(masks), confidence_levels
