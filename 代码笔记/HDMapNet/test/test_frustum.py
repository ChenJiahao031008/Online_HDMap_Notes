import numpy as np
import torch
from torch import nn

ogfH = 128
ogfW = 352
fH, fW = ogfH // 16, ogfW // 16
D = 41
xs = torch.linspace(0, ogfW - 1, fW, dtype=torch.float).view(1, 1, fW).expand(D, fH, fW)
ys = torch.linspace(0, ogfH - 1, fH, dtype=torch.float).view(1, fH, 1).expand(D, fH, fW)
ds = torch.arange(*[4, 45, 1], dtype=torch.float).view(-1, 1, 1).expand(-1, fH, fW)
frustum = torch.stack((xs, ys, ds), -1)

# print(xs.size())
# print(xs[1])
# print("-------------------------")
# print(torch.linspace(0, ogfW - 1, fW, dtype=torch.float))
# print("-------------------------")
# print(torch.linspace(0, ogfW - 1, fW, dtype=torch.float).view(1, 1, fW))

# print("-------------------------")
# print(ds)
# print("-------------------------")
# print(torch.arange(*[4, 45, 1], dtype=torch.float))
# print("-------------------------")
# print(torch.arange(*[4, 45, 1], dtype=torch.float).view(-1, 1, 1))

# print("-------------------------")
# print(frustum)
# print("-------------------------")
# print(frustum.size())
# print("-------------------------")
# print(xs[0])
# print(ys[0])
# print(ds[0])

print("-------------------------")
print(frustum)
