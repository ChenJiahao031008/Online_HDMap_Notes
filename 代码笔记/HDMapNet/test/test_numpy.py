import numpy as np
import cv2

# test = np.array([[[1, 1.5], [1, 2]], [[2, 2.5], [2, 4]], [[3, 3.5], [3, 6]], [[4, 4.5], [4, 8]], [[5, 5.5], [5, 10]]])
# print(test.shape)
# print(test)
# print(test[:, 0, :])
# print(test[:, 0])
# print("------------------------------------")

# h, w = 200, 400
# tri_mask = np.zeros((h, w))
# vertices = np.array([[0, 0], [0, h], [w, h]], np.int32)
# pts = vertices.reshape((-1, 1, 2))
# print(pts)
# cv2.fillPoly(tri_mask, [pts], color=1.)
# cv2.imshow("tri_mask", tri_mask)
# cv2.waitKey(0)
# print("------------------------------------")

# tri_mask = np.flip(tri_mask, 1)
# cv2.imshow("tri_mask", tri_mask)
# cv2.waitKey(0)
# print(tri_mask)
# print("------------------------------------")


# test = np.array([[1, 1.5], [2, 2.5], [2, 4]])
# b_test = np.array([[True, False], [False, True], [True, True]])
# print(test[b_test])
# test[b_test] = 0
# print(test)
# print("------------------------------------")

#repeat
coords = np.array([[1, 1.5], [2, 2.5], [2, 4]])
num_points = coords.shape[0]
print("repeat :\n", np.repeat(coords[:, None], num_points, 1))

#diff_matrix
diff_matrix = np.repeat(coords[:, None], num_points, 1) - coords
print("diff_matrix : \n", diff_matrix)

dist_matrix = np.sqrt(((diff_matrix) ** 2).sum(-1))
print("dist_matrix : \n", dist_matrix)

direction_matrix = diff_matrix / (dist_matrix.reshape(num_points, num_points, 1) + 1e-6)
print(dist_matrix.reshape(num_points, num_points, 1))
print("direction_matrix : \n", direction_matrix)
print("------------------------------------")
