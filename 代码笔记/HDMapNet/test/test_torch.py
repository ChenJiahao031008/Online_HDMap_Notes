import numpy as np
import torch
from torch import nn
import cv2

B, N, D, H, W, C = 5, 6, 41, 8, 22, 64
xbound = [-30.0, 30.0, 0.15]
ybound = [-15.0, 15.0, 0.15]
zbound = [-10.0, 10.0, 20.0]
# Nprime = B * N * D * H * W
# batch_ix = torch.cat([torch.full([Nprime//B, 1], ix, dtype=torch.long) for ix in range(B)])
# print("batch_ix: \n", batch_ix.size())
# print([torch.full([Nprime//B, 1], 1, dtype=torch.long)])
# print("-----------------------------------")

# test_tensor = torch.FloatTensor([[[1, 2], [2, 4], [3, 6]], [[-40, 18], [15, 10], [6, 12]]])
# print(test_tensor)
# print(test_tensor.size())
# print(test_tensor.max(1).values)
# print(test_tensor.max(1).values.size())
# print("-----------------------------------")


# test_tensor = torch.FloatTensor([[[[1, 2, 3], [2, 4, 5], [3, 6, 5]], [[-40, 18, 19], [15, 10, 11], [6, 12, 13]] , [[0, -8, -14], [-5, 20, 11], [16, 19, 15]]]])
# print(test_tensor)
# print(test_tensor.size())
# max_pool = nn.AdaptiveMaxPool2d(1)
# test_tensor = max_pool(test_tensor)
# print(test_tensor)
# print(test_tensor.size())
# print("-----------------------------------")

# xmin, xmax = xbound[0], xbound[1]
# num_x = int((xbound[1] - xbound[0]) / xbound[2])
# ymin, ymax = ybound[0], ybound[1]
# num_y = int((ybound[1] - ybound[0]) / ybound[2])
# #  -30.0 30.0 -15.0 15.0 400 200
# # print("xmin, xmax, ymin, ymax, numx, numy: " ,xmin, xmax, ymin, ymax, num_x, num_y)
# y = torch.linspace(xmin, xmax, num_x)
# x = torch.linspace(ymin, ymax, num_y)
# y, x = torch.meshgrid(x, y)
# # print("x: ", x.size()) # x:  torch.Size([200, 400])
# x = x.flatten()
# y = y.flatten()
# # print("x: ", x.size()) # x:  torch.Size([80000])
# # print("x.unsqueeze(0): ", x.unsqueeze(0).size()) # torch.Size([1, 80000])
# x = x.unsqueeze(0).repeat(B, 1)
# y = y.unsqueeze(0).repeat(B, 1)
# print("x: ", x.size()) # x:  torch.Size([5, 80000])
# print("-----------------------------------")


h, w = 200, 400
tri_mask = np.zeros((h, w))
vertices = np.array([[0, 0], [0, h], [w, h]], np.int32)
pts = vertices.reshape((-1, 1, 2))
print(pts)
cv2.fillPoly(tri_mask, [pts], color=1.)
tri_mask = torch.tensor(tri_mask[None, :, :, None]) #  torch.Size([1, 200, 400, 1])
print("tri_mask.size() : ", tri_mask.size())
flipped_tri_mask = torch.flip(tri_mask, [2]).bool()
print("flipped_tri_mask: \n", torch.flip(tri_mask, [2]).view(h, w).numpy())
print("-----------------------------------")
