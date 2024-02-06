import numpy as np
import torch
from torch import nn
import cv2

# input = torch.zeros(2, 5)
# src = torch.tensor([[1., 2., 3., 4., 5.], [6., 7., 8., 9., 10.]])
# index = torch.tensor([[0, 1, 2, 3, 4], [1, 0, 2, 4, 3]])
# input.scatter_(dim=1, index=index, src=src)
# print(input)
# print("-----------------------------------")

dim = 1
logits = torch.tensor([[1.45, 2.24, 3.76, 9.22, 4.44, 5.55], [6.434, 7.2423, 8.2423, -5.4234, 9.423, 10.56]])
gt_mask = logits
logits = torch.softmax(logits, dim)
max_idx = torch.argmax(logits, dim, keepdim=True)
print(max_idx)
one_hot = logits.new_full(logits.shape, 0)
print("one_hot1: \n", one_hot)
one_hot.scatter_(dim, max_idx, 1)
print("one_hot2: \n", one_hot)
one_hot.scatter_(dim, torch.clamp(max_idx-1, min=0), 1)
one_hot.scatter_(dim, torch.clamp(max_idx-2, min=0), 1)
print("one_hot3: \n", one_hot)
one_hot.scatter_(dim, torch.clamp(max_idx+1, max=logits.shape[dim]-1), 1)
one_hot.scatter_(dim, torch.clamp(max_idx+2, max=logits.shape[dim]-1), 1)
print("one_hot4: \n", one_hot)
print("-----------------------------------")


idx1 = torch.argmax(logits, dim)
idx1_onehot_spread = one_hot.bool()
print("before logits: \n", logits)
logits[idx1_onehot_spread] = 0
print("after logits: \n", logits)
idx2 = torch.argmax(logits, dim)
print("idx1: \n", idx1)
print("idx2: \n", idx2)
logits = torch.stack([idx1, idx2], dim) - 1
print("finial logits: \n", logits)
print("-----------------------------------")


print(torch.topk(gt_mask, 2, dim=1))
print(torch.topk(gt_mask, 2, dim=1)[1] - 1)
print("-----------------------------------")
