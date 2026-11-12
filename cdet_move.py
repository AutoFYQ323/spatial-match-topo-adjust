# -*- coding: utf-8 -*-
"""CDET 移动模式：整要素平移（先预览再写回）。

移动方式全部在「移动模式」里按被移图层、参考图层的点／线／面组合列出。
两种选参考要素的办法：
- lock：容差内按要素整体距离取最近的一个，再对齐到它的某个位置（位置可以比容差更远）
- near：在容差内比较这种位置本身，取离被移位置最近的一个（位置必须在容差内）
不改吸附检测／字段命名逻辑。
"""
from __future__ import annotations

import time

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QProgressDialog
from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsWkbTypes,
    QgsCoordinateTransform,
)

try:
    from .cdet_field_naming import _build_ref_state, _rect_grow, _layer_geom_class
    from .cdet_category import iter_features
except ImportError:
    from cdet_field_naming import _build_ref_state, _rect_grow, _layer_geom_class
    from cdet_category import iter_features

try:
    from .cdet_memory_style import apply_memory_output_style
except ImportError:
    try:
        from cdet_memory_style import apply_memory_output_style
    except ImportError:
        def apply_memory_output_style(_layer):
            return None

from .i18n import tr as _i18n_tr
from .qtutil import run_dialog, run_menu, AppMessageBox as QMessageBox


def tr(text):
    return _i18n_tr(text)


def _preview_suffix():
    return tr('_移动预览')
PREVIEW_FLAG = '_cdet_move_preview'


def _unique_layer_name(project, base_name):
    names = {lyr.name() for lyr in project.mapLayers().values()}
    if base_name not in names:
        return base_name
    i = 2
    while f'{base_name}_{i}' in names:
        i += 1
    return f'{base_name}_{i}'


def _create_memory_layer(name, geom_type, crs, fields):
    type_map = {
        QgsWkbTypes.PointGeometry: 'Point',
        QgsWkbTypes.LineGeometry: 'LineString',
        QgsWkbTypes.PolygonGeometry: 'Polygon',
    }
    type_str = type_map.get(geom_type, 'Point')
    uri = f'{type_str}?crs={crs.authid()}'
    layer = QgsVectorLayer(uri, name, 'memory')
    if fields and fields.count() > 0:
        layer.dataProvider().addAttributes(fields.toList())
        layer.updateFields()
    return layer


def _shortest_delta(tg, rg):
    """整要素平移向量：最短连线终点 − 起点（目标上最近点 → 参考上最近点）。"""
    if tg is None or rg is None or tg.isEmpty() or rg.isEmpty():
        return None
    try:
        sl = tg.shortestLine(rg)
    except Exception:
        sl = None
    if sl is None or sl.isEmpty():
        return None
    try:
        pts = sl.asPolyline()
    except Exception:
        pts = None
    if not pts or len(pts) < 2:
        try:
            # Multi / Curve fallback
            pts = []
            for p in sl.vertices():
                pts.append(p)
            if len(pts) < 2:
                return None
            # QgsPoint → treat as XY
            p0, p1 = pts[0], pts[-1]
            return (float(p1.x()) - float(p0.x()), float(p1.y()) - float(p0.y()), float(sl.length()))
        except Exception:
            return None
    p0, p1 = pts[0], pts[-1]
    try:
        length = float(sl.length())
    except Exception:
        length = ((p1.x() - p0.x()) ** 2 + (p1.y() - p0.y()) ** 2) ** 0.5
    return (float(p1.x()) - float(p0.x()), float(p1.y()) - float(p0.y()), length)


def _best_translate_for_feature(tg, ref_entries, ref_idx, tol, exclude_layer_id=None, exclude_fid=None):
    """在容差内找最近参考，返回 (dx, dy, dist) 或 None。整要素单一平移，不改顶点拓扑。"""
    if tg is None or tg.isEmpty() or not ref_entries:
        return None
    tol = float(tol)
    if tol <= 0:
        return None
    try:
        rect = _rect_grow(tg.boundingBox(), tol)
        cand_ids = list(ref_idx.intersects(rect))
    except Exception:
        cand_ids = list(range(len(ref_entries)))
    best = None  # (dist, dx, dy)
    for cid in cand_ids:
        if cid < 0 or cid >= len(ref_entries):
            continue
        e = ref_entries[cid]
        if exclude_layer_id is not None and exclude_fid is not None:
            if e['layer'].id() == exclude_layer_id and int(e['fid']) == int(exclude_fid):
                continue
        rg = e['geom']
        try:
            d = float(tg.distance(rg))
        except Exception:
            continue
        if d > tol:
            continue
        delta = _shortest_delta(tg, rg)
        if delta is None:
            continue
        dx, dy, slen = delta
        use_d = slen if slen is not None else d
        if use_d > tol:
            continue
        if best is None or use_d < best[0]:
            best = (use_d, dx, dy)
    if best is None:
        return None
    dist, dx, dy = best
    if abs(dx) < 1e-15 and abs(dy) < 1e-15:
        return None  # already snapped
    return dx, dy, dist


_P = QgsWkbTypes.PointGeometry
_L = QgsWkbTypes.LineGeometry
_G = QgsWkbTypes.PolygonGeometry

# 锚点落在要素几何上时，近距模式可以用要素距离提前剔除（几何中心可能在面外，不能这么剔）。
_ANCHOR_ON_GEOM = frozenset({
    'geom', 'start', 'end', 'mid', 'endpt', 'vertex', 'inner', 'boundary', 'center',
})

_LINE_ANCHORS = ('geom', 'start', 'end', 'mid', 'endpt', 'vertex', 'inner')
_POLY_ANCHORS = ('geom', 'center', 'centroid', 'boundary', 'vertex')
_POINT_ANCHORS = ('geom',)

_ANCHORS_FOR = {
    _P: _POINT_ANCHORS,
    _L: _LINE_ANCHORS,
    _G: _POLY_ANCHORS,
}

_GEOM_LETTER = {_P: 'p', _L: 'l', _G: 'g'}
_GEOM_NOUN = {}
_CATALOG_READY = False
_MOVE_BY_CODE = {}
_MOVE_CHOICES = {}

_STANDARD_SPEC = {
    'code': 'standard',
    'policy': 'lock',
    'src': 'geom',
    'dst': 'geom',
    't': None,
    'r': None,
}

# Existing line-line codes kept in the dropdown and accepted on import/run.
# Other ll_* codes stay in the catalog and keep their function bodies, but
# line-line selection, import, and execution reject them instead of remapping.
LINE_LINE_ALLOWED_MODES = frozenset((
    'standard',
    'll_L_start_start',
    'll_L_end_end',
    'll_L_start_end',
    'll_L_end_start',
    'll_L_endpt_endpt',
    'll_L_endpt_geom',
    'll_L_geom_endpt',
    'll_L_mid_mid',
    'll_L_vertex_vertex',
    'll_L_inner_inner',
    'll_N_endpt_endpt',
    'll_N_start_start',
    'll_N_end_end',
    'll_N_vertex_vertex',
))


def is_withdrawn_line_line_mode(code):
    if not code or code == 'standard':
        return False
    text = str(code)
    return text.startswith('ll_') and text not in LINE_LINE_ALLOWED_MODES


def layers_are_line_line(t_layer, r_layer):
    try:
        return (
            _layer_geom_class(t_layer) == QgsWkbTypes.LineGeometry
            and _layer_geom_class(r_layer) == QgsWkbTypes.LineGeometry
        )
    except Exception:
        return False


def withdrawn_line_line_message(code):
    return tr(
        '线-线移动模式「{0}」已从可选列表撤下，不能再用于线-线任务。'
        '请改选仍可用的 15 种模式之一并保存后再执行。'
    ).format(code or '')


def _already_there(dx, dy):
    return abs(dx) < 1e-9 and abs(dy) < 1e-9


def _geom_noun(geom_type):
    return {
        _P: tr('点'),
        _L: tr('线'),
        _G: tr('面'),
    }.get(geom_type, tr('该类型'))


def _geom_cls(geom_type):
    """量词：一条线 / 一个点 / 一个面。"""
    return tr('条') if geom_type == _L else tr('个')


def _anchor_phrase(kind, geom_type):
    if kind == 'geom' and geom_type == _L:
        return tr('线身最近点')
    if kind == 'geom' and geom_type == _G:
        return tr('最近点')
    if kind == 'geom':
        return tr('位置')
    return {
        'start': tr('起点'),
        'end': tr('终点'),
        'mid': tr('中点'),
        'endpt': tr('端点'),
        'vertex': tr('顶点'),
        'inner': tr('中间折点'),
        'center': tr('内部点'),
        'centroid': tr('几何中心'),
        'boundary': tr('边界最近点'),
    }.get(kind, kind)


def _anchor_cat(kind):
    return {
        'geom': '距离',
        'start': '起点',
        'end': '终点',
        'mid': '中点',
        'endpt': '端点',
        'vertex': '顶点',
        'inner': '折点',
        'center': '中心',
        'centroid': '中心',
        'boundary': '边界',
    }.get(kind, '距离')


def _standard_label(t_type, r_type):
    labels = {
        (_P, _P): tr('【距离】移到容差内最近的参考点'),
        (_P, _L): tr('【距离】移到最近那条参考线的线身最近点'),
        (_P, _G): tr('【距离】移到最近那个参考面的最近点（已在面内则跳过）'),
        (_L, _P): tr('【距离】把线上最近点移到最近的参考点'),
        (_L, _L): tr('【距离】两线最近点对齐（整线平移到最近那条参考线）'),
        (_L, _G): tr('【距离】把线上最近点移到最近那个参考面的最近点'),
        (_G, _P): tr('【距离】把面上最近点移到最近的参考点'),
        (_G, _L): tr('【距离】把面上最近点移到最近那条参考线的线身最近点'),
        (_G, _G): tr('【距离】两面最近点对齐（整面平移到最近那个参考面）'),
    }
    return labels.get((t_type, r_type), tr('【距离】移到容差内最近参考要素的最近点'))


def _move_label(t_type, r_type, policy, src, dst, standard=False):
    if standard:
        return _standard_label(t_type, r_type)
    # Category source stays Chinese (stable internal key). Translate only the
    # visible prefix; do not use the source token as if it were already tr()'d.
    cat = _anchor_cat(src if r_type == _P else dst)
    src_phrase = _anchor_phrase(src, t_type)
    dst_phrase = _anchor_phrase(dst, r_type)
    t_noun = _geom_noun(t_type)
    r_noun = _geom_noun(r_type)
    r_cls = _geom_cls(r_type)
    if t_type == _P:
        if policy == 'lock':
            body = tr('移到最近那{0}参考{1}的「{2}」').format(r_cls, r_noun, dst_phrase)
        else:
            body = tr('移到容差内距离最近的参考{0}「{1}」').format(r_noun, dst_phrase)
    elif r_type == _P:
        if policy == 'lock':
            body = tr('把被移{0}的「{1}」移到最近那个参考点（参考点按离整{0}最近选取）').format(
                t_noun, src_phrase,
            )
        else:
            body = tr('把被移{0}的「{1}」移到离「{1}」最近的参考点').format(t_noun, src_phrase)
    elif policy == 'lock':
        body = tr('把被移{0}的「{1}」移到最近那{2}参考{3}的「{4}」').format(
            t_noun, src_phrase, r_cls, r_noun, dst_phrase,
        )
    else:
        body = tr('把被移{0}的「{1}」移到容差内距离最近的参考{2}「{3}」').format(
            t_noun, src_phrase, r_noun, dst_phrase,
        )
    return tr('【{0}】{1}').format(tr(cat), body)


def _move_tip(t_type, r_type, policy, src, dst, standard=False):
    src_phrase = _anchor_phrase(src, t_type)
    dst_phrase = _anchor_phrase(dst, r_type)
    lines = []
    if standard:
        lines.append(tr(
            '与原先的「标准」相同：容差内按两个要素的最近距离选参考要素，'
            '再沿最短连线把被移要素整段平移过去。'
        ))
        lines.append(tr(
            '落到线或面上时，落点是线身或边界上离它最近的位置，不必是顶点。'
            '已经重合（例如点已在面内）则跳过。'
        ))
        lines.append(tr('要落到起点、终点、中点、端点或顶点，请在本列表里改选其它项。'))
    elif policy == 'lock':
        lines.append(tr(
            '先定是哪一个参考要素：容差内、离被移要素整体最近的那一个'
            '（按要素之间的最近距离，不按起点或端点远近）。'
        ))
        lines.append(tr('再对齐：把被移侧的「{0}」平移到这个参考要素的「{1}」。').format(
            src_phrase, dst_phrase,
        ))
        lines.append(tr(
            '参考要素只要有一部分进入容差就会入选；'
            '入选之后可以移到它较远的起点、终点或中点。'
        ))
    else:
        lines.append(tr(
            '先比位置、再决定是哪一个参考要素：在容差内比较各参考要素的「{0}」，'
            '取离被移侧「{1}」最近的那个。'
        ).format(dst_phrase, src_phrase))
        lines.append(tr('这个位置本身必须在容差内，不会飞到容差外面的端点。'))
    if not standard and ('endpt' in (src, dst)):
        lines.append(tr('端点只算起点和终点（多部件线每个部件的首尾都算），中间折点不算。'))
    if not standard and ('vertex' in (src, dst)):
        lines.append(tr('顶点包括端点和全部中间折点，取其中最近的一个。'))
    if not standard and ('inner' in (src, dst)):
        lines.append(tr('中间折点不含起点和终点。直线段没有中间折点时，这条要素会跳过；锁定最近要素时，会改看容差内下一条有中间折点的要素。'))
    if dst == 'center' or src == 'center':
        lines.append(tr('内部点保证落在面内，凹面不会落到面外。'))
    if dst == 'centroid' or src == 'centroid':
        lines.append(tr('几何中心是顶点的平均位置，凹面时可能在面外。'))
    if dst == 'boundary' or src == 'boundary':
        lines.append(tr('边界最近点落在面的边界线上。已经在面内时，也会被拉到边界上。'))
    if dst == 'mid' or src == 'mid':
        lines.append(tr('中点是沿整条线的长度走到一半的位置，不是顶点序号的正中间。'))
    lines.append(tr('整要素一起平移，形状不变。'))
    return '\n'.join(lines)


def _ensure_move_catalog():
    """Cache only structural specs. Labels and tips are translated at display time."""
    global _CATALOG_READY, _MOVE_BY_CODE, _MOVE_CHOICES
    if _CATALOG_READY:
        return
    by_code = {}
    choices = {}
    for t_type, src_kinds in _ANCHORS_FOR.items():
        for r_type, dst_kinds in _ANCHORS_FOR.items():
            items = []
            pair = _GEOM_LETTER[t_type] + _GEOM_LETTER[r_type]
            for dst in dst_kinds:
                for src in src_kinds:
                    for policy in ('lock', 'near'):
                        standard = policy == 'lock' and src == 'geom' and dst == 'geom'
                        if policy == 'near' and src == 'geom' and dst == 'geom':
                            continue
                        code = 'standard' if standard else '{0}_{1}_{2}_{3}'.format(
                            pair, 'L' if policy == 'lock' else 'N', src, dst,
                        )
                        spec = {
                            'code': code,
                            'policy': policy,
                            'src': src,
                            'dst': dst,
                            't': t_type,
                            'r': r_type,
                            'standard': standard,
                        }
                        items.append(spec)
                        if code != 'standard':
                            by_code[code] = spec
            choices[(t_type, r_type)] = items
    _MOVE_BY_CODE = by_code
    _MOVE_CHOICES = choices
    _CATALOG_READY = True


def _choice_entry(spec):
    label = _move_label(
        spec['t'], spec['r'], spec['policy'], spec['src'], spec['dst'], spec.get('standard', False),
    )
    tip = _move_tip(
        spec['t'], spec['r'], spec['policy'], spec['src'], spec['dst'], spec.get('standard', False),
    )
    return (spec['code'], label, tip)


def move_mode_choices(t_layer, r_layer):
    """[(code, 标题, 说明)]，顺序即下拉顺序；类别（【】）变化处由界面插分隔线。"""
    _ensure_move_catalog()
    try:
        pair = (_layer_geom_class(t_layer), _layer_geom_class(r_layer))
    except Exception:
        pair = (None, None)
    items = _MOVE_CHOICES.get(pair)
    if not items:
        return [(
            'standard',
            tr('【距离】移到容差内最近参考要素的最近点'),
            tr('当前图层类型还不能列出专用组合，先按最近距离整要素平移。'),
        )]
    # Line-line only: keep the 15 existing codes; do not invent or remap.
    if pair == (_L, _L):
        items = [spec for spec in items if spec.get('code') in LINE_LINE_ALLOWED_MODES]
    return [_choice_entry(spec) for spec in items]


def move_mode_label(code):
    if not code or code == 'standard':
        return tr('【距离】容差内最近参考要素，整要素平移到最近点')
    _ensure_move_catalog()
    spec = _MOVE_BY_CODE.get(code)
    if not spec:
        return str(code)
    return _move_label(
        spec['t'], spec['r'], spec['policy'], spec['src'], spec['dst'], spec.get('standard', False),
    )


def move_mode_known(code):
    if not code or code == 'standard':
        return True
    _ensure_move_catalog()
    return code in _MOVE_BY_CODE


def move_spec(code):
    """standard 不限制几何类型，走原来的最短连线。其它代码带被移／参考几何类型。"""
    if not code or code == 'standard':
        return dict(_STANDARD_SPEC)
    _ensure_move_catalog()
    spec = _MOVE_BY_CODE.get(code)
    return dict(spec) if spec else None


def _geom_xy(geom):
    if geom is None or geom.isEmpty():
        return None
    try:
        if geom.type() == _P:
            return QgsPointXY(geom.asPoint())
    except Exception:
        pass
    try:
        return QgsPointXY(next(geom.vertices()))
    except Exception:
        return None


def _xy_list(geom):
    xy = _geom_xy(geom)
    return [xy] if xy is not None else []


def _all_point_xy(geom):
    try:
        if geom.isMultipart():
            pts = geom.asMultiPoint() or []
            if pts:
                return [QgsPointXY(p) for p in pts]
        return [QgsPointXY(geom.asPoint())]
    except Exception:
        return _all_vertices(geom)


def _all_vertices(geom):
    out = []
    try:
        for v in geom.vertices():
            out.append(QgsPointXY(v))
    except Exception:
        pass
    return out


def _line_parts(geom):
    if geom is None or geom.isEmpty() or geom.type() != _L:
        return []
    try:
        if geom.isMultipart():
            parts = [p for p in (geom.asMultiPolyline() or []) if p]
            if parts:
                return parts
        else:
            line = geom.asPolyline() or []
            if line:
                return [line]
    except Exception:
        pass
    verts = _all_vertices(geom)
    return [verts] if verts else []


def _boundary_geom(geom):
    if geom is None or geom.isEmpty() or geom.type() != _G:
        return None
    rings = []
    try:
        polys = geom.asMultiPolygon() if geom.isMultipart() else [geom.asPolygon()]
    except Exception:
        polys = []
    for poly in polys or []:
        for ring in poly or []:
            if ring and len(ring) >= 2:
                rings.append(ring)
    if not rings:
        verts = _all_vertices(geom)
        if len(verts) >= 2:
            return QgsGeometry.fromPolylineXY(verts)
        return None
    if len(rings) == 1:
        return QgsGeometry.fromPolylineXY(rings[0])
    return QgsGeometry.fromMultiPolylineXY(rings)


def _discrete_points_calc(geom, kind):
    """离散锚点列表。相对位置（线身最近点、边界最近点）返回 None。没有这种点时返回空列表。"""
    if geom is None or geom.isEmpty():
        return None if kind in ('geom', 'boundary') else []
    gtype = geom.type()
    if kind == 'geom':
        if gtype == _P:
            return _all_point_xy(geom)
        return None
    if kind == 'boundary':
        return None
    if kind in ('start', 'end', 'mid', 'endpt', 'inner'):
        parts = _line_parts(geom)
        if not parts:
            return []
        if kind == 'start':
            return [QgsPointXY(parts[0][0])] if parts[0] else []
        if kind == 'end':
            return [QgsPointXY(parts[-1][-1])] if parts[-1] else []
        if kind == 'endpt':
            out = []
            for part in parts:
                if not part:
                    continue
                out.append(QgsPointXY(part[0]))
                if len(part) >= 2:
                    a, b = part[0], part[-1]
                    if a.x() != b.x() or a.y() != b.y():
                        out.append(QgsPointXY(b))
            return out
        if kind == 'inner':
            out = []
            for part in parts:
                if len(part) > 2:
                    out.extend(QgsPointXY(p) for p in part[1:-1])
            return out
        try:
            length = float(geom.length())
            hit = geom.interpolate(max(length, 0.0) * 0.5)
        except Exception:
            return []
        return _xy_list(hit)
    if kind == 'vertex':
        if gtype == _P:
            return _all_point_xy(geom)
        return _all_vertices(geom)
    if kind == 'center':
        if gtype != _G:
            return []
        try:
            return _xy_list(geom.pointOnSurface())
        except Exception:
            return []
    if kind == 'centroid':
        if gtype != _G:
            return []
        try:
            return _xy_list(geom.centroid())
        except Exception:
            return []
    return []


def _discrete_points(geom, kind, cache=None):
    if cache is not None and kind in cache:
        return cache[kind]
    pts = _discrete_points_calc(geom, kind)
    if cache is not None:
        cache[kind] = pts
    return pts


def _carrier(geom, kind, cache=None):
    if kind != 'boundary':
        return geom
    if cache is not None and '_boundary' in cache:
        return cache['_boundary']
    boundary = _boundary_geom(geom)
    if cache is not None:
        cache['_boundary'] = boundary
    return boundary


def _nearest_on(carrier, pt_xy):
    if carrier is None or carrier.isEmpty():
        return None
    try:
        hit = carrier.nearestPoint(QgsGeometry.fromPointXY(QgsPointXY(pt_xy)))
    except Exception:
        return None
    return _geom_xy(hit)


def _closest_pair(src_pts, dst_pts):
    if not src_pts or not dst_pts:
        return None
    best = None
    for src in src_pts:
        sx, sy = float(src.x()), float(src.y())
        for dst in dst_pts:
            dx = float(dst.x()) - sx
            dy = float(dst.y()) - sy
            dist2 = dx * dx + dy * dy
            if best is None or dist2 < best[0]:
                best = (dist2, dx, dy)
    return best[1], best[2], best[0] ** 0.5


def _project_points(pts, carrier, onto_carrier):
    """onto_carrier=True：pts 是被移侧，投影到 carrier 得到目标点。
    False：pts 是参考侧的固定点，carrier 是被移侧，取其上最近点作为起点。
    """
    if not pts or carrier is None or carrier.isEmpty():
        return None
    best = None
    for pt in pts:
        hit = _nearest_on(carrier, pt)
        if hit is None:
            continue
        if onto_carrier:
            dx = float(hit.x()) - float(pt.x())
            dy = float(hit.y()) - float(pt.y())
        else:
            dx = float(pt.x()) - float(hit.x())
            dy = float(pt.y()) - float(hit.y())
        dist2 = dx * dx + dy * dy
        if best is None or dist2 < best[0]:
            best = (dist2, dx, dy)
    if best is None:
        return None
    return best[1], best[2], best[0] ** 0.5


def _align_prepared(src_pts, src_carrier, ref_geom, dst, ref_cache):
    dst_pts = _discrete_points(ref_geom, dst, ref_cache)
    if src_pts is not None and dst_pts is not None:
        return _closest_pair(src_pts, dst_pts)
    if src_pts is not None and dst_pts is None:
        return _project_points(src_pts, _carrier(ref_geom, dst, ref_cache), True)
    if src_pts is None and dst_pts is not None:
        return _project_points(dst_pts, src_carrier, False)
    return _shortest_delta(src_carrier, _carrier(ref_geom, dst, ref_cache))


def _translate_by_mode(tg, ref_entries, ref_idx, tol, spec, exclude_layer_id=None, exclude_fid=None):
    """按移动模式返回 (dx, dy, dist)。锁定模式只要求参考要素在容差内；近距模式要求锚点在容差内。"""
    if tg is None or tg.isEmpty() or not ref_entries or not spec:
        return None
    tol = float(tol)
    if tol <= 0:
        return None
    src = spec['src']
    dst = spec['dst']
    r_type = spec.get('r')
    policy = spec['policy']
    try:
        rect = _rect_grow(tg.boundingBox(), tol)
        cand_ids = list(ref_idx.intersects(rect))
    except Exception:
        cand_ids = list(range(len(ref_entries)))

    src_pts = _discrete_points(tg, src)
    src_carrier = None
    if src_pts is None:
        src_carrier = _carrier(tg, src)
        if src_carrier is None or src_carrier.isEmpty():
            return None

    prefilter = src in _ANCHOR_ON_GEOM and dst in _ANCHOR_ON_GEOM

    def _entry(cid):
        if cid < 0 or cid >= len(ref_entries):
            return None
        entry = ref_entries[cid]
        if exclude_layer_id is not None and exclude_fid is not None:
            if entry['layer'].id() == exclude_layer_id and int(entry['fid']) == int(exclude_fid):
                return None
        rg = entry.get('geom')
        if rg is None or rg.isEmpty():
            return None
        if r_type is not None and rg.type() != r_type:
            return None
        return entry

    if policy == 'lock':
        ranked = []
        for cid in cand_ids:
            entry = _entry(cid)
            if entry is None:
                continue
            try:
                dist = float(tg.distance(entry['geom']))
            except Exception:
                continue
            if dist <= tol:
                ranked.append((dist, cid))
        ranked.sort()
        for _dist, cid in ranked:
            entry = ref_entries[cid]
            cache = entry.setdefault('_cdet_move_pts', {})
            delta = _align_prepared(src_pts, src_carrier, entry['geom'], dst, cache)
            if delta is None:
                continue
            dx, dy, align_dist = delta
            if _already_there(dx, dy):
                return None
            return dx, dy, align_dist
        return None

    best = None
    for cid in cand_ids:
        entry = _entry(cid)
        if entry is None:
            continue
        if prefilter:
            try:
                dist = float(tg.distance(entry['geom']))
            except Exception:
                continue
            if dist > tol:
                continue
        cache = entry.setdefault('_cdet_move_pts', {})
        delta = _align_prepared(src_pts, src_carrier, entry['geom'], dst, cache)
        if delta is None:
            continue
        dx, dy, align_dist = delta
        if align_dist > tol:
            continue
        if best is None or align_dist < best[0]:
            best = (align_dist, dx, dy)
    if best is None:
        return None
    align_dist, dx, dy = best
    if _already_there(dx, dy):
        return None
    return dx, dy, align_dist


def remove_move_preview_layers(project=None):
    project = project or QgsProject.instance()
    to_remove = []
    for lid, lyr in project.mapLayers().items():
        if lyr.customProperty(PREVIEW_FLAG):
            to_remove.append(lid)
        elif isinstance(lyr, QgsVectorLayer) and lyr.name().endswith(_preview_suffix()):
            to_remove.append(lid)
    if to_remove:
        project.removeMapLayers(to_remove)


def run_move(
    iface,
    project,
    target_layers,
    ref_layers,
    tolerance,
    category_filters=None,
    ref_category_filters=None,
    show_messages=True,
    show_progress=True,
    move_mode='standard',
):
    """
    整要素平移（形状不变）：
    1) 生成「_移动预览」内存层（非筛结果层）
    2) 确认后写回原图层几何；取消则删除预览
    move_mode 为 standard 时与原先一样，沿最短连线平移；其它代码见移动模式下拉。
    返回 dict: ok / moved / skipped / preview_layers / written / error
    """
    result = {
        'ok': False,
        'moved': 0,
        'skipped': 0,
        'preview_layers': [],
        'written': False,
        'error': None,
        'elapsed': 0.0,
    }
    start = time.time()

    def _warn(msg):
        if show_messages:
            QMessageBox.warning(iface.mainWindow(), tr('提示'), msg)

    def _info(msg):
        if show_messages:
            QMessageBox.information(iface.mainWindow(), tr('提示'), msg)

    if not target_layers:
        msg = tr('请选择被移图层！')
        result['error'] = msg
        _warn(msg)
        return result
    if not ref_layers:
        msg = tr('请选择参考图层！')
        result['error'] = msg
        _warn(msg)
        return result

    move_mode = move_mode or 'standard'
    if layers_are_line_line(target_layers[0], ref_layers[0]) and is_withdrawn_line_line_mode(move_mode):
        msg = withdrawn_line_line_message(move_mode)
        result['error'] = msg
        _warn(msg)
        return result
    spec = move_spec(move_mode)
    if spec is None:
        msg = tr('未知的移动模式。')
        result['error'] = msg
        _warn(msg)
        return result
    mode_label = move_mode_label(move_mode)
    for code, label, _tip in move_mode_choices(target_layers[0], ref_layers[0]):
        if code == move_mode:
            mode_label = label
            break
    if spec.get('t') is not None:
        if not any(lyr.geometryType() == spec['t'] for lyr in target_layers):
            msg = tr('这个移动模式要求被移图层是{0}。').format(_geom_noun(spec['t']))
            result['error'] = msg
            _warn(msg)
            return result
        if not any(lyr.geometryType() == spec['r'] for lyr in ref_layers):
            msg = tr('这个移动模式要求参考图层是{0}。').format(_geom_noun(spec['r']))
            result['error'] = msg
            _warn(msg)
            return result

    # CRS：以第一个被移图层为准。两侧分类分开：同一图层在两边勾选可以不同。
    base_crs = target_layers[0].crs()
    ref_entries, ref_idx = _build_ref_state(
        ref_layers, base_crs, project, ref_category_filters
    )
    if not ref_entries:
        msg = tr('参考图层没有可用要素。')
        result['error'] = msg
        _warn(msg)
        return result

    # 先清旧预览，避免叠层
    remove_move_preview_layers(project)

    total_feats = 0
    for lyr in target_layers:
        try:
            total_feats += lyr.featureCount()
        except Exception:
            pass

    progress = None
    if show_progress and total_feats > 0:
        progress = QProgressDialog(
            tr('计算移动预览…'), tr('取消'), 0, max(total_feats, 1), iface.mainWindow()
        )
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(400)
        progress.setValue(0)

    # pending_writes: { layer_id: [ (fid, new_geom_in_layer_crs), ... ] }
    pending_writes = {}
    preview_layers = []
    processed = 0
    moved = 0
    skipped = 0
    type_skipped = 0
    canceled = False

    for layer in target_layers:
        geom_type = layer.geometryType()
        layer_crs = layer.crs()
        transform_to_base = None
        transform_from_base = None
        if layer_crs != base_crs:
            transform_to_base = QgsCoordinateTransform(layer_crs, base_crs, project)
            transform_from_base = QgsCoordinateTransform(base_crs, layer_crs, project)

        preview_feats = []
        writes = []
        same_as_ref = any(layer.id() == rl.id() for rl in ref_layers)

        for feature in iter_features(layer, category_filters):
            processed += 1
            if progress:
                progress.setValue(processed)
                if progress.wasCanceled():
                    canceled = True
                    break
            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                skipped += 1
                continue
            check_geom = QgsGeometry(geom)
            if transform_to_base:
                try:
                    check_geom.transform(transform_to_base)
                except Exception:
                    skipped += 1
                    continue
            excl_lid = layer.id() if same_as_ref else None
            excl_fid = feature.id() if same_as_ref else None
            if spec.get('t') is not None and check_geom.type() != spec['t']:
                skipped += 1
                type_skipped += 1
                continue
            if spec.get('code') == 'standard':
                hit = _best_translate_for_feature(
                    check_geom, ref_entries, ref_idx, tolerance,
                    exclude_layer_id=excl_lid, exclude_fid=excl_fid,
                )
            else:
                hit = _translate_by_mode(
                    check_geom, ref_entries, ref_idx, tolerance, spec,
                    exclude_layer_id=excl_lid, exclude_fid=excl_fid,
                )
            if hit is None:
                skipped += 1
                continue
            dx, dy, _dist = hit
            moved_base = QgsGeometry(check_geom)
            try:
                moved_base.translate(dx, dy)
            except Exception:
                skipped += 1
                continue
            if moved_base.isEmpty():
                skipped += 1
                continue
            moved_layer = QgsGeometry(moved_base)
            if transform_from_base:
                try:
                    moved_layer.transform(transform_from_base)
                except Exception:
                    skipped += 1
                    continue
            writes.append((feature.id(), QgsGeometry(moved_layer)))
            nf = QgsFeature(layer.fields())
            nf.setAttributes(feature.attributes())
            nf.setGeometry(QgsGeometry(moved_layer))
            preview_feats.append(nf)
            moved += 1

        if canceled:
            break
        if preview_feats:
            pname = _unique_layer_name(project, f'{layer.name()}{_preview_suffix()}')
            pl = _create_memory_layer(pname, geom_type, layer_crs, layer.fields())
            pl.dataProvider().addFeatures(preview_feats)
            pl.updateExtents()
            pl.setCustomProperty(PREVIEW_FLAG, True)
            try:
                apply_memory_output_style(pl)
            except Exception:
                pass
            project.addMapLayer(pl)
            preview_layers.append(pl)
            pending_writes[layer.id()] = (layer, writes)

    if progress:
        progress.close()

    result['moved'] = moved
    result['skipped'] = skipped
    result['preview_layers'] = [pl.name() for pl in preview_layers]
    result['elapsed'] = time.time() - start

    if canceled:
        remove_move_preview_layers(project)
        result['error'] = tr('已取消')
        result['ok'] = False
        return result

    if moved <= 0:
        if type_skipped and type_skipped >= processed:
            msg = tr('被移要素的几何类型与当前移动模式不符。')
        else:
            msg = tr('容差内没有可平移的要素（已在位或距离超过容差）。')
        result['error'] = msg
        _info(msg)
        result['ok'] = True
        return result

    # 先预览再写回
    preview_names = '\n'.join(f'  → {n}' for n in result['preview_layers'])
    box = QMessageBox(iface.mainWindow())
    box.setWindowTitle(tr('移动预览'))
    box.setIcon(QMessageBox.Question)
    box.setText(
        tr('已生成移动预览（整要素平移，形状不变）。\n'
           '移动模式：{0}\n'
           '可平移：{1}    跳过：{2}\n'
           '预览图层：\n{3}\n\n'
           '是否写回原图层几何？').format(mode_label, moved, skipped, preview_names)
    )
    btn_write = box.addButton(tr('写回原图层'), QMessageBox.AcceptRole)
    btn_keep = box.addButton(tr('仅保留预览'), QMessageBox.ActionRole)
    btn_discard = box.addButton(tr('丢弃预览'), QMessageBox.RejectRole)
    box.setDefaultButton(btn_write)
    run_dialog(box)
    clicked = box.clickedButton()

    if clicked is btn_discard:
        remove_move_preview_layers(project)
        result['ok'] = True
        result['written'] = False
        return result

    if clicked is btn_keep:
        result['ok'] = True
        result['written'] = False
        if show_messages:
            _info(tr('已保留预览图层。确认无误后可再次执行并选择「写回原图层」。'))
        return result

    # 写回
    write_errors = []
    written_count = 0
    for _lid, (layer, writes) in pending_writes.items():
        if not writes:
            continue
        if not layer.isEditable():
            if not layer.startEditing():
                write_errors.append(
                    tr('{0}：无法进入编辑模式').format(layer.name())
                )
                continue
        ok_all = True
        for fid, new_g in writes:
            if not layer.changeGeometry(fid, new_g):
                ok_all = False
        if ok_all:
            if not layer.commitChanges():
                write_errors.append(
                    tr('{0}：提交失败 — {1}').format(
                        layer.name(), layer.commitErrors() if hasattr(layer, 'commitErrors') else ''
                    )
                )
                try:
                    layer.rollBack()
                except Exception:
                    pass
            else:
                written_count += len(writes)
                try:
                    layer.triggerRepaint()
                except Exception:
                    pass
        else:
            write_errors.append(tr('{0}：部分要素写回失败，已回滚').format(layer.name()))
            try:
                layer.rollBack()
            except Exception:
                pass

    remove_move_preview_layers(project)
    result['written'] = written_count > 0
    result['ok'] = not write_errors
    result['elapsed'] = time.time() - start
    if write_errors:
        result['error'] = '\n'.join(write_errors)
        _warn(tr('写回完成但有错误：\n{0}').format(result['error']))
    elif show_messages:
        _info(
            tr('已写回 {0} 个要素（整要素平移）。用时 {1:.2f} 秒').format(
                written_count, result['elapsed']
            )
        )
    return result
