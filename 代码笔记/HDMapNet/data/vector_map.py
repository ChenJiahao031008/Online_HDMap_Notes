import numpy as np
from nuscenes.map_expansion.map_api import NuScenesMap, NuScenesMapExplorer
from nuscenes.eval.common.utils import quaternion_yaw, Quaternion

# Shapely - 一个允许操作和分析平面几何对象的库。
from shapely import affinity, ops
from shapely.geometry import LineString, box, MultiPolygon, MultiLineString

from .const import CLASS2LABEL


class VectorizedLocalMap(object):
    def __init__(
        self,
        dataroot,
        patch_size,
        canvas_size,
        line_classes=["road_divider", "lane_divider"],
        ped_crossing_classes=["ped_crossing"],
        contour_classes=["road_segment", "lane"],
        sample_dist=1,
        num_samples=250,
        padding=False,
        normalize=False,
        fixed_num=-1,
    ):
        """
        Args:
            fixed_num = -1 : no fixed num
        """
        super().__init__()
        self.data_root = dataroot
        self.MAPS = [
            "boston-seaport",
            "singapore-hollandvillage",
            "singapore-onenorth",
            "singapore-queenstown",
        ]
        self.line_classes = line_classes  # 线的属性，方向分割线/车道分割
        self.ped_crossing_classes = ped_crossing_classes  # 人行道
        self.polygon_classes = contour_classes  # 多边型的类别

        self.nusc_maps = {}
        self.map_explorer = {}
        for loc in self.MAPS:
            self.nusc_maps[loc] = NuScenesMap(dataroot=self.data_root, map_name=loc)
            self.map_explorer[loc] = NuScenesMapExplorer(self.nusc_maps[loc])

        self.patch_size = patch_size
        self.canvas_size = canvas_size  # 这个含义不明确
        self.sample_dist = sample_dist
        self.num_samples = num_samples
        self.padding = padding
        self.normalize = normalize
        self.fixed_num = fixed_num

    def gen_vectorized_samples(
        self, location, ego2global_translation, ego2global_rotation
    ):
        map_pose = ego2global_translation[:2]
        rotation = Quaternion(ego2global_rotation)

        patch_box = (map_pose[0], map_pose[1], self.patch_size[0], self.patch_size[1])
        patch_angle = quaternion_yaw(rotation) / np.pi * 180

        line_geom = self.get_map_geom(
            patch_box, patch_angle, self.line_classes, location
        )
        line_vector_dict = self.line_geoms_to_vectors(line_geom)

        ped_geom = self.get_map_geom(
            patch_box, patch_angle, self.ped_crossing_classes, location
        )
        # ped_vector_list = self.ped_geoms_to_vectors(ped_geom)
        ped_vector_list = self.line_geoms_to_vectors(ped_geom)["ped_crossing"]

        polygon_geom = self.get_map_geom(
            patch_box, patch_angle, self.polygon_classes, location
        )
        poly_bound_list = self.poly_geoms_to_vectors(polygon_geom)

        vectors = []
        for line_type, vects in line_vector_dict.items():
            for line, length in vects:
                vectors.append(
                    (line.astype(float), length, CLASS2LABEL.get(line_type, -1))
                )

        for ped_line, length in ped_vector_list:
            vectors.append(
                (ped_line.astype(float), length, CLASS2LABEL.get("ped_crossing", -1))
            )

        for contour, length in poly_bound_list:
            vectors.append(
                (contour.astype(float), length, CLASS2LABEL.get("contours", -1))
            )

        # filter out -1: 用字典保存
        filtered_vectors = []
        for pts, pts_num, type in vectors:
            if type != -1:
                filtered_vectors.append({"pts": pts, "pts_num": pts_num, "type": type})

        return filtered_vectors

    def get_map_geom(self, patch_box, patch_angle, layer_names, location):
        map_geom = []
        for layer_name in layer_names:
            if layer_name in self.line_classes:
                geoms = self.map_explorer[location]._get_layer_line(
                    patch_box, patch_angle, layer_name
                )
                map_geom.append((layer_name, geoms))
            elif layer_name in self.polygon_classes:
                geoms = self.map_explorer[location]._get_layer_polygon(
                    patch_box, patch_angle, layer_name
                )
                map_geom.append((layer_name, geoms))
            elif layer_name in self.ped_crossing_classes:
                geoms = self.get_ped_crossing_line(patch_box, patch_angle, location)
                # geoms = self.map_explorer[location]._get_layer_polygon(patch_box, patch_angle, layer_name)
                map_geom.append((layer_name, geoms))
        return map_geom

    def _one_type_line_geom_to_vectors(self, line_geom):
        line_vectors = []
        for line in line_geom:
            if not line.is_empty:
                if line.geom_type == "MultiLineString":
                    # todo 这里处理，多线也都分成每个单线
                    for single_line in line.geoms:
                        line_vectors.append(self.sample_pts_from_line(single_line))
                elif line.geom_type == "LineString":
                    line_vectors.append(self.sample_pts_from_line(line))
                else:
                    raise NotImplementedError
        return line_vectors

    def poly_geoms_to_vectors(self, polygon_geom):
        # sharply库的简单使用: https://blog.csdn.net/jclian91/article/details/121887135
        roads = polygon_geom[0][1]
        lanes = polygon_geom[1][1]
        # unary_union: 返回给定几何对象的并集表示。重叠的多边形将被合并.线会溶解并结点, 重复的点将被合并
        union_roads = ops.unary_union(roads)
        union_lanes = ops.unary_union(lanes)
        union_segments = ops.unary_union([union_roads, union_lanes])
        max_x = self.patch_size[1] / 2
        max_y = self.patch_size[0] / 2
        local_patch = box(-max_x + 0.2, -max_y + 0.2, max_x - 0.2, max_y - 0.2)
        exteriors = []  # exteriors 外部边界点集
        interiors = []  # interiors 内部空洞点集

        if union_segments.geom_type != "MultiPolygon":
            union_segments = MultiPolygon([union_segments])
        for poly in union_segments.geoms:
            exteriors.append(poly.exterior)
            for inter in poly.interiors:
                interiors.append(inter)

        results = []
        # 参考: https://blog.csdn.net/ymzhu385/article/details/133613409
        ## is_ccw: 判断是否是逆时针的
        for ext in exteriors:
            if ext.is_ccw:
                # 倒叙输出（从后向前输出）
                ## a = '1234568910', while print([::-1]) == '0198654321'
                ## commit: 省略了start和end，只保留了步长(-1)，这句话的含义是将逆时针转为顺时针
                ext.coords = list(ext.coords)[::-1]
            # 与外边框相交，防止直线溢出
            lines = ext.intersection(local_patch)
            if isinstance(lines, MultiLineString):
                lines = ops.linemerge(lines)
            results.append(lines)

        for inter in interiors:
            if not inter.is_ccw:
                inter.coords = list(inter.coords)[::-1]
            lines = inter.intersection(local_patch)
            if isinstance(lines, MultiLineString):
                lines = ops.linemerge(lines)
            results.append(lines)

        return self._one_type_line_geom_to_vectors(results)

    def line_geoms_to_vectors(self, line_geom):
        line_vectors_dict = dict()
        for line_type, a_type_of_lines in line_geom:
            one_type_vectors = self._one_type_line_geom_to_vectors(a_type_of_lines)
            line_vectors_dict[line_type] = one_type_vectors

        return line_vectors_dict

    def ped_geoms_to_vectors(self, ped_geom):
        ped_geom = ped_geom[0][1]
        union_ped = ops.unary_union(ped_geom)
        if union_ped.geom_type != "MultiPolygon":
            union_ped = MultiPolygon([union_ped])

        max_x = self.patch_size[1] / 2
        max_y = self.patch_size[0] / 2
        local_patch = box(-max_x + 0.2, -max_y + 0.2, max_x - 0.2, max_y - 0.2)
        results = []
        for ped_poly in union_ped:
            # rect = ped_poly.minimum_rotated_rectangle
            ext = ped_poly.exterior
            if not ext.is_ccw:
                ext.coords = list(ext.coords)[::-1]
            lines = ext.intersection(local_patch)
            results.append(lines)

        return self._one_type_line_geom_to_vectors(results)

    # get_ped_crossing_line: 这个函数本质上将人行道的矩形框外观提取出来，只保留两根最长的直线
    def get_ped_crossing_line(self, patch_box, patch_angle, location):
        def add_line(poly_xy, idx, patch, patch_angle, patch_x, patch_y, line_list):
            # points: 获取索引对应的直线
            points = [
                (p0, p1)
                for p0, p1 in zip(poly_xy[0, idx : idx + 2], poly_xy[1, idx : idx + 2])
            ]
            line = LineString(points)
            line = line.intersection(patch)
            if not line.is_empty:
                line = affinity.rotate(
                    line, -patch_angle, origin=(patch_x, patch_y), use_radians=False
                )
                line = affinity.affine_transform(
                    line, [1.0, 0.0, 0.0, 1.0, -patch_x, -patch_y]
                )
                line_list.append(line)

        patch_x = patch_box[0]
        patch_y = patch_box[1]

        patch = NuScenesMapExplorer.get_patch_coord(patch_box, patch_angle)
        line_list = []
        # getattr() 函数用于返回一个对象属性值
        records = getattr(self.nusc_maps[location], "ped_crossing")
        for record in records:
            polygon = self.map_explorer[location].extract_polygon(
                record["polygon_token"]
            )
            # 返回numpy类型的外边界点
            poly_xy = np.array(polygon.exterior.xy)
            # poly_xy[:, 1:] 去掉第一个点（因为输出的格式就是第一个点绕完一圈后会重复一遍）
            # poly_xy[:, :-1] 去掉最后一个点
            # poly_xy[:, 1:] - poly_xy[:, :-1] 错位相减
            dist = np.square(poly_xy[:, 1:] - poly_xy[:, :-1]).sum(0)
            # np.argsort(dist): 将dist中的元素从小到大排列，将index(索引)输出
            # x1, x2: 最大的两个距离所对应的索引
            x1, x2 = np.argsort(dist)[-2:]

            add_line(poly_xy, x1, patch, patch_angle, patch_x, patch_y, line_list)
            add_line(poly_xy, x2, patch, patch_angle, patch_x, patch_y, line_list)

        return line_list

    def sample_pts_from_line(self, line):
        if self.fixed_num < 0:
            distances = np.arange(0, line.length, self.sample_dist)
            sampled_points = np.array(
                [list(line.interpolate(distance).coords) for distance in distances]
            ).reshape(-1, 2)
        else:
            # fixed number of points, so distance is line.length / self.fixed_num
            distances = np.linspace(0, line.length, self.fixed_num)
            sampled_points = np.array(
                [list(line.interpolate(distance).coords) for distance in distances]
            ).reshape(-1, 2)

        if self.normalize:
            sampled_points = sampled_points / np.array(
                [self.patch_size[1], self.patch_size[0]]
            )

        num_valid = len(sampled_points)

        if not self.padding or self.fixed_num > 0:
            # fixed num sample can return now!
            return sampled_points, num_valid

        # fixed distance sampling need padding!
        num_valid = len(sampled_points)

        # 裁减填充至固定大小
        if self.fixed_num < 0:
            if num_valid < self.num_samples:
                padding = np.zeros((self.num_samples - len(sampled_points), 2))
                sampled_points = np.concatenate([sampled_points, padding], axis=0)
            else:
                sampled_points = sampled_points[: self.num_samples, :]
                num_valid = self.num_samples

            if self.normalize:
                sampled_points = sampled_points / np.array(
                    [self.patch_size[1], self.patch_size[0]]
                )
                num_valid = len(sampled_points)

        return sampled_points, num_valid
