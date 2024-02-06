# Pytorch and Python Tricks Notes

[TOC]

## 一、Pytorch

### 1. nn.Conv2d 尺寸计算

> W_o = (W - K + 2 * P) / S + 1
>
> H_o = (H  - K + 2 * P) / S + 1
>

其中，W 表示输入特征图的宽度，H 表示输入特征图的高度，K 表示卷积核的大小，P 表示 padding 的大小，S 表示卷积核的步幅。

### 2. 卷积网络宽度/深度设计

1. 参考：https://blog.csdn.net/qq_39478403/article/details/117414535

### 3. view 和 reshape 的区别

1. view()方法：只适用于满足连续性条件的tensor，并且该操作不会开辟新的内存空间，只是产生了对原存储空间的一个新别称和引用，返回值是视图，因此不可以改变数据量；
2. reshape()方法：返回值既可以是视图，也可以是副本。当满足连续性条件时返回view，否则返回副本[ 此时等价于先调用contiguous()方法在使用view() ]，因此可以改变数据量；

## 二、Python
