# -*- coding: utf-8 -*-
"""吸附模式特殊检测（2.1 新增）：悬挂端点、交叉未打断、无效几何、面积筛选、尖角/过密顶点、点过近。"""
import math
from collections import OrderedDict

from qgis.PyQt.QtCore import QVariant

from qgis.core import (
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsRectangle,
    QgsVectorLayer,
    QgsWkbTypes,
    QgsDistanceArea,
    QgsCoordinateTransform,
    QgsPointXY,
    QgsSpatialIndex,
    QgsUnitTypes,
)

try:
    from .cdet_memory_style import apply_memory_output_style
    from .cdet_output_tree import add_layer_to_output_tree
    from .cdet_category import iter_features
    from .cdet_field_naming import _layer_geom_class
    from .cdet_snap_special import (
        _gather_lines_workspace,
        _gather_points_workspace,
        _line_vertices_by_parts,
        _index_candidate_pairs,
        _snap_memory_output_basename,
        _unique_project_layer_name,
        evaluate_length_rule,
        SPECIAL_EXTRA_DEFAULTS,
    )
except ImportError:
    from cdet_memory_style import apply_memory_output_style
    from cdet_output_tree import add_layer_to_output_tree
    from cdet_category import iter_features
    from cdet_field_naming import _layer_geom_class
    from cdet_snap_special import (
        _gather_lines_workspace,
        _gather_points_workspace,
        _line_vertices_by_parts,
        _index_candidate_pairs,
        _snap_memory_output_basename,
        _unique_project_layer_name,
        evaluate_length_rule,
        SPECIAL_EXTRA_DEFAULTS,
    )
from .i18n import tr as _i18n_tr
from .qtutil import run_dialog, run_menu, qvariant_type, qtype_is, is_null_qvariant, AppMessageBox as QMessageBox


def _tr(t):
    return _i18n_tr(t)


QUALITY_EXTRA_DEFAULTS = SPECIAL_EXTRA_DEFAULTS


def _fail(iface, params, err, error_code=None):
    if params.get('_show_messages', True) and iface:
        QMessageBox.warning(iface.mainWindow(), _tr('提示'), err)
    ret = {'ok': False, 'error': err, 'spatial_mode': '__special__'}
    if error_code:
        ret['error_code'] = error_code
    return ret


def _done(layers_created, summary_lines):
    return {
        'ok': True,
        'results': {'layers_created': list(layers_created)},
        'spatial_mode': '__special__',
        'summary_lines': list(summary_lines),
    }


def _tolerance(params):
    try:
        tol = float(params.get('tolerance', 0) or 0)
    except (TypeError, ValueError):
        tol = 0.0
    return max(tol, 0.0)


def _float_param(params, key, lo=0.0):
    try:
        v = float(params.get(key, QUALITY_EXTRA_DEFAULTS[key]))
    except (TypeError, ValueError):
        v = float(QUALITY_EXTRA_DEFAULTS[key])
    return max(v, lo)


def _make_da(crs, project):
    da = QgsDistanceArea()
    da.setSourceCrs(crs, project.transformContext())
    try:
        da.setEllipsoid(crs.ellipsoidAcronym())
    except Exception:  # nosec B110
        pass
    return da


def _layers_of(target_layers, geom_classes):
    return [lyr for lyr in (target_layers or []) if _layer_geom_class(lyr) in geom_classes]


def _meters_to_map_units(meters, crs, ref_lat=0.0):
    """把米换算成图层坐标单位的搜索半径；地理坐标系按纬度放宽，最终仍以椭球距离复核。"""
    if crs.isGeographic():
        c = max(math.cos(math.radians(max(-89.0, min(89.0, ref_lat)))), 0.05)
        return meters / (111320.0 * c)
    try:
        f = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceUnit.DistanceMeters, crs.mapUnits())
    except Exception:
        f = 1.0
    return meters * f


def _output_tag_name(base, params):
    tag = (params.get('_output_tag') or '').strip()
    return base if not tag else '{0}_{1}'.format(base, tag)


def _write_point_layer(project, crs, base_name, params, fields, rows):
    """fields: [(name, QVariant 类型)]；rows: [(QgsPointXY, [属性...])]。返回图层名，无数据返回 None。"""
    if not rows:
        return None
    authid = crs.authid() if crs.isValid() else ''
    uri = 'Point?crs=%s' % authid if authid else 'Point'
    mem = QgsVectorLayer(uri, _unique_project_layer_name(project, _output_tag_name(base_name, params)), 'memory')
    if not mem.isValid():
        return None
    mem.dataProvider().addAttributes([QgsField(n, t) for n, t in fields])
    mem.updateFields()
    feats = []
    for pt, attrs in rows:
        f = QgsFeature(mem.fields())
        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(pt)))
        f.setAttributes(list(attrs))
        feats.append(f)
    mem.dataProvider().addFeatures(feats)
    mem.updateExtents()
    apply_memory_output_style(mem)
    add_layer_to_output_tree(project, mem)
    return mem.name()


def _write_feature_copies(project, params, snap_enabled, by_lyr, extra_fields=()):
    """by_lyr: OrderedDict[layer, list[(QgsFeature, 追加属性列表)]]，按原图层几何类型输出副本。"""
    names = []
    for lyr, items in by_lyr.items():
        if not items:
            continue
        uniq = _unique_project_layer_name(
            project, _snap_memory_output_basename(lyr.name(), params, snap_enabled)
        )
        type_str = QgsWkbTypes.displayString(lyr.wkbType()) or 'Point'
        authid = lyr.crs().authid()
        nf = QgsVectorLayer('{0}?crs={1}'.format(type_str, authid), uniq, 'memory')
        if not nf.isValid():
            continue
        prv = nf.dataProvider()
        base_fields = lyr.fields().toList()
        prv.addAttributes(base_fields + [QgsField(n, t) for n, t in extra_fields])
        nf.updateFields()
        n_base = len(base_fields)
        feats = []
        for rf, extra in items:
            ox = QgsFeature(nf.fields())
            al = list(rf.attributes())[:n_base]
            while len(al) < n_base:
                al.append(None)
            al.extend(list(extra)[:len(extra_fields)])
            while len(al) < nf.fields().count():
                al.append(None)
            ox.setAttributes(al)
            ox.setGeometry(rf.geometry())
            feats.append(ox)
        prv.addFeatures(feats)
        nf.updateExtents()
        apply_memory_output_style(nf)
        add_layer_to_output_tree(project, nf)
        names.append(nf.name())
    return names


def _xy_dist(a, b):
    return math.hypot(a.x() - b.x(), a.y() - b.y())


def _end_label(which, part_idx, n_parts):
    s = _tr('起点') if which == 0 else _tr('终点')
    return s if n_parts <= 1 else _tr('部件{0}{1}').format(part_idx + 1, s)


# ---------------------------------------------------------------- 悬挂端点

def _endpoint_loops_back(pts, which, tol):
    """端点是否绕回碰到本部件的线身（「6」字形），跳过端点附近 tol 范围内的顶点。"""
    seq = pts if which == 0 else list(reversed(pts))
    end = seq[0]
    k = 1
    while k < len(seq) and _xy_dist(seq[k], end) <= tol:
        k += 1
    rest = seq[k:]
    if len(rest) < 2:
        return False
    try:
        return QgsGeometry.fromPolylineXY(rest).distance(QgsGeometry.fromPointXY(end)) <= tol
    except Exception:
        return False


def run_line_dangles_snap(iface, project, target_layers, params):
    line_layers = _layers_of(target_layers, (QgsWkbTypes.GeometryType.LineGeometry,))
    if not line_layers:
        return _fail(iface, params, _tr('【拓扑】悬挂端点：请选择线图层'))
    tol = _tolerance(params)
    eff = tol if tol > 0 else 1e-9
    base_crs = line_layers[0].crs()
    geoms, meta = _gather_lines_workspace(line_layers, base_crs, project, params.get('_category_target'))
    index = QgsSpatialIndex()
    stubs = []
    for i, g in geoms.items():
        stub = QgsFeature(int(i))
        stub.setGeometry(g)
        stubs.append(stub)
    from .qtutil import add_index_features
    add_index_features(index, stubs)

    rows = []
    for i in sorted(geoms.keys()):
        lyr, fid = meta[i]
        parts = _line_vertices_by_parts(geoms[i])
        part_geoms = [QgsGeometry.fromPolylineXY(p) for p in parts]
        for pi, pts in enumerate(parts):
            closed = _xy_dist(pts[0], pts[-1]) <= eff
            for which in (0, 1):
                end = pts[0] if which == 0 else pts[-1]
                if closed:
                    continue
                pg = QgsGeometry.fromPointXY(end)
                linked = False
                for pj, og in enumerate(part_geoms):
                    if pj != pi and og.distance(pg) <= eff:
                        linked = True
                        break
                if not linked:
                    linked = _endpoint_loops_back(pts, which, eff)
                if not linked:
                    rect = QgsRectangle(end.x() - eff, end.y() - eff, end.x() + eff, end.y() + eff)
                    for j in index.intersects(rect):
                        if j != i and j in geoms and geoms[j].distance(pg) <= eff:
                            linked = True
                            break
                if not linked:
                    rows.append((end, [lyr.name(), int(fid), _end_label(which, pi, len(parts))]))

    name = _write_point_layer(
        project, base_crs, _tr('悬挂端点'), params,
        [('图层', qvariant_type("String")), ('来源FID', qvariant_type("LongLong")), ('端', qvariant_type("String"))],
        rows,
    )
    return _done([name] if name else [], [_tr('悬挂端点：共 {0} 个').format(len(rows))])


# ---------------------------------------------------------------- 交叉未打断

def _intersection_points(inter):
    out = []
    if inter is None or inter.isEmpty():
        return out
    try:
        parts = inter.asGeometryCollection() if inter.isMultipart() or \
            QgsWkbTypes.flatType(inter.wkbType()) == QgsWkbTypes.Type.GeometryCollection else [inter]
    except Exception:
        parts = [inter]
    for p in parts:
        if p.type() != QgsWkbTypes.GeometryType.PointGeometry:
            continue
        if p.isMultipart():
            out.extend(QgsPointXY(q) for q in p.asMultiPoint())
        else:
            out.append(QgsPointXY(p.asPoint()))
    return out


def _has_vertex_near(parts, pt, tol):
    return any(_xy_dist(v, pt) <= tol for pts in parts for v in pts)


def run_line_cross_nonode_snap(iface, project, target_layers, params):
    line_layers = _layers_of(target_layers, (QgsWkbTypes.GeometryType.LineGeometry,))
    if not line_layers:
        return _fail(iface, params, _tr('【拓扑】交叉未打断：请选择线图层'))
    tol = _tolerance(params)
    eff = tol if tol > 0 else 1e-9
    base_crs = line_layers[0].crs()
    geoms, meta = _gather_lines_workspace(line_layers, base_crs, project, params.get('_category_target'))
    verts = {i: _line_vertices_by_parts(g) for i, g in geoms.items()}

    rows = []
    for i, j in _index_candidate_pairs(geoms, 0.0):
        lyr1, fid1 = meta[i]
        lyr2, fid2 = meta[j]
        if lyr1.id() == lyr2.id() and fid1 == fid2:
            continue
        try:
            inter = geoms[i].intersection(geoms[j])
        except Exception:  # nosec B112
            continue
        seen = []
        for pt in _intersection_points(inter):
            if any(_xy_dist(pt, s) <= eff for s in seen):
                continue
            seen.append(pt)
            ok1 = _has_vertex_near(verts[i], pt, eff)
            ok2 = _has_vertex_near(verts[j], pt, eff)
            if ok1 and ok2:
                continue
            miss = _tr('两条线') if not ok1 and not ok2 else (_tr('线1') if not ok1 else _tr('线2'))
            rows.append((pt, [lyr1.name(), int(fid1), lyr2.name(), int(fid2), miss]))

    name = _write_point_layer(
        project, base_crs, _tr('交叉未打断'), params,
        [('图层1', qvariant_type("String")), ('FID1', qvariant_type("LongLong")),
         ('图层2', qvariant_type("String")), ('FID2', qvariant_type("LongLong")), ('缺节点', qvariant_type("String"))],
        rows,
    )
    return _done([name] if name else [], [_tr('交叉未打断：共 {0} 处').format(len(rows))])


# ---------------------------------------------------------------- 无效几何

def _geos_validation_errors(g):
    engine = None
    try:
        from qgis.core import Qgis
        engine = Qgis.GeometryValidationEngine.Geos
    except Exception:
        engine = getattr(QgsGeometry, 'ValidatorGeos', None)
    try:
        return list(g.validateGeometry(engine) if engine is not None else g.validateGeometry())
    except Exception:
        return []


def _part_count(g):
    try:
        return int(g.constGet().partCount())
    except Exception:
        return 1


def geometry_problems(g, check_multipart=False):
    """返回 [(问题文字, QgsPointXY 或 None)]；没有问题返回空列表。"""
    if g is None or g.isNull() or g.isEmpty():
        return [(_tr('空几何'), None)]
    out = []
    for err in _geos_validation_errors(g):
        where = None
        try:
            if err.hasWhere():
                where = QgsPointXY(err.where())
        except Exception:  # nosec B110
            pass
        out.append((str(err.what()) or _tr('几何无效'), where))
    gt = g.type()
    if gt == QgsWkbTypes.GeometryType.LineGeometry:
        try:
            if g.length() <= 0:
                out.append((_tr('长度为0'), None))
            elif not g.isSimple():
                out.append((_tr('线自相交'), None))
        except Exception:  # nosec B110
            pass
    elif gt == QgsWkbTypes.GeometryType.PolygonGeometry and not out:
        try:
            if g.area() <= 0:
                out.append((_tr('面积为0'), None))
        except Exception:  # nosec B110
            pass
    if check_multipart and g.isMultipart() and _part_count(g) > 1:
        out.append((_tr('多部件（{0}个）').format(_part_count(g)), None))
    return out


def run_geom_validity_snap(iface, project, target_layers, params):
    layers = [lyr for lyr in (target_layers or []) if _layer_geom_class(lyr) is not None]
    if not layers:
        return _fail(iface, params, _tr('【质检】无效几何：请选择矢量图层'))
    snap_enabled = bool(params.get('snap_enabled', False))
    check_multi = bool(params.get('_validity_multipart', False))
    base_crs = layers[0].crs()
    by_lyr = OrderedDict()
    loc_rows = []
    n_bad = 0
    for lyr in layers:
        xf = QgsCoordinateTransform(lyr.crs(), base_crs, project) if lyr.crs() != base_crs else None
        items = []
        for f in iter_features(lyr, params.get('_category_target')):
            probs = geometry_problems(QgsGeometry(f.geometry()), check_multi)
            if probs:
                n_bad += 1
                for text, where in probs:
                    if where is None:
                        continue
                    pt = where
                    if xf is not None:
                        try:
                            pt = xf.transform(where)
                        except Exception:  # nosec B112
                            continue
                    loc_rows.append((pt, [lyr.name(), int(f.id()), text]))
            if bool(probs) == snap_enabled:
                items.append((f, ['；'.join(t for t, _ in probs)] if snap_enabled else []))
        by_lyr[lyr] = items

    extra = [('CDET_问题', qvariant_type("String"))] if snap_enabled else []
    names = _write_feature_copies(project, params, snap_enabled, by_lyr, extra)
    loc_name = _write_point_layer(
        project, base_crs, _tr('无效几何位置'), params,
        [('图层', qvariant_type("String")), ('来源FID', qvariant_type("LongLong")), ('问题', qvariant_type("String"))],
        loc_rows,
    )
    if loc_name:
        names.append(loc_name)
    return _done(names, [_tr('无效几何：有问题的要素 {0} 个，可定位的问题点 {1} 个').format(n_bad, len(loc_rows))])


# ---------------------------------------------------------------- 面积筛选

def run_poly_area_snap(iface, project, target_layers, params):
    poly_layers = _layers_of(target_layers, (QgsWkbTypes.GeometryType.PolygonGeometry,))
    if not poly_layers:
        return _fail(iface, params, _tr('【筛选】按面积筛选：请选择面图层'))
    snap_enabled = bool(params.get('snap_enabled', False))
    rule = params.get('_poly_area_rule') or dict(QUALITY_EXTRA_DEFAULTS['_poly_area_rule'])
    base_crs = poly_layers[0].crs()
    da = _make_da(base_crs, project)
    by_lyr = OrderedDict()
    total = 0
    for lyr in poly_layers:
        xf = QgsCoordinateTransform(lyr.crs(), base_crs, project) if lyr.crs() != base_crs else None
        items = []
        for f in iter_features(lyr, params.get('_category_target')):
            g = QgsGeometry(f.geometry())
            area = None
            if not g.isEmpty():
                try:
                    if xf is not None:
                        g.transform(xf)
                    area = float(da.measureArea(g))
                except Exception:
                    area = None
            ok = evaluate_length_rule(area, rule)
            if ok == snap_enabled:
                items.append((f, [area]))
        total += len(items)
        by_lyr[lyr] = items
    names = _write_feature_copies(project, params, snap_enabled, by_lyr, [('面积_m2', qvariant_type("Double"))])
    return _done(names, [_tr('按面积筛选：输出面要素 {0} 个').format(total)])


# ---------------------------------------------------------------- 尖角 / 过密顶点

def _gather_any_workspace(layers, base_crs, project, category_filters=None):
    out = []
    for lyr in layers:
        xf = QgsCoordinateTransform(lyr.crs(), base_crs, project) if lyr.crs() != base_crs else None
        for f in iter_features(lyr, category_filters):
            g = QgsGeometry(f.geometry())
            if g.isEmpty():
                continue
            if xf is not None:
                try:
                    g.transform(xf)
                except Exception:  # nosec B112
                    continue
            out.append((lyr, int(f.id()), g))
    return out


def _vertex_sequences(g):
    """[(顶点列表, 是否闭合环)]。面：每个环（去掉重复的闭合点）；线：每个部件。"""
    try:
        if QgsWkbTypes.isCurvedType(g.wkbType()):
            g = QgsGeometry(g.constGet().segmentize())
    except Exception:  # nosec B110
        pass
    seqs = []
    if g.type() == QgsWkbTypes.GeometryType.PolygonGeometry:
        try:
            polys = g.asMultiPolygon() if g.isMultipart() else [g.asPolygon()]
        except Exception:
            polys = []
        for poly in polys:
            for ring in poly:
                pts = [QgsPointXY(p) for p in ring]
                if len(pts) >= 2 and pts[0] == pts[-1]:
                    pts = pts[:-1]
                if len(pts) >= 3:
                    seqs.append((pts, True))
    elif g.type() == QgsWkbTypes.GeometryType.LineGeometry:
        for pts in _line_vertices_by_parts(g):
            closed = len(pts) >= 4 and pts[0] == pts[-1]
            seqs.append((pts[:-1] if closed else pts, closed))
    return seqs


def _vertex_angle_deg(prev, cur, nxt, geographic):
    sx = math.cos(math.radians(cur.y())) if geographic else 1.0
    ax, ay = (prev.x() - cur.x()) * sx, prev.y() - cur.y()
    bx, by = (nxt.x() - cur.x()) * sx, nxt.y() - cur.y()
    la, lb = math.hypot(ax, ay), math.hypot(bx, by)
    if la <= 0 or lb <= 0:
        return None
    c = max(-1.0, min(1.0, (ax * bx + ay * by) / (la * lb)))
    return math.degrees(math.acos(c))


def vertex_quality_issues(pts, closed, spike_deg, dense_m, da, geographic):
    """返回 [(QgsPointXY, 问题, 角度或None, 间距或None)]。"""
    out = []
    n = len(pts)
    seg_count = n if closed else n - 1
    for k in range(seg_count):
        a, b = pts[k], pts[(k + 1) % n]
        try:
            d = 0.0 if a == b else float(da.measureLine(a, b))
        except Exception:
            d = _xy_dist(a, b)
        if d <= 0:
            out.append((b, _tr('重复顶点'), None, 0.0))
        elif d < dense_m:
            out.append((b, _tr('过密顶点'), None, d))
    if spike_deg > 0:
        uniq = [pts[0]]
        for p in pts[1:]:
            if p != uniq[-1]:
                uniq.append(p)
        if closed and len(uniq) > 1 and uniq[0] == uniq[-1]:
            uniq.pop()
        m = len(uniq)
        idx = range(m) if closed else range(1, m - 1)
        if m >= 3:
            for k in idx:
                ang = _vertex_angle_deg(uniq[k - 1], uniq[k], uniq[(k + 1) % m], geographic)
                if ang is not None and ang < spike_deg:
                    out.append((uniq[k], _tr('回头线') if ang < 1.0 else _tr('尖角'), ang, None))
    return out


def run_vertex_quality_snap(iface, project, target_layers, params):
    layers = _layers_of(target_layers, (QgsWkbTypes.GeometryType.LineGeometry, QgsWkbTypes.GeometryType.PolygonGeometry))
    if not layers:
        return _fail(iface, params, _tr('【质检】尖角 / 回头线 / 过密顶点：请选择线或面图层'))
    spike = _float_param(params, '_spike_angle')
    dense = _float_param(params, '_dense_min_dist')
    base_crs = layers[0].crs()
    da = _make_da(base_crs, project)
    geographic = base_crs.isGeographic()
    rows = []
    for lyr, fid, g in _gather_any_workspace(layers, base_crs, project, params.get('_category_target')):
        for pts, closed in _vertex_sequences(g):
            for pt, what, ang, dist in vertex_quality_issues(pts, closed, spike, dense, da, geographic):
                rows.append((pt, [lyr.name(), fid, what, ang, dist]))
    name = _write_point_layer(
        project, base_crs, _tr('顶点问题'), params,
        [('图层', qvariant_type("String")), ('来源FID', qvariant_type("LongLong")), ('问题', qvariant_type("String")),
         ('角度_度', qvariant_type("Double")), ('间距_m', qvariant_type("Double"))],
        rows,
    )
    counts = OrderedDict()
    for _pt, attrs in rows:
        counts[attrs[2]] = counts.get(attrs[2], 0) + 1
    detail = '，'.join('{0} {1}'.format(k, v) for k, v in counts.items()) or _tr('无')
    return _done([name] if name else [], [_tr('顶点问题：共 {0} 处（{1}）').format(len(rows), detail)])


# ---------------------------------------------------------------- 点过近

def run_point_near_snap(iface, project, target_layers, params):
    pt_layers = _layers_of(target_layers, (QgsWkbTypes.GeometryType.PointGeometry,))
    if not pt_layers:
        return _fail(iface, params, _tr('【距离】点与点过近：请选择点图层'))
    snap_enabled = bool(params.get('snap_enabled', False))
    near_m = _float_param(params, '_near_dist_m')
    include_same = bool(params.get('_near_include_same', False))
    tol = _tolerance(params)
    base_crs = pt_layers[0].crs()
    da = _make_da(base_crs, project)
    pts = _gather_points_workspace(pt_layers, base_crs, project, params.get('_category_target'))

    index = QgsSpatialIndex()
    stubs = []
    for n, (_lyr, _fid, p) in enumerate(pts):
        stub = QgsFeature(n)
        stub.setGeometry(QgsGeometry.fromPointXY(p))
        stubs.append(stub)
    from .qtutil import add_index_features
    add_index_features(index, stubs)

    best = {}
    for n, (lyr, fid, p) in enumerate(pts):
        r = _meters_to_map_units(near_m, base_crs, p.y()) * (1.5 if base_crs.isGeographic() else 1.0)
        r = max(r, 1e-12)
        for m in index.intersects(QgsRectangle(p.x() - r, p.y() - r, p.x() + r, p.y() + r)):
            if m == n:
                continue
            lyr2, fid2, q = pts[m]
            if lyr2.id() == lyr.id() and fid2 == fid:
                continue
            if not include_same and _xy_dist(p, q) <= tol:
                continue
            try:
                d = float(da.measureLine(p, q))
            except Exception:
                d = _xy_dist(p, q)
            if d > near_m:
                continue
            key = (lyr.id(), fid)
            if key not in best or d < best[key][0]:
                best[key] = (d, lyr2.name(), int(fid2))

    by_lyr = OrderedDict()
    hit_n = 0
    for lyr in pt_layers:
        items = []
        for f in iter_features(lyr, params.get('_category_target')):
            hit = best.get((lyr.id(), int(f.id())))
            if hit is not None:
                hit_n += 1
            if (hit is not None) == snap_enabled:
                items.append((f, list(hit) if hit is not None else []))
        by_lyr[lyr] = items
    extra = [('最近距离_m', qvariant_type("Double")), ('最近图层', qvariant_type("String")), ('最近FID', qvariant_type("LongLong"))]
    names = _write_feature_copies(project, params, snap_enabled, by_lyr, extra if snap_enabled else [])
    return _done(names, [_tr('点与点过近：{0} 个点在 {1:g} 米内有别的点').format(hit_n, near_m)])


QUALITY_RUNNERS = {
    'line_dangles': lambda iface, project, t, r, p: run_line_dangles_snap(iface, project, t, p),
    'line_cross_nonode': lambda iface, project, t, r, p: run_line_cross_nonode_snap(iface, project, t, p),
    'geom_validity': lambda iface, project, t, r, p: run_geom_validity_snap(iface, project, t, p),
    'poly_area': lambda iface, project, t, r, p: run_poly_area_snap(iface, project, t, p),
    'vertex_quality': lambda iface, project, t, r, p: run_vertex_quality_snap(iface, project, t, p),
    'point_near': lambda iface, project, t, r, p: run_point_near_snap(iface, project, t, p),
}
