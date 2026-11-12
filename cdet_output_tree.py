# -*- coding: utf-8 -*-
"""临时矢量图层归入图层树：「输出图层」下分子组。"""
from qgis.core import QgsProject, QgsVectorLayer, QgsLayerTreeLayer, QgsWkbTypes

from .i18n import tr as _i18n_tr

# Source titles (Chinese). Display goes through tr(); findGroup also tries the
# source name so existing projects keep their groups after a language switch.
ROOT_GROUP = '输出图层'
GROUP_POINT = '点'
GROUP_LINE = '线'
GROUP_POLYGON = '面'
GROUP_POLYGON_INSPECT = '面检测'


def _find_or_create_group(parent, title_src, index=0):
    title = _i18n_tr(title_src)
    group = parent.findGroup(title)
    if group is not None:
        return group
    if title != title_src:
        group = parent.findGroup(title_src)
        if group is not None:
            try:
                group.setName(title)
            except Exception:
                pass
            return group
    return parent.insertGroup(index, title)


def _geom_subfolder(geom_type):
    if geom_type == QgsWkbTypes.PointGeometry:
        return GROUP_POINT
    if geom_type == QgsWkbTypes.LineGeometry:
        return GROUP_LINE
    return GROUP_POLYGON


def add_layer_to_output_tree(project: QgsProject, layer: QgsVectorLayer, placement='geometry'):
    """placement: 'geometry' 按点/线/面；'polygon_inspect' 归入「面检测」子文件夹（与吸附结果并列第 4 类）"""
    if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
        return
    root = project.layerTreeRoot()
    top = _find_or_create_group(root, ROOT_GROUP, 0)
    if placement == 'polygon_inspect':
        title_src = GROUP_POLYGON_INSPECT
    else:
        title_src = _geom_subfolder(layer.geometryType())
    sub = _find_or_create_group(top, title_src, 0)
    project.addMapLayer(layer, False)
    sub.insertChildNode(0, QgsLayerTreeLayer(layer))
