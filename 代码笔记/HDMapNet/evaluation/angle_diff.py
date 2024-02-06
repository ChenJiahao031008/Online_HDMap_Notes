import torch

def onehot_encoding_spread(logits, dim=1):
    # 这段的演示详见: test_one_hot.py
    max_idx = torch.argmax(logits, dim, keepdim=True)
    one_hot = logits.new_full(logits.shape, 0)
    # scatter_：将源张量 src 的值按照给定的索引 index 散射到目标张量 input 的指定维度 dim 上。
    # torch.clamp：对张量进行截断操作
    one_hot.scatter_(dim, max_idx, 1)
    # 创建了另一个一热编码，但向左偏移了一个位置。torch.clamp 函数用于确保索引不会小于 0。
    # 允许在最大索引的上下文中捕捉相邻信息
    one_hot.scatter_(dim, torch.clamp(max_idx-1, min=0), 1)
    one_hot.scatter_(dim, torch.clamp(max_idx-2, min=0), 1)
    one_hot.scatter_(dim, torch.clamp(max_idx+1, max=logits.shape[dim]-1), 1)
    one_hot.scatter_(dim, torch.clamp(max_idx+2, max=logits.shape[dim]-1), 1)
    return one_hot


def get_pred_top2_direction(direction, dim=1):
    direction = torch.softmax(direction, dim)
    idx1 = torch.argmax(direction, dim)
    idx1_onehot_spread = onehot_encoding_spread(direction, dim)
    idx1_onehot_spread = idx1_onehot_spread.bool()
    direction[idx1_onehot_spread] = 0
    idx2 = torch.argmax(direction, dim)
    # idx1 最大的可能性位置
    # idx2 处理最大可能性及附近标签后，剩余的最大值位置
    ## TODO idx2 目的是什么？
    direction = torch.stack([idx1, idx2], dim) - 1
    return direction


def calc_angle_diff(pred_mask, gt_mask, angle_class):
    per_angle = float(360. / angle_class)
    eval_mask = 1 - gt_mask[:, 0]
    pred_direction = get_pred_top2_direction(pred_mask, dim=1).float()
    # torch.topk[0] == value; torch.topk[1] == index
    gt_direction = (torch.topk(gt_mask, 2, dim=1)[1] - 1).float()

    pred_direction *= per_angle
    gt_direction *= per_angle
    pred_direction = pred_direction[:, :, None, :, :].repeat(1, 1, 2, 1, 1)
    gt_direction = gt_direction[:, None, :, :, :].repeat(1, 2, 1, 1, 1)
    diff_mask = torch.abs(pred_direction - gt_direction)
    diff_mask = torch.min(diff_mask, 360 - diff_mask)
    diff_mask = torch.min(diff_mask[:, 0, 0] + diff_mask[:, 1, 1], diff_mask[:, 1, 0] + diff_mask[:, 0, 1]) / 2
    return ((eval_mask * diff_mask).sum() / (eval_mask.sum() + 1e-6)).item()
