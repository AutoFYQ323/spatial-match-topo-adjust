# -*- coding: utf-8 -*-
"""改编自 EXP.txt：面重叠、内部孔洞、面间间隙与合并后的要素索引映射。"""
from qgis.core import (
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsSpatialIndex,
    QgsRectangle,
    QgsDistanceArea,
    QgsCoordinateTransform,
    QgsWkbTypes,
)

try:
    from .cdet_category import iter_features
except ImportError:
    from cdet_category import iter_features


def gather_polygon_workspace(layers, base_crs, project, category_filters=None):
    """
    将所有目标图层多边形统一到 base_crs，返回：
    valid_geoms: idx(int)->QgsGeometry（已 makeValid）
    meta: idx(int)->(QgsVectorLayer, source_fid, layer_display_name)
    extent:QgsRectangle 联合范围
    """
    valid_geoms = {}
    meta = {}
    xf_cache = {}

    extent = QgsRectangle()
    extent.setMinimal()

    idx_key = -1
    stubs = []

    def _xf(lyr):
        if lyr.crs() == base_crs:
            return None
        k = lyr.crs().authid()
        if k not in xf_cache:
            xf_cache[k] = QgsCoordinateTransform(lyr.crs(), base_crs, project)
        return xf_cache[k]

    idx = QgsSpatialIndex()
    ii = 0
    for lyr in layers:
        xf = _xf(lyr)
        for f in iter_features(lyr, category_filters):
            g = QgsGeometry(f.geometry())
            if g.isEmpty():
                continue
            if xf:
                try:
                    g.transform(xf)
                except Exception:  # nosec B112
                    continue
            if not g.isGeosValid():
                gm = g.makeValid()
                g = gm if gm and not gm.isEmpty() else g
            if g.isEmpty():
                continue
            r = g.boundingBox()
            extent.combineExtentWith(r)

            fid_map = ii
            ii += 1
            valid_geoms[fid_map] = g
            meta[fid_map] = (lyr, int(f.id()), lyr.name())

            stub = QgsFeature(fid_map)
            stub.setGeometry(g)
            stubs.append(stub)
    try:
        from .qtutil import add_index_features
    except ImportError:
        from qtutil import add_index_features
    add_index_features(idx, stubs)
    return valid_geoms, meta, extent, idx


def intersecting_feature_pairs(valid_geoms, idx, tolerance_m2, distance_area):
    """与原 API 兼容：返回不重复的 (fid,cid,相交面积摘要㎡)；面积取该对要素各片段中最大的一块。"""
    details = intersecting_overlap_details(valid_geoms, idx, tolerance_m2, distance_area)
    best_area = {}
    for fid, cid, a_m2, _geom, _pidx in details:
        key = tuple(sorted((fid, cid)))
        if a_m2 > best_area.get(key, 0):
            best_area[key] = a_m2
    return [(k[0], k[1], v) for k, v in sorted(best_area.items())]


def _polygon_parts_of_intersection(inter):
    """将面相交结果拆成单独的多边形片段（单部/多部）。"""
    if inter.isEmpty() or inter.type() != QgsWkbTypes.GeometryType.PolygonGeometry:
        return []
    out = []
    try:
        if inter.isMultipart():
            for poly in inter.asMultiPolygon():
                pg = QgsGeometry.fromPolygonXY(poly)
                if pg and not pg.isEmpty():
                    out.append(pg)
        else:
            out.append(QgsGeometry(inter))
    except Exception:  # nosec B110
        pass
    return out


def _geom_boundary(geom):
    """与 666 一致：polygon 外边线转为线几何。"""
    if geom is None or geom.isEmpty():
        return None
    try:
        c = geom.constGet()
        if c:
            b = c.boundary()
            if b:
                return QgsGeometry(b)
    except Exception:  # nosec B110
        pass
    try:
        bn = geom.boundary()
        if bn and not bn.isEmpty():
            return bn
    except Exception:  # nosec B110
        pass
    return None


def intersecting_overlap_details(valid_geoms, idx, tolerance_m2, distance_area):
    """参考 666：每对相交要素输出 ≥ 容差的相交面片段，含几何。"""
    details = []
    processed_pairs = set()
    for fid in sorted(valid_geoms.keys()):
        geom = valid_geoms.get(fid)
        if not geom:
            continue
        for cid in idx.intersects(geom.boundingBox()):
            cid = int(cid)
            if cid <= fid:
                continue
            nog = valid_geoms.get(cid)
            if not nog or not geom.intersects(nog):
                continue
            pair_key = tuple(sorted((fid, cid)))
            if pair_key in processed_pairs:
                continue
            processed_pairs.add(pair_key)
            inter = geom.intersection(nog)
            if inter.isEmpty():
                continue
            if not inter.isGeosValid():
                mv = inter.makeValid()
                inter = mv if mv and not mv.isEmpty() else inter
            if inter.isEmpty():
                continue
            piece_idx = 0
            for g_piece in _polygon_parts_of_intersection(inter):
                try:
                    a_m2 = abs(distance_area.measureArea(g_piece))
                except Exception:
                    a_m2 = abs(g_piece.area()) if hasattr(g_piece, 'area') else 0
                if a_m2 <= tolerance_m2:
                    continue
                details.append((fid, cid, a_m2, QgsGeometry(g_piece), piece_idx))
                piece_idx += 1
    return details


def detect_holes_gaps(valid_geoms, layer_extent_rect, tolerance_m2, distance_area):
    """
    holes: [(面积㎡, 孔洞几何), ...]，来自合并后 multipart 的内环。
    gaps: [(面积㎡, 几何, is_outer), ...]，is_outer 与 666 一致：与外扩范围边界
    （shrink_bbox 外边）触点长度超过阈值的片状空隙视为制图范围外侧留白，常为正常；
    False 的为斑块间的「内部空隙」倾向需关注。
    """
    holes = []
    gaps = []
    unioned = None

    ordered = sorted(valid_geoms.keys())
    for fid in ordered:
        geom = valid_geoms.get(fid)
        if not geom:
            continue
        try:
            if unioned is None:
                unioned = QgsGeometry(geom)
            else:
                cg = unioned.combine(geom)
                unioned = cg if cg and not cg.isEmpty() else unioned.union(geom)
        except Exception:
            try:
                unioned = geom if unioned is None else unioned.union(geom)
            except Exception:
                unioned = unioned

    if unioned and not unioned.isEmpty():
        polys = unioned.asMultiPolygon() if unioned.isMultipart() else [unioned.asPolygon()]
        for poly in polys:
            if not poly:
                continue
            for hole_ring in poly[1:]:
                hole_geom = QgsGeometry.fromPolygonXY([[QgsPointXY(pt.x(), pt.y()) for pt in hole_ring]])
                try:
                    a_m2 = abs(distance_area.measureArea(hole_geom))
                except Exception:
                    a_m2 = hole_geom.area()
                if a_m2 > tolerance_m2:
                    holes.append((a_m2, hole_geom))

    if unioned and not unioned.isEmpty():
        bw = layer_extent_rect.width()
        bh = layer_extent_rect.height()
        buffer_dist = max((bw + bh) * 0.01, 1e-9)
        shrink_extent = QgsRectangle(
            layer_extent_rect.xMinimum() + buffer_dist,
            layer_extent_rect.yMinimum() + buffer_dist,
            layer_extent_rect.xMaximum() - buffer_dist,
            layer_extent_rect.yMaximum() - buffer_dist,
        )
        shrink_geom = QgsGeometry.fromRect(shrink_extent)
        try:
            gap_geom = shrink_geom.difference(unioned)
        except Exception:
            gap_geom = QgsGeometry()
        if not gap_geom.isEmpty():
            shrink_boundary = _geom_boundary(shrink_geom)
            min_edge = 1e-6
            gap_polys = gap_geom.asMultiPolygon() if gap_geom.isMultipart() else [gap_geom.asPolygon()]
            for poly in gap_polys:
                if not poly or not poly[0]:
                    continue
                gap_single = QgsGeometry.fromPolygonXY([[QgsPointXY(pt.x(), pt.y()) for pt in poly[0]]])
                try:
                    a_m2 = abs(distance_area.measureArea(gap_single))
                except Exception:
                    a_m2 = gap_single.area()
                if a_m2 <= tolerance_m2:
                    continue
                is_outer = False
                try:
                    gap_b = _geom_boundary(gap_single)
                    if gap_b and shrink_boundary and not shrink_boundary.isEmpty():
                        touch = gap_b.intersection(shrink_boundary)
                        if touch and not touch.isEmpty():
                            ln = abs(distance_area.measureLength(touch))
                            if ln > min_edge:
                                is_outer = True
                except Exception:  # nosec B110
                    pass
                gaps.append((a_m2, gap_single, is_outer))

    return holes, gaps


def hit_ids_from_overlap_pairs(overlap_pairs):
    ids = set()
    for fid, cid, _ in overlap_pairs:
        ids.add(fid)
        ids.add(cid)
    return ids
