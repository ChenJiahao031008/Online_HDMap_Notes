import numpy as np

feats = np.array([[1,1], [2,2], [3,3], [4,4], [5,5]])
ft_cumsum = feats.cumsum(0)
print(ft_cumsum)
print("-----------------------------------")

ranks = np.array([0, 1, 2, 2, 3])
kept = np.ones(feats.shape[0], dtype=bool)
kept[:-1] = (ranks[1:] != ranks[:-1])
print(kept)
print("-----------------------------------")

print("ranks     : ", ranks)
print("ranks[:-1]: ", ranks[:-1])
print("ranks[1:] : ", ranks[1:])
print(ranks[1:] != ranks[:-1])
print("-----------------------------------")

print("before    : ", ft_cumsum.shape)
ft_cumsum = ft_cumsum[kept]
print("after     : ", ft_cumsum.shape)
print("ft_cumsum : \n", ft_cumsum)
print("-----------------------------------")

print("ft_cumsum[:1]  : \n", ft_cumsum[:1])
print("ft_cumsum[1:]  : \n", ft_cumsum[1:])
print("ft_cumsum[:-1] : \n", ft_cumsum[:-1])
print("ft_cumsum[1:] - ft_cumsum[:-1] : \n", ft_cumsum[1:] - ft_cumsum[:-1])
ft_cumsum = np.concatenate((ft_cumsum[:1], ft_cumsum[1:] - ft_cumsum[:-1]))
print("ft_cumsum      : \n", ft_cumsum)
print("-----------------------------------")

# ranks = np.array([0, 1, (2), 2, 3])
feats_remove_repeat1 = np.array([[1,1], [2,2], [4,4], [5,5]])
feats_cumsum1 = feats_remove_repeat1.cumsum(0)
print("feats_cumsum1  : \n", feats_cumsum1)
print(feats_cumsum1 == ft_cumsum)

# ranks = np.array([0, 1, 2, (2), 3])
feats_remove_repeat2 = np.array([[1,1], [2,2], [3,3], [5,5]])
feats_cumsum2 = feats_remove_repeat2.cumsum(0)
print("feats_cumsum2  : \n", feats_cumsum2)
print(feats_cumsum2 == ft_cumsum)

# ranks = np.array([0, 1, (2 + 2), 3])
feats_cumsum3 = np.array([[1,1], [2,2], [3 + 4, 3 + 4], [5,5]])
print("feats_cumsum3  : \n", feats_cumsum3)
print(feats_cumsum3 == ft_cumsum)
print("-----------------------------------")
