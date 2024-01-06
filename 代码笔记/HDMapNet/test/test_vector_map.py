import numpy as np
from nuscenes import NuScenes
from nuscenes.map_expansion.map_api import NuScenesMap, NuScenesMapExplorer
from nuscenes.eval.common.utils import quaternion_yaw, Quaternion

if __name__ == '__main__':
    dataroot = '/home/idriver/learning/'
    # nusc = NuScenes(version='v1.0-mini', dataroot=dataroot, verbose=True)
    nusc_map = NuScenesMap(dataroot, map_name='singapore-onenorth')
    nusc_map_explorer = NuScenesMapExplorer(nusc_map)
