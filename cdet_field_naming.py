# -*- coding: utf-8 -*-
import math
import time
from pathlib import Path

from qgis.PyQt.QtCore import QVariant, Qt
from qgis.PyQt.QtWidgets import QProgressDialog
from qgis.core import (
    QgsFeature,
    QgsGeometry,
    QgsProject,
    QgsRectangle,
    QgsSpatialIndex,
    QgsVectorLayer,
    QgsWkbTypes,
    QgsCoordinateTransform,
)

try:
    from .cdet_category import iter_features
except ImportError:
    from cdet_category import iter_features
from .i18n import tr as _i18n_tr
from .errors import NO_REF_FEATURES as ERR_NO_REF_FEATURES
from .qtutil import run_dialog, run_menu, qvariant_type, qtype_is, is_null_qvariant, AppMessageBox as QMessageBox

LAYER_NAME_VALUE = '\x00__cdet_layer_name__\x00'
LAYER_NAME_SETTINGS_KEY = '__cdet_layer_title__'
REF_ELEMENT_COUNT = '\x00__cdet_ref_element_count__\x00'
REF_ELEMENT_COUNT_STORE = '__cdet_element_count__'


def tr(text):
    return _i18n_tr(text)


def default_element_count_rule():
    return {'kind': 'direct'}


def format_element_count_rule_summary(rule):
    if not rule:
        return tr('原样')
    k = rule.get('kind', 'direct')
    if k == 'direct':
        return tr('原样')
    if k == 'le':
        return tr('≤{0}→「{1}」/否则「{2}」').format(
            rule.get('threshold', 0),
            rule.get('if_yes', ''),
            rule.get('if_no', ''),
        )
    if k == 'ge':
        return tr('≥{0}→「{1}」/否则「{2}」').format(
            rule.get('threshold', 0),
            rule.get('if_yes', ''),
            rule.get('if_no', ''),
        )
    if k == 'le_ge':
        return tr('≤{0}→「{1}」; ≥{2}→「{3}」; 其他「{4}」').format(
            rule.get('t_le', 0),
            rule.get('v_le', ''),
            rule.get('t_ge', 0),
            rule.get('v_ge', ''),
            rule.get('v_other', ''),
        )
    return tr('原样')


def apply_element_count_rule(count_int, rule):
    if count_int is None:
        return None
    try:
        c = int(count_int)
    except (TypeError, ValueError):
        return None
    r = rule or default_element_count_rule()
    k = r.get('kind', 'direct')
    if k == 'direct':
        return c
    if k == 'le':
        t = int(r.get('threshold', 0))
        return r.get('if_yes', '') if c <= t else r.get('if_no', '')
    if k == 'ge':
        t = int(r.get('threshold', 0))
        return r.get('if_yes', '') if c >= t else r.get('if_no', '')
    if k == 'le_ge':
        t1 = int(r.get('t_le', 0))
        t2 = int(r.get('t_ge', 0))
        if c <= t1:
            return r.get('v_le')
        if c >= t2:
            return r.get('v_ge')
        return r.get('v_other')
    return c


def _geom_kind(wkb_type):
    gt = QgsWkbTypes.geometryType(wkb_type)
    if gt == QgsWkbTypes.PointGeometry:
        return QgsWkbTypes.PointGeometry
    if gt == QgsWkbTypes.LineGeometry:
        return QgsWkbTypes.LineGeometry
    if gt == QgsWkbTypes.PolygonGeometry:
        return QgsWkbTypes.PolygonGeometry
    return None


def _layer_geom_class(lyr):
    """判定矢量图层点/线/面类别：优先 geometryType()，避免仅用 wkbType 时出现 Unknown 导致只能退回「通用」模式。"""
    try:
        g = lyr.geometryType()
        if g in (QgsWkbTypes.PointGeometry, QgsWkbTypes.LineGeometry, QgsWkbTypes.PolygonGeometry):
            return g
    except Exception:
        pass
    return _geom_kind(lyr.wkbType())


def _type_pair(t_layer, r_layer):
    return (_layer_geom_class(t_layer), _layer_geom_class(r_layer))


def _spatial_choice(code, label, tip=None):
    if tip:
        return (code, label, tip)
    return (code, label)


AGGREGATE_LINE_POINT_MODES = frozenset({
    'lp_both_endpoints_on_pts',
    'lp_one_endpoint_on_pts',
    'lp_either_endpoint_on_pts',
    'lp_any_vertex_on_pts',
    'lp_consecutive_segment_endpoints_match',
})

DEFAULT_KTH_NEAREST_K = 2
DEFAULT_LENGTH_RATIO_PCT = 50.0
DEFAULT_AREA_RATIO_PCT = 50.0
DEFAULT_CONSECUTIVE_N = 2
DEFAULT_LL_SEGMENT_RATIO_PCT = 70.0

_PCT_SPEC = {'label': '比例阈值', 'min': 0.0, 'max': 100.0, 'decimals': 1, 'step': 5.0, 'suffix': ' %'}
MODE_PARAM_SPECS = {
    'pp_kth_nearest': {
        'label': '第几近 K', 'default': float(DEFAULT_KTH_NEAREST_K),
        'min': 1.0, 'max': 1000.0, 'decimals': 0, 'step': 1.0, 'suffix': '',
        'tip': '取容差内第几近的参考点（1 = 最近）。',
    },
    'lp_consecutive_segment_endpoints_match': {
        'label': '连续段数 N', 'default': float(DEFAULT_CONSECUTIVE_N),
        'min': 1.0, 'max': 1000.0, 'decimals': 0, 'step': 1.0, 'suffix': '',
        'tip': '至少连续多少小段的顶点都挂着参考点。',
    },
    'll_length_ratio': dict(_PCT_SPEC, default=DEFAULT_LENGTH_RATIO_PCT, tip='重叠长度占被命名线总长的最低比例。'),
    'll_buffer_length_ratio': dict(_PCT_SPEC, default=DEFAULT_LENGTH_RATIO_PCT, tip='容差内贴合长度占被命名线总长的最低比例。'),
    'll_adjacent_seg_ratio': dict(_PCT_SPEC, default=DEFAULT_LL_SEGMENT_RATIO_PCT, tip='对得上的小段长度占被命名线总长的最低比例。'),
    'lg_inside_length_ratio': dict(_PCT_SPEC, default=DEFAULT_LENGTH_RATIO_PCT, tip='线在面内的长度占线总长的最低比例。'),
    'gl_inside_length_ratio': dict(_PCT_SPEC, default=DEFAULT_LENGTH_RATIO_PCT, tip='参考线在面内的长度占参考线总长的最低比例。'),
    'gg_overlap_area_ratio': dict(_PCT_SPEC, default=DEFAULT_AREA_RATIO_PCT, tip='重叠面积占被命名面面积的最低比例。'),
}


def mode_param_spec(code):
    """需要额外阈值的模式返回参数说明 dict，其它模式返回 None。"""
    return MODE_PARAM_SPECS.get(code)


def mode_param_value(code, value):
    spec = MODE_PARAM_SPECS.get(code)
    if spec is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return float(spec['default'])
    return min(max(v, spec['min']), spec['max'])


def format_mode_param(code, value):
    """方案列表用的简短参数文字，如「比例阈值 60%」；无参数模式返回空串。"""
    spec = MODE_PARAM_SPECS.get(code)
    if spec is None:
        return ''
    v = mode_param_value(code, value)
    num = '{0:.0f}'.format(v) if spec['decimals'] == 0 or float(v).is_integer() else '{0:g}'.format(v)
    return '{0} {1}{2}'.format(tr(spec['label']), num, spec['suffix'].strip())


def _segment_endpoints_per_part(line_geom):
    """每条折线段的 (起点, 终点)；多点/多部件逐段判断。"""
    out = []
    if line_geom.type() != QgsWkbTypes.LineGeometry:
        return out
    if line_geom.isMultipart():
        for part in line_geom.asMultiPolyline():
            if len(part) >= 2:
                out.append((part[0], part[-1]))
    else:
        ln = line_geom.asPolyline()
        if len(ln) >= 2:
            out.append((ln[0], ln[-1]))
    return out


def _line_all_vertices_xy(line_geom):
    """折线全部顶点（多端线/part 順序罗列）。"""
    out = []
    if line_geom.type() != QgsWkbTypes.LineGeometry:
        return out
    if line_geom.isMultipart():
        for part in line_geom.asMultiPolyline():
            out.extend(part)
    else:
        out.extend(line_geom.asPolyline())
    return out


def _line_adjacent_segments_xy(line_geom):
    """折线按相邻顶点拆分为线段：(v[i], v[i+1])。"""
    out = []
    if line_geom.type() != QgsWkbTypes.LineGeometry:
        return out
    parts = line_geom.asMultiPolyline() if line_geom.isMultipart() else [line_geom.asPolyline()]
    for part in parts:
        if len(part) < 2:
            continue
        for i in range(len(part) - 1):
            out.append((part[i], part[i + 1]))
    return out


def _segment_pair_match(a1, a2, b1, b2, tol):
    """无向端点对匹配：A-B 与 B-A 视为同一段。"""
    d11 = _geom_distance(QgsGeometry.fromPointXY(a1), QgsGeometry.fromPointXY(b1))
    d22 = _geom_distance(QgsGeometry.fromPointXY(a2), QgsGeometry.fromPointXY(b2))
    if d11 <= tol and d22 <= tol:
        return True
    d12 = _geom_distance(QgsGeometry.fromPointXY(a1), QgsGeometry.fromPointXY(b2))
    d21 = _geom_distance(QgsGeometry.fromPointXY(a2), QgsGeometry.fromPointXY(b1))
    return d12 <= tol and d21 <= tol


def _line_adjacent_segment_stats(tg_line, rg_line, tol):
    """返回判断线相邻段匹配统计：(matched_count, total_count, matched_length, total_length)。"""
    seg_t = _line_adjacent_segments_xy(tg_line)
    seg_r = _line_adjacent_segments_xy(rg_line)
    if not seg_t:
        return (0, 0, 0.0, 0.0)
    matched_count = 0
    matched_length = 0.0
    total_length = 0.0
    for a1, a2 in seg_t:
        seg_len = _geom_distance(QgsGeometry.fromPointXY(a1), QgsGeometry.fromPointXY(a2))
        if math.isfinite(seg_len):
            total_length += max(0.0, float(seg_len))
        ok = False
        for b1, b2 in seg_r:
            if _segment_pair_match(a1, a2, b1, b2, tol):
                ok = True
                break
        if ok:
            matched_count += 1
            if math.isfinite(seg_len):
                matched_length += max(0.0, float(seg_len))
    return (matched_count, len(seg_t), matched_length, total_length)


def ref_point_geoms_from_candidates(ref_entries, cand_ids):
    geoms = []
    for cid in cand_ids:
        if cid < 0 or cid >= len(ref_entries):
            continue
        g = ref_entries[cid]['geom']
        if g.type() == QgsWkbTypes.PointGeometry:
            geoms.append(g)
    return geoms


def line_point_aggregate_ok(mode, line_geom, ref_point_geoms, tol, param=None):
    """参考点图层合并为一点池；逐折线段判断端点是否落在池内(≤容差)。"""
    if line_geom.isEmpty() or tol < 0:
        return False
    if not ref_point_geoms:
        return False
    segs = _segment_endpoints_per_part(line_geom)
    if not segs:
        return False

    def _near(pt_xy, pg):
        return _geom_distance(QgsGeometry.fromPointXY(pt_xy), pg) <= tol

    def _xy_near_any(pt_xy):
        return any(_near(pt_xy, pg) for pg in ref_point_geoms)

    if mode == 'lp_both_endpoints_on_pts':
        for a, b in segs:
            if not (_xy_near_any(a) and _xy_near_any(b)):
                return False
        return True
    if mode == 'lp_one_endpoint_on_pts':
        for a, b in segs:
            ca, cb = _xy_near_any(a), _xy_near_any(b)
            if ca and cb:
                return False
            if ca ^ cb:
                continue
            return False
        return True
    if mode == 'lp_either_endpoint_on_pts':
        for a, b in segs:
            if not (_xy_near_any(a) or _xy_near_any(b)):
                return False
        return True
    if mode == 'lp_any_vertex_on_pts':
        for v in _line_all_vertices_xy(line_geom):
            if _xy_near_any(v):
                return True
        return False
    if mode == 'lp_consecutive_segment_endpoints_match':
        n_need = int(mode_param_value(mode, param))
        run = 0
        for a, b in _line_adjacent_segments_xy(line_geom):
            if _xy_near_any(a) and _xy_near_any(b):
                run += 1
                if run >= n_need:
                    return True
            else:
                run = 0
        return False
    return False


def _tip(*lines):
    return '\n'.join(str(x) for x in lines if x)


_TIP_TOL_UNUSED = '容差：不使用（按坐标精确判断）。'
_TIP_MULTI = '多个参考要素同时满足时，按「多匹配处理」选取。'
_TIP_LP_POOL = (
    '所选的全部参考点合并成一个「点池」一起判断；写入值来自贴在对应位置上的参考点。'
)
_TIP_SEG = (
    '「小段」＝线上相邻两个顶点之间的直线段；'
    '「段匹配」＝参考线上有一段，两个顶点分别与它的两个顶点距离≤容差（方向相反也算）。'
)
_TIP_SEG_NOTE = (
    '注意：只比较顶点，参考线在同一位置多一个或少一个折点，该段就匹配不上。'
    '吸附模式下按小段逐段输出。'
)
_TIP_LG_ENDS = '端点＝线的起点和终点；多部件线把每个部件的首尾都算上。「在面内」含边界。'


def _mode_tables():
    """几何组合 → [(code, 标题, 浮动说明)]。标题统一「【类别】一句话」，说明统一「判定 / 用途 / 注意」。"""
    P = QgsWkbTypes.PointGeometry
    L = QgsWkbTypes.LineGeometry
    G = QgsWkbTypes.PolygonGeometry
    # Late-bind tip fragments so a language switch does not freeze first-language text.
    _TIP_TOL_UNUSED = tr(globals()['_TIP_TOL_UNUSED'])
    _TIP_MULTI = tr(globals()['_TIP_MULTI'])
    _TIP_LP_POOL = tr(globals()['_TIP_LP_POOL'])
    _TIP_SEG = tr(globals()['_TIP_SEG'])
    _TIP_SEG_NOTE = tr(globals()['_TIP_SEG_NOTE'])
    _TIP_LG_ENDS = tr(globals()['_TIP_LG_ENDS'])
    return {
        (P, P): [
            ('pp_tol', tr('【距离】两点相距 ≤ 容差（最常用）'), _tip(
                tr('判定：被命名点与参考点的直线距离 ≤ 容差。'),
                _TIP_MULTI,
            )),
            ('pp_coincident', tr('【重合】两点坐标重合（极严格）'), _tip(
                tr('判定：距离 ≤ 容差×0.001（最小 1e-9），即几乎同一位置。'),
                tr('用途：检查本应完全重合的点，例如测量点与控制点。'),
            )),
            ('pp_kth_nearest', tr('【距离】只取第 K 近的参考点'), _tip(
                tr('判定：把容差内的参考点按距离由近到远排队，只取第 K 个；不足 K 个则不命中。'),
                tr('K 在右侧「第几近 K」里设置，默认 2。'),
                tr('用途：字段模式下参考图层就是自身图层时，第 1 近是自己，取第 2 近就是「最近的邻居」。'),
                tr('吸附模式会自动排除自身，此时第 K 近就是真正的第 K 近。'),
                tr('注意：只会得到一个结果，「多匹配处理」不起作用。'),
            )),
        ],
        (P, L): [
            ('pl_tol', tr('【距离】点到参考线 ≤ 容差'), _tip(
                tr('判定：点到参考线上最近位置（线身任意处，不只是顶点）的距离 ≤ 容差。'),
                _TIP_MULTI,
            )),
            ('pl_on_line', tr('【距离】点落在参考线上（同上一项，兼容旧方案）'), _tip(
                tr('判定：与「点到参考线 ≤ 容差」完全相同。'),
                tr('保留此项只是为了让 1.0 版保存的方案还能正常运行，新建任务请用上一项。'),
            )),
            ('pl_at_ref_line_endpoints', tr('【端点】点在参考线的端点上'), _tip(
                tr('判定：点与参考线的起点或终点距离 ≤ 容差。'),
                tr('多部件线：每个部件的首尾都算端点。'),
                tr('用途：给节点写入所连线的属性，例如检查井取管线编号。'),
            )),
            ('pl_at_ref_line_endpoint_only', tr('【端点】点只在端点上（同时贴近中间折点则排除）'), _tip(
                tr('判定：满足「点在参考线的端点上」，并且点与该线所有中间折点的距离都 > 容差。'),
                tr('与上一项的区别：短线或折点很密时，点可能同时靠近端点和折点，本项会排除这种情况。'),
            )),
            ('pl_at_ref_line_inner_vertex', tr('【折点】点在参考线的中间折点上（不含端点）'), _tip(
                tr('判定：点与某个中间折点距离 ≤ 容差，并且不靠近线的两端。'),
                tr('用途：找落在线拐点上、但不在线头线尾的点。'),
            )),
        ],
        (P, G): [
            ('pg_within', tr('【包含】点在参考面内部（不含边界）'), _tip(
                tr('判定：点严格落在面的内部；正好压在边界线上的点不算。'),
                _TIP_TOL_UNUSED,
            )),
            ('pg_interior_boundary', tr('【包含】点在参考面内或边界上'), _tip(
                tr('判定：点在面内部，或正好压在边界线上。'),
                _TIP_TOL_UNUSED,
                tr('用途：给点写入所在行政区、地块等面的属性。'),
            )),
            ('pg_boundary_only', tr('【边界】点正好在参考面边界上'), _tip(
                tr('判定：点压在面的边界线上，且不在面内部。'),
                _TIP_TOL_UNUSED,
                tr('注意：坐标稍有偏差就判不中，这种情况建议用「点到参考面边界线 ≤ 容差」。'),
            )),
            ('pg_outside_near', tr('【距离】点在参考面内，或在面外 ≤ 容差'), _tip(
                tr('判定：相当于把参考面向外扩大一个容差，点落在扩大后的面里就命中。'),
                tr('面内的点一律命中；面外的点距离面 ≤ 容差才命中。'),
            )),
            ('pg_min_distance_to_boundary', tr('【边界】点到参考面边界线 ≤ 容差（面内外都算）'), _tip(
                tr('判定：只看点到边界线的距离，面内、面外都一样。'),
                tr('注意：面内部离边界较远的点不会命中。'),
            )),
        ],
        (L, P): [
            ('lp_both_endpoints_on_pts', tr('【端点】线的两个端点都有参考点'), _tip(
                tr('判定：线的起点、终点都能在容差内找到参考点（可以是不同的点）。'),
                tr('多部件线：每个部件的首尾都要满足。'),
                _TIP_LP_POOL,
                tr('用途：检查管线/道路两端是否都接到了节点。'),
            )),
            ('lp_one_endpoint_on_pts', tr('【端点】线恰好一端有参考点'), _tip(
                tr('判定：一端有参考点、另一端没有才命中；两端都有或都没有都不命中。'),
                tr('多部件线：每个部件都要恰好一端有。'),
                _TIP_LP_POOL,
                tr('用途：找一端悬空的线。'),
            )),
            ('lp_either_endpoint_on_pts', tr('【端点】线至少一端有参考点'), _tip(
                tr('判定：起点或终点任一有参考点即命中，两端都有也命中。'),
                tr('多部件线：每个部件都要至少一端有。'),
                _TIP_LP_POOL,
            )),
            ('lp_head_on_pt', tr('【端点】线头（起点）有参考点'), _tip(
                tr('判定：线的第一个顶点（按绘制方向）与参考点距离 ≤ 容差；线尾不参与。'),
                tr('多部件线取第一个部件的起点。'),
                tr('用途：给线写入起始节点编号。'),
            )),
            ('lp_tail_on_pt', tr('【端点】线尾（终点）有参考点'), _tip(
                tr('判定：线的最后一个顶点（按绘制方向）与参考点距离 ≤ 容差；线头不参与。'),
                tr('多部件线取最后一个部件的终点。'),
                tr('用途：给线写入终止节点编号。'),
            )),
            ('lp_endpoint', tr('【端点】线的任一端点靠近参考点（逐点判断）'), _tip(
                tr('判定：每个参考点单独判断，只要它靠近线的某个端点就算命中。'),
                tr('与「线至少一端有参考点」的区别只在多部件线：那一项要求每个部件都满足，本项任一部件满足即可。'),
                _TIP_MULTI,
            )),
            ('lp_any_vertex_on_pts', tr('【折点】线的任一顶点有参考点（含端点）'), _tip(
                tr('判定：线上任意一个顶点（端点或中间折点）与参考点距离 ≤ 容差。'),
                _TIP_LP_POOL,
            )),
            ('lp_any_vertex', tr('【折点】线的任一顶点靠近参考点（同上一项，兼容旧方案）'), _tip(
                tr('判定：与「线的任一顶点有参考点」结果相同，保留用于兼容 1.0 版方案。'),
            )),
            ('lp_consecutive_segment_endpoints_match', tr('【折点】线上连续 N 小段的顶点都有参考点'), _tip(
                tr('判定：把线按相邻顶点拆成小段，只要线上某处有连续 N 段，每段两头的顶点都有参考点即命中。'),
                tr('也就是至少有 N+1 个相邻顶点连续挂着参考点。N 在右侧「连续段数 N」里设置，默认 2。'),
                _TIP_LP_POOL,
            )),
            ('lp_nearest', tr('【距离】参考点到线身 ≤ 容差'), _tip(
                tr('判定：参考点到线上最近位置（任意处，不只是顶点）的距离 ≤ 容差。'),
                _TIP_MULTI,
            )),
            (LP_END_FIELDS, tr('【写入】线头、线尾分别写入不同字段'), _tip(
                tr('按绘制方向：第一个顶点是线头，最后一个顶点是线尾（多部件取首部件起点、末部件终点）。'),
                tr('线头、线尾各自在容差内找参考点，把点的字段分别写到线的两个字段里；可以只填一头。'),
                tr('多匹配处理对头、尾分别生效；同一个点同时靠近头和尾时，两边都会写。'),
            )),
        ],
        (L, L): [
            ('ll_near', tr('【距离】两线最近距离 ≤ 容差（不必接触）'), _tip(
                tr('判定：两条线之间最近两处的距离 ≤ 容差。'),
                _TIP_MULTI,
            )),
            ('ll_buffer_overlap', tr('【距离】两线最近距离 ≤ 2×容差'), _tip(
                tr('判定：两线各自向外扩大一个容差后有交集，等价于最近距离 ≤ 2 倍容差。'),
                tr('比「两线最近距离 ≤ 容差」宽松一倍。'),
            )),
            ('ll_equals', tr('【重合】两线完全相同（坐标精确一致）'), _tip(
                tr('判定：两线形状、位置完全一样；方向相反也算。'),
                _TIP_TOL_UNUSED,
            )),
            ('ll_almost_equals', tr('【重合】两线基本重合（容差内）'), _tip(
                tr('判定：两线各自扩大容差后，都能完整罩住对方。'),
                tr('用途：同一条线在两个图层里数字化有轻微偏差。'),
            )),
            ('ll_intersects', tr('【相交】两线有任何接触（交叉、端点相碰、重叠都算）'), _tip(
                tr('判定：两线有任意公共点。'),
                _TIP_TOL_UNUSED,
            )),
            ('ll_touches', tr('【相交】两线只在端点处相碰（首尾相接、T 形）'), _tip(
                tr('判定：至少一条线的端点落在另一条线上，并且两线内部没有交叉或重叠。'),
                tr('首尾相接、T 字形接入命中；十字交叉、重叠不命中。'),
                _TIP_TOL_UNUSED,
            )),
            ('ll_crosses', tr('【相交】两线十字交叉穿过'), _tip(
                tr('判定：两线在各自的中间部位交叉于一点。'),
                tr('首尾相接、T 字形、重叠都不命中。'),
                _TIP_TOL_UNUSED,
            )),
            ('ll_end_to_end', tr('【端点】两线端点相接（首尾相连）'), _tip(
                tr('判定：被命名线的某个端点与参考线的某个端点距离 ≤ 容差。'),
                tr('用途：检查路网、管网的连通；只看端点，线身靠近不算。'),
            )),
            ('ll_end_on_body', tr('【端点】线的端点搭在参考线身上（T 形接入）'), _tip(
                tr('判定：被命名线的某个端点到参考线身 ≤ 容差，但离参考线的两个端点都 > 容差。'),
                tr('用途：找接到别的线中间、而对方没有在接入处打断的情况。'),
            )),
            ('ll_length_ratio', tr('【比例】精确重叠长度占自身长度 ≥ 比例阈值'), _tip(
                tr('判定：两线坐标完全重叠部分的长度 ÷ 被命名线总长 ≥ 比例阈值（右侧设置，默认 50%）。'),
                _TIP_TOL_UNUSED,
                tr('注意：坐标有微小偏差时重叠长度会是 0，这种情况请用「容差内重合长度占比」。'),
            )),
            ('ll_buffer_length_ratio', tr('【比例】容差内重合长度占自身长度 ≥ 比例阈值'), _tip(
                tr('判定：被命名线落在「参考线扩大容差」范围内的长度 ÷ 被命名线总长 ≥ 比例阈值（右侧设置，默认 50%）。'),
                tr('不要求顶点对齐，比「相邻顶点匹配」更宽容。'),
                tr('用途：判断一条线大部分是否沿着另一条线走。'),
            )),
            ('ll_adjacent_seg_any', tr('【小段】至少一小段与参考线对得上'), _tip(
                tr('判定：被命名线里只要有一小段能匹配即命中。'),
                _TIP_SEG,
                _TIP_SEG_NOTE,
            )),
            ('ll_adjacent_seg_all', tr('【小段】每一小段都与参考线对得上'), _tip(
                tr('判定：被命名线的所有小段都能匹配才命中。'),
                _TIP_SEG,
                _TIP_SEG_NOTE,
            )),
            ('ll_adjacent_seg_ratio', tr('【小段】对得上的小段长度占自身 ≥ 比例阈值'), _tip(
                tr('判定：匹配成功的小段长度之和 ÷ 被命名线总长 ≥ 比例阈值（右侧设置，默认 70%）。'),
                _TIP_SEG,
                _TIP_SEG_NOTE,
            )),
            ('ll_adjacent_seg_any_and_near', tr('【小段】至少一小段对得上（同上，兼容旧方案）'), _tip(
                tr('判定：与「至少一小段与参考线对得上」结果相同。'),
                tr('原设计的附加条件「两线距离 ≤ 容差」在有小段匹配时必然成立，所以不会多筛掉任何线。保留用于兼容 1.0 版方案。'),
            )),
        ],
        (L, G): [
            ('lg_any_intersection', tr('【相交】线与参考面有任何接触（最宽松）'), _tip(
                tr('判定：线与面的内部或边界有任意公共部分。'),
                _TIP_TOL_UNUSED,
            )),
            ('lg_full_within', tr('【包含】线整条在参考面内'), _tip(
                tr('判定：线完全在面内，没有任何部分出界（可以部分贴着边界走）。'),
                _TIP_TOL_UNUSED,
            )),
            ('lg_midpoint_in', tr('【包含】线的中点在参考面内'), _tip(
                tr('判定：沿线走到一半长度处的那个点落在面内（含边界）。'),
                tr('用途：跨了两个面的线，按中点归属到其中一个，避免一条线被两个面同时命中。'),
            )),
            ('lg_inside_length_ratio', tr('【比例】线在面内的长度占线长 ≥ 比例阈值'), _tip(
                tr('判定：线被面截取的部分长度 ÷ 线总长 ≥ 比例阈值（右侧设置，默认 50%）。'),
                tr('用途：跨界线归属到它「大部分所在」的面。'),
            )),
            ('lg_one_endpoint_in', tr('【端点】线一端在面内、另一端在面外'), _tip(
                tr('判定：线的端点里恰好只有 1 个在面内。'),
                _TIP_LG_ENDS,
                tr('用途：找进出面边界的线。'),
            )),
            ('lg_both_ends_in_not_full_within', tr('【端点】两端都在面内，但线身出过界'), _tip(
                tr('判定：所有端点都在面内，但线不是整条在面内（中途穿出去又回来）。'),
                _TIP_LG_ENDS,
            )),
            ('lg_both_ends_out_mid_in', tr('【折点】两端都在面外，但有中间折点在面内'), _tip(
                tr('判定：端点都不在面内，至少一个中间折点在面内。'),
                _TIP_LG_ENDS,
            )),
            ('lg_all_vertices_out_but_intersects', tr('【相交】所有顶点都在面外，线身却穿过面'), _tip(
                tr('判定：线的所有顶点都在面外，但顶点之间的直线段切过了面。'),
                tr('典型：一条长直线段斜切过面的一角。'),
            )),
            ('lg_near', tr('【距离】线到参考面 ≤ 容差（不必接触）'), _tip(
                tr('判定：线与面最近处的距离 ≤ 容差；相交时距离为 0，也命中。'),
            )),
        ],
        (G, P): [
            ('gp_intersects', tr('【包含】参考点在面内或边界上'), _tip(
                tr('判定：参考点在被命名面内部，或正好压在边界上。'),
                _TIP_TOL_UNUSED,
                tr('用途：给面写入面内点的属性，例如地块取门牌号。'),
            )),
            ('gp_contains', tr('【包含】参考点在面内部（不含边界）'), _tip(
                tr('判定：参考点严格在被命名面内部；正好压在边界上的点不算。'),
                _TIP_TOL_UNUSED,
            )),
            ('gp_touches', tr('【边界】参考点正好在面边界上'), _tip(
                tr('判定：参考点压在被命名面的边界线上。'),
                _TIP_TOL_UNUSED,
            )),
            ('gp_near', tr('【距离】参考点在面内，或在面外 ≤ 容差'), _tip(
                tr('判定：相当于把被命名面向外扩大一个容差，参考点落在扩大后的面里就命中。'),
            )),
            ('gp_count_inside', tr('【计数】面内参考点（同「在面内或边界上」）'), _tip(
                tr('判定：与「参考点在面内或边界上」相同。'),
                tr('习惯上配合参考取值「元素数量」使用：统计面内（含边界）有几个参考点。'),
            )),
        ],
        (G, L): [
            ('gl_any_intersection', tr('【相交】参考线与面有任何接触（最宽松）'), _tip(
                tr('判定：参考线与被命名面的内部或边界有任意公共部分。'),
                _TIP_TOL_UNUSED,
            )),
            ('gl_full_within', tr('【包含】参考线整条在面内'), _tip(
                tr('判定：参考线完全在被命名面内，没有任何部分出界。'),
                _TIP_TOL_UNUSED,
            )),
            ('gl_inside_length_ratio', tr('【比例】参考线在面内的长度占参考线长 ≥ 比例阈值'), _tip(
                tr('判定：参考线被面截取的部分长度 ÷ 参考线总长 ≥ 比例阈值（右侧设置，默认 50%）。'),
            )),
            ('gl_one_endpoint_in', tr('【端点】参考线一端在面内、另一端在面外'), _tip(
                tr('判定：参考线的端点里恰好只有 1 个在被命名面内。'),
                _TIP_LG_ENDS,
            )),
            ('gl_both_ends_in_not_full_within', tr('【端点】参考线两端都在面内，但线身出过界'), _tip(
                tr('判定：参考线所有端点都在面内，但不是整条在面内。'),
                _TIP_LG_ENDS,
            )),
            ('gl_both_ends_out_mid_in', tr('【折点】参考线两端在面外，但有中间折点在面内'), _tip(
                tr('判定：参考线端点都不在面内，至少一个中间折点在面内。'),
                _TIP_LG_ENDS,
            )),
            ('gl_all_vertices_out_but_intersects', tr('【相交】参考线所有顶点在面外，线身却穿过面'), _tip(
                tr('判定：参考线的所有顶点都在面外，但线段切过了被命名面。'),
            )),
            ('gl_near', tr('【距离】参考线到面 ≤ 容差（不必接触）'), _tip(
                tr('判定：参考线与被命名面最近处的距离 ≤ 容差；相交时距离为 0，也命中。'),
            )),
        ],
        (G, G): [
            ('gg_inner_point_in', tr('【包含】面的内部点落在参考面内（推荐做面→面归属）'), _tip(
                tr('判定：在被命名面内部取一个保证落在面内的点，这个点在参考面内（含边界）就命中。'),
                tr('用途：图斑归属行政区等。边界有微小错位也不影响，而且每个面通常只会命中一个参考面。'),
            )),
            ('gg_ref_inner_point_in', tr('【包含】参考面的内部点落在本面内'), _tip(
                tr('判定：在参考面内部取一个保证落在面内的点，这个点在被命名面内（含边界）就命中。'),
                tr('用途：大面收集小面的信息，例如行政区统计所含图斑，常配合「全部拼接」或「元素数量」。'),
            )),
            ('gg_intersects', tr('【相交】两面有任何接触（重叠或边界相碰）'), _tip(
                tr('判定：两面有任意公共部分，只碰到一个角也算。'),
                _TIP_TOL_UNUSED,
            )),
            ('gg_overlaps', tr('【相交】两面部分重叠（互不包含）'), _tip(
                tr('判定：两面有重叠区域，但谁也没有完全包住谁；只接边不算。'),
                _TIP_TOL_UNUSED,
            )),
            ('gg_overlap_area_ratio', tr('【比例】重叠面积占本面面积 ≥ 比例阈值'), _tip(
                tr('判定：两面重叠部分面积 ÷ 被命名面面积 ≥ 比例阈值（右侧设置，默认 50%）。'),
                tr('用途：跨界面归属到它「大部分所在」的参考面。'),
            )),
            ('gg_within', tr('【包含】本面完全在参考面内'), _tip(
                tr('判定：被命名面没有任何部分超出参考面。'),
                _TIP_TOL_UNUSED,
                tr('注意：边界稍微出界一点就不命中，这种情况请用「本面在参考面内（允许出界 ≤ 容差）」。'),
            )),
            ('gg_buffer_inside', tr('【包含】本面在参考面内（允许出界 ≤ 容差）'), _tip(
                tr('判定：把参考面向外扩大一个容差后，能完整罩住被命名面。'),
            )),
            ('gg_contains', tr('【包含】本面完全包住参考面'), _tip(
                tr('判定：参考面没有任何部分超出被命名面。'),
                _TIP_TOL_UNUSED,
            )),
            ('gg_touches', tr('【边界】两面只接边、不重叠（相邻）'), _tip(
                tr('判定：两面边界有接触，内部不重叠；只碰一个角也算。'),
                _TIP_TOL_UNUSED,
            )),
            ('gg_shared_edge', tr('【边界】两面共用一段边（只碰一个角不算）'), _tip(
                tr('判定：本面边界贴着参考面边界（≤容差）的长度超过 3×容差。'),
                tr('用途：找真正相邻的图斑；只在一个角点相碰的不算邻居。'),
            )),
            ('gg_equals', tr('【重合】两面完全相同（坐标精确一致）'), _tip(
                tr('判定：两面形状、位置完全一样。'),
                _TIP_TOL_UNUSED,
            )),
            ('gg_almost_equals', tr('【重合】两面基本重合（容差内）'), _tip(
                tr('判定：两面各自扩大容差后，都能完整罩住对方。'),
                tr('用途：同一块面在两个图层里边界有轻微偏差。'),
            )),
            ('gg_near', tr('【距离】两面最近距离 ≤ 容差（不必接触）'), _tip(
                tr('判定：两面最近处的距离 ≤ 容差；相交时距离为 0，也命中。'),
            )),
        ],
    }


def _generic_choice():
    return (
        'generic_tol',
        tr('【距离】两要素最近距离 ≤ 容差（通用）'),
        tr('当前几何组合没有专用模式时使用：只看两个要素最近处的距离是否 ≤ 容差。'),
    )


MODE_CATEGORY_ORDER = (
    '距离', '重合', '端点', '折点', '小段', '包含', '相交', '边界', '比例', '计数', '写入',
)


def mode_category(label):
    """取标题开头「【类别】」或翻译后「[category]」里的类别文字，没有则返回空串。

    只用于下拉分隔，不把类别译文当成内部键。
    """
    s = str(label or '')
    if s.startswith('【') and '】' in s:
        return s[1:s.index('】')]
    if s.startswith('[') and ']' in s:
        return s[1:s.index(']')]
    return ''


def _category_rank(label):
    cat = mode_category(label)
    return MODE_CATEGORY_ORDER.index(cat) if cat in MODE_CATEGORY_ORDER else len(MODE_CATEGORY_ORDER)


def spatial_mode_choices(t_layer, r_layer):
    """按类别排序（同类别内保持表内顺序），界面据此在类别之间插分隔线。"""
    pair = _type_pair(t_layer, r_layer)
    if pair[0] is None or pair[1] is None:
        return [_generic_choice()]
    modes = _mode_tables().get((pair[0], pair[1]))
    if not modes:
        return [_generic_choice()]
    modes = sorted(modes, key=lambda m: _category_rank(m[1]))
    return [_spatial_choice(code, label, tip) for code, label, tip in modes]


def spatial_mode_label(code):
    """不依赖图层，按模式代码取标题（方案列表等处显示用）；未知代码原样返回。"""
    if not code:
        return ''
    if code == 'generic_tol':
        return _generic_choice()[1]
    for modes in _mode_tables().values():
        for c, label, _tip_txt in modes:
            if c == code:
                return label
    return str(code)


MULTI_MATCH_CHOICES = (
    ('nearest', '取距离最近的一个', _tip(
        '按到参考要素的最近距离排序，取第一个。',
        '注意：面与面、线与面等「相交」类模式，命中的参考要素距离往往都是 0，谁排第一不确定，建议改用「取重叠最多的一个」。',
    )),
    ('largest_overlap', '取重叠最多的一个（面积 / 长度）', _tip(
        '面-面：取重叠面积最大的参考面；线-面 / 面-线：取重叠长度最长的；线-线：取容差内贴合长度最长的。',
        '点参与的组合没有面积和长度可比，自动改为「取距离最近」。',
        '用途：跨界要素归属到它大部分所在的那个参考要素。',
    )),
    ('first', '按参考图层顺序取第一个', _tip(
        '按「参考图层列表顺序 → 要素 ID」排序，取第一个。',
        '用途：参考图层之间有优先级时，把优先的图层放前面。',
    )),
    ('join', '全部拼接（按距离排序）', _tip(
        '把所有命中的值用分隔符连起来，距离近的排前面；空值自动跳过。',
    )),
    ('join_unique', '全部拼接并去重', _tip(
        '同「全部拼接」，但相同的值只保留一次。',
        '用途：一个面里有多个同名点时，只写一次名字。',
    )),
    ('most_common', '取出现次数最多的值', _tip(
        '统计命中参考要素的取值，取出现最多的那个；次数相同时取距离更近的。',
        '用途：按多数表决给要素定类别。',
    )),
    ('min_value', '取值最小的一个', _tip(
        '在命中的值里取最小值；全部能转成数字时按数字比较，否则按文字排序。空值跳过。',
    )),
    ('max_value', '取值最大的一个', _tip(
        '在命中的值里取最大值；全部能转成数字时按数字比较，否则按文字排序。空值跳过。',
    )),
    ('skip_multi', '多于一个就不写入（留给人工核查）', _tip(
        '只有恰好命中 1 个参考要素才写入；命中多个时保持原值不动，并计入「多命中统计」。',
    )),
)

MULTI_MATCH_COMMON_TIP = (
    '一个要素同时命中多个参考要素时，按这里的规则决定写入哪个值。\n'
    '所有策略下：一个都没命中时，字段保持原值，不会被清空。'
)


def multi_match_choices():
    """(code, 标题)。1.0 版的 skip_zero 与「取距离最近」完全相同，已从列表移除，旧方案照常按最近处理。"""
    return [(code, tr(label)) for code, label, _t in MULTI_MATCH_CHOICES]


def multi_match_tip(code):
    for c, _label, tip in MULTI_MATCH_CHOICES:
        if c == code:
            return '\n'.join(tr(part) for part in tip.split('\n') if part)
    return ''


def _rect_grow(rect, d):
    if d <= 0:
        return rect
    try:
        rect.grow(d)
        return rect
    except Exception:
        return QgsRectangle(
            rect.xMinimum() - d,
            rect.yMinimum() - d,
            rect.xMaximum() + d,
            rect.yMaximum() + d,
        )


def _geom_distance(g1, g2):
    try:
        d = g1.distance(g2)
        if math.isfinite(d):
            return d
    except Exception:
        pass
    return float('inf')


def _pt_on_or_in_poly(pt_xy, poly_geom):
    if pt_xy is None or poly_geom is None or poly_geom.isEmpty():
        return False
    gpt = QgsGeometry.fromPointXY(pt_xy)
    if gpt.isEmpty():
        return False
    try:
        return poly_geom.intersects(gpt)
    except Exception:
        return False


def _line_all_endpoints(line_geom):
    if line_geom.type() != QgsWkbTypes.LineGeometry:
        return []
    out = []
    if line_geom.isMultipart():
        for part in line_geom.asMultiPolyline():
            if len(part) >= 2:
                out.append(part[0])
                out.append(part[-1])
            elif len(part) == 1:
                out.append(part[0])
    else:
        ln = line_geom.asPolyline()
        if len(ln) >= 2:
            out.append(ln[0])
            out.append(ln[-1])
        elif len(ln) == 1:
            out.append(ln[0])
    return out


def _line_internal_vertices_only(line_geom):
    if line_geom.type() != QgsWkbTypes.LineGeometry:
        return []
    out = []
    if line_geom.isMultipart():
        for part in line_geom.asMultiPolyline():
            if len(part) > 2:
                out.extend(part[1:-1])
    else:
        ln = line_geom.asPolyline()
        if len(ln) > 2:
            out.extend(ln[1:-1])
    return out


def _line_all_vertices(line_geom):
    if line_geom.type() != QgsWkbTypes.LineGeometry:
        return []
    out = []
    if line_geom.isMultipart():
        for part in line_geom.asMultiPolyline():
            out.extend(part)
    else:
        out.extend(line_geom.asPolyline())
    return out


def _line_polygon_suffix_match(suffix, line_geom, poly_geom, tol):
    if suffix == 'near':
        return _geom_distance(line_geom, poly_geom) <= tol
    if line_geom.isEmpty() or poly_geom.isEmpty():
        return False
    if line_geom.type() != QgsWkbTypes.LineGeometry or poly_geom.type() != QgsWkbTypes.PolygonGeometry:
        return False
    eps = _line_all_endpoints(line_geom)
    verts = _line_all_vertices(line_geom)
    internals = _line_internal_vertices_only(line_geom)
    pin = lambda p: _pt_on_or_in_poly(p, poly_geom)
    wi = line_geom.within(poly_geom)
    ix = line_geom.intersects(poly_geom)
    n_ep_in = sum(1 for p in eps if pin(p))
    all_ep_in = bool(eps) and all(pin(p) for p in eps)
    any_int_in = any(pin(p) for p in internals)
    all_v_out = bool(verts) and not any(pin(p) for p in verts)
    if suffix == 'full_within':
        return wi
    if suffix == 'one_endpoint_in':
        if not eps:
            return False
        return (not wi) and n_ep_in == 1
    if suffix == 'both_ends_in_not_full_within':
        if not eps:
            return False
        return (not wi) and all_ep_in
    if suffix == 'both_ends_out_mid_in':
        if not eps:
            return False
        return n_ep_in == 0 and any_int_in
    if suffix == 'all_vertices_out_but_intersects':
        if not verts:
            return False
        return ix and all_v_out
    if suffix == 'any_intersection':
        return ix
    return False


COUNT_ATTACH_ENDPOINT = 'endpoint'
COUNT_ATTACH_VERTEX = 'vertex'
COUNT_ATTACH_ALONG = 'along'


def normalize_count_attach(value):
    s = str(value or '').strip().lower()
    if s in (COUNT_ATTACH_VERTEX, 'any_vertex', 'vertices'):
        return COUNT_ATTACH_VERTEX
    if s in (COUNT_ATTACH_ALONG, 'line', 'body', 'along_line'):
        return COUNT_ATTACH_ALONG
    return COUNT_ATTACH_ENDPOINT


def point_hits_line(pt_geom, line_geom, tol, attach=COUNT_ATTACH_ENDPOINT):
    """点与线是否按挂接位置命中。endpoint=仅端点（旧点关联线数）；vertex=任意折点；along=整条线身。"""
    if pt_geom is None or line_geom is None:
        return False
    if pt_geom.isEmpty() or line_geom.isEmpty() or tol < 0:
        return False
    if pt_geom.type() != QgsWkbTypes.PointGeometry or line_geom.type() != QgsWkbTypes.LineGeometry:
        return False
    kind = normalize_count_attach(attach)
    if kind == COUNT_ATTACH_ENDPOINT:
        return _pl_point_at_ref_line_endpoints(pt_geom, line_geom, tol)
    if kind == COUNT_ATTACH_VERTEX:
        for v in _line_all_vertices_xy(line_geom):
            if _geom_distance(pt_geom, QgsGeometry.fromPointXY(v)) <= tol:
                return True
        return False
    d = _geom_distance(pt_geom, line_geom)
    return math.isfinite(d) and d <= tol


def _pl_point_at_ref_line_endpoints(pt_geom, line_geom, tol):
    if pt_geom.isEmpty() or line_geom.isEmpty():
        return False
    if pt_geom.type() != QgsWkbTypes.PointGeometry or line_geom.type() != QgsWkbTypes.LineGeometry:
        return False
    for a, b in _segment_endpoints_per_part(line_geom):
        da = _geom_distance(pt_geom, QgsGeometry.fromPointXY(a))
        db = _geom_distance(pt_geom, QgsGeometry.fromPointXY(b))
        if min(da, db) <= tol:
            return True
    return False


def _pl_point_at_ref_line_inner_vertex(pt_geom, line_geom, tol):
    if pt_geom.isEmpty() or line_geom.isEmpty():
        return False
    if pt_geom.type() != QgsWkbTypes.PointGeometry or line_geom.type() != QgsWkbTypes.LineGeometry:
        return False
    if _pl_point_at_ref_line_endpoints(pt_geom, line_geom, tol):
        return False
    for v in _line_internal_vertices_only(line_geom):
        if _geom_distance(pt_geom, QgsGeometry.fromPointXY(v)) <= tol:
            return True
    return False


PP_KTH_NEAREST_MODE = 'pp_kth_nearest'
LP_END_FIELDS = 'lp_end_fields'


def _pp_kth_nearest_pick(point_geom, ref_entries, cand_ids, tol, k):
    """点-点：按距离升序取第 K 近，距离≤tol 命中。返回命中 entry（或 None）。"""
    if point_geom.isEmpty() or k <= 0:
        return None
    cand_pairs = []
    for cid in cand_ids:
        if cid < 0 or cid >= len(ref_entries):
            continue
        e = ref_entries[cid]
        g = e.get('geom')
        if g is None or g.isEmpty() or g.type() != QgsWkbTypes.PointGeometry:
            continue
        d = _geom_distance(point_geom, g)
        if not math.isfinite(d):
            continue
        cand_pairs.append((d, e))
    if len(cand_pairs) < k:
        return None
    cand_pairs.sort(key=lambda x: x[0])
    d_k, e_k = cand_pairs[k - 1]
    if d_k > tol:
        return None
    return {'entry': e_k, 'score': d_k}


def aggregate_line_point_field_hits(mode, line_geom, ref_entries, cand_ids, tol, ref_source, param=None):
    """线+参考点聚合模式下的命中列表（字段取值）。"""
    hits = []
    pts_entries = []
    for cid in cand_ids:
        if cid < 0 or cid >= len(ref_entries):
            continue
        e = ref_entries[cid]
        if e['geom'].type() != QgsWkbTypes.PointGeometry:
            continue
        pts_entries.append(e)
    geoms = [e['geom'] for e in pts_entries]
    if not line_point_aggregate_ok(mode, line_geom, geoms, tol, param):
        return hits

    def _near_xy(pt_xy, pg):
        return _geom_distance(QgsGeometry.fromPointXY(pt_xy), pg) <= tol

    for e in pts_entries:
        g = e['geom']
        use = False
        if mode == 'lp_either_endpoint_on_pts':
            for a, b in _segment_endpoints_per_part(line_geom):
                if _near_xy(a, g) or _near_xy(b, g):
                    use = True
                    break
        elif mode in ('lp_any_vertex_on_pts', 'lp_consecutive_segment_endpoints_match'):
            for v in _line_all_vertices_xy(line_geom):
                if _near_xy(v, g):
                    use = True
                    break
        else:
            for a, b in _segment_endpoints_per_part(line_geom):
                if _near_xy(a, g) or _near_xy(b, g):
                    use = True
                    break
        if not use:
            continue
        sc = _geom_distance(line_geom, g)
        raw = _raw_value_from_ref(e, ref_source)
        hits.append({'entry': e, 'score': sc, 'raw': raw})
    return hits


def count_aggregate_line_point_matches(line_geom, ref_entries, cand_ids, tol, mode, param=None):
    """元素数量：聚合线-点模式下计参考点要素数。"""
    rpg = ref_point_geoms_from_candidates(ref_entries, cand_ids)
    if not line_point_aggregate_ok(mode, line_geom, rpg, tol, param):
        return 0

    def _near_xy(pt_xy, pg):
        return _geom_distance(QgsGeometry.fromPointXY(pt_xy), pg) <= tol

    n = 0
    seen = set()
    for cid in cand_ids:
        if cid < 0 or cid >= len(ref_entries):
            continue
        e = ref_entries[cid]
        if e['geom'].type() != QgsWkbTypes.PointGeometry:
            continue
        g = e['geom']
        hit = False
        if mode in ('lp_any_vertex_on_pts', 'lp_consecutive_segment_endpoints_match'):
            verts = _line_all_vertices_xy(line_geom)
            for v in verts:
                if _near_xy(v, g):
                    hit = True
                    break
        else:
            for a, b in _segment_endpoints_per_part(line_geom):
                if _near_xy(a, g) or _near_xy(b, g):
                    hit = True
                    break
        if hit:
            fid = (e['layer'].id(), int(e['feature'].id()))
            if fid not in seen:
                seen.add(fid)
                n += 1
    return n


def _geom_almost_equals(g1, g2, tol):
    if g1.isEmpty() or g2.isEmpty():
        return False
    try:
        if g1.equals(g2):
            return True
    except Exception:
        pass
    if tol <= 0:
        return False
    try:
        b1 = g1.buffer(tol, 8)
        b2 = g2.buffer(tol, 8)
        if b1.isEmpty() or b2.isEmpty():
            return False
        return b1.contains(g2) and b2.contains(g1)
    except Exception:
        return False


def _line_intersection_length(g1, g2):
    """两个几何（至少一条线）相交线性部分的长度（base CRS 单位）。"""
    try:
        if not g1.intersects(g2):
            return 0.0
        xi = g1.intersection(g2)
        if xi.isEmpty():
            return 0.0
        if xi.type() == QgsWkbTypes.LineGeometry:
            return float(xi.length())
        if xi.isMultipart():
            try:
                acc = 0.0
                for part in xi.asGeometryCollection():
                    if part.type() == QgsWkbTypes.LineGeometry:
                        acc += float(part.length())
                return acc
            except Exception:
                pass
        return 0.0
    except Exception:
        return 0.0


def _polygon_area(g):
    try:
        a = float(g.area())
        if math.isfinite(a):
            return abs(a)
    except Exception:
        pass
    return 0.0


def _polygon_intersection_area(g1, g2):
    try:
        if not g1.intersects(g2):
            return 0.0
        xi = g1.intersection(g2)
        if xi.isEmpty():
            return 0.0
        if xi.type() == QgsWkbTypes.PolygonGeometry:
            return _polygon_area(xi)
        if xi.isMultipart():
            try:
                acc = 0.0
                for part in xi.asGeometryCollection():
                    if part.type() == QgsWkbTypes.PolygonGeometry:
                        acc += _polygon_area(part)
                return acc
            except Exception:
                return 0.0
        return 0.0
    except Exception:
        return 0.0


def _safe_buffer(g, d):
    if d <= 0:
        return None
    try:
        b = g.buffer(d, 8)
        if b and not b.isEmpty():
            return b
    except Exception:
        pass
    return None


_V2_MODES = frozenset({
    'lp_head_on_pt',
    'lp_tail_on_pt',
    'll_end_to_end',
    'll_end_on_body',
    'll_buffer_length_ratio',
    'lg_midpoint_in',
    'gg_inner_point_in',
    'gg_ref_inner_point_in',
    'gg_shared_edge',
})


def _xy_within(pt_xy, geom, tol):
    if pt_xy is None:
        return False
    return _geom_distance(QgsGeometry.fromPointXY(pt_xy), geom) <= tol


def _boundary_of(g):
    """QgsGeometry 没有 boundary()，须经 constGet() 取抽象几何的边界。"""
    try:
        b = g.constGet().boundary()
    except Exception:
        return None
    if b is None:
        return None
    bg = QgsGeometry(b)
    return None if bg.isEmpty() else bg


def _inner_point(g):
    try:
        p = g.pointOnSurface()
        if p is not None and not p.isEmpty():
            return p
    except Exception:
        pass
    return None


def _line_len_within_buffer(line_g, other_g, tol):
    if tol <= 0:
        return _line_intersection_length(line_g, other_g)
    bf = _safe_buffer(other_g, tol)
    if bf is None:
        return 0.0
    return _line_intersection_length(line_g, bf)


def _v2_mode_ok(mode, tg, rg, tol, param=None):
    t_type = tg.type()
    r_type = rg.type()
    if mode in ('lp_head_on_pt', 'lp_tail_on_pt'):
        if t_type != QgsWkbTypes.LineGeometry:
            return False
        head, tail = line_head_tail_xy(tg)
        return _xy_within(head if mode == 'lp_head_on_pt' else tail, rg, tol)
    if mode in ('ll_end_to_end', 'll_end_on_body', 'll_buffer_length_ratio'):
        if t_type != QgsWkbTypes.LineGeometry or r_type != QgsWkbTypes.LineGeometry:
            return False
        if mode == 'll_buffer_length_ratio':
            try:
                tlen = float(tg.length())
            except Exception:
                tlen = 0.0
            if tlen <= 0:
                return False
            ratio = _line_len_within_buffer(tg, rg, tol) / tlen * 100.0
            return ratio >= mode_param_value(mode, param)
        t_ends = _line_all_endpoints(tg)
        r_ends = [QgsGeometry.fromPointXY(p) for p in _line_all_endpoints(rg)]
        for p in t_ends:
            pg = QgsGeometry.fromPointXY(p)
            near_end = any(_geom_distance(pg, re) <= tol for re in r_ends)
            if mode == 'll_end_to_end' and near_end:
                return True
            if mode == 'll_end_on_body' and not near_end and _geom_distance(pg, rg) <= tol:
                return True
        return False
    if mode == 'lg_midpoint_in':
        if t_type != QgsWkbTypes.LineGeometry or r_type != QgsWkbTypes.PolygonGeometry:
            return False
        try:
            mid = tg.interpolate(float(tg.length()) * 0.5)
        except Exception:
            return False
        if mid is None or mid.isEmpty():
            return False
        return rg.intersects(mid)
    if mode in ('gg_inner_point_in', 'gg_ref_inner_point_in', 'gg_shared_edge'):
        if t_type != QgsWkbTypes.PolygonGeometry or r_type != QgsWkbTypes.PolygonGeometry:
            return False
        if mode == 'gg_inner_point_in':
            p = _inner_point(tg)
            return p is not None and rg.intersects(p)
        if mode == 'gg_ref_inner_point_in':
            p = _inner_point(rg)
            return p is not None and tg.intersects(p)
        if tol <= 0 or _geom_distance(tg, rg) > tol:
            return False
        tb = _boundary_of(tg)
        rb = _boundary_of(rg)
        if tb is None or rb is None:
            return False
        return _line_len_within_buffer(tb, rb, tol) > tol * 3.0
    return False


def _mode_ok(mode, tg, rg, tol, param=None):
    if tg.isEmpty() or rg.isEmpty():
        return False
    if mode in AGGREGATE_LINE_POINT_MODES:
        return False
    if mode in _V2_MODES:
        return _v2_mode_ok(mode, tg, rg, tol, param)
    dist = _geom_distance(tg, rg)
    if mode == 'pp_tol':
        return dist <= tol
    if mode == 'pp_coincident':
        strict = max(tol * 0.001, 1e-9)
        return dist <= strict
    if mode == 'pl_tol':
        return dist <= tol
    if mode == 'pl_on_line':
        if rg.type() != QgsWkbTypes.LineGeometry:
            return False
        return dist <= tol
    if mode == 'pl_at_ref_line_endpoints':
        if rg.type() != QgsWkbTypes.LineGeometry:
            return False
        return _pl_point_at_ref_line_endpoints(tg, rg, tol)
    if mode == 'pl_at_ref_line_endpoint_only':
        if rg.type() != QgsWkbTypes.LineGeometry:
            return False
        if not _pl_point_at_ref_line_endpoints(tg, rg, tol):
            return False
        for v in _line_internal_vertices_only(rg):
            if _geom_distance(tg, QgsGeometry.fromPointXY(v)) <= tol:
                return False
        return True
    if mode == 'pl_at_ref_line_inner_vertex':
        if rg.type() != QgsWkbTypes.LineGeometry:
            return False
        return _pl_point_at_ref_line_inner_vertex(tg, rg, tol)
    if mode == 'pg_within':
        return tg.within(rg)
    if mode == 'pg_interior_boundary':
        return rg.contains(tg) or tg.intersects(rg)
    if mode == 'pg_boundary_only':
        bnd = _boundary_of(rg)
        if bnd is None:
            return False
        return tg.intersects(bnd) and not tg.within(rg)
    if mode == 'pg_outside_near':
        if rg.contains(tg) or tg.within(rg):
            return True
        return dist <= tol
    if mode == 'pg_min_distance_to_boundary':
        if rg.type() != QgsWkbTypes.PolygonGeometry:
            return False
        bnd = _boundary_of(rg)
        if bnd is None:
            return False
        return _geom_distance(tg, bnd) <= tol
    if mode == 'pp_kth_nearest':
        return False
    if mode == 'lp_endpoint':
        if tg.type() != QgsWkbTypes.LineGeometry:
            return False
        pts = []
        if tg.isMultipart():
            for ln in tg.asMultiPolyline():
                if ln:
                    pts.extend([ln[0], ln[-1]])
        else:
            ln = tg.asPolyline()
            if ln:
                pts.extend([ln[0], ln[-1]])
        for p in pts:
            if _geom_distance(QgsGeometry.fromPointXY(p), rg) <= tol:
                return True
        return False
    if mode == 'lp_any_vertex':
        if tg.type() != QgsWkbTypes.LineGeometry:
            return False
        for v in _line_all_vertices_xy(tg):
            if _geom_distance(QgsGeometry.fromPointXY(v), rg) <= tol:
                return True
        return False
    if mode == 'lp_nearest':
        return dist <= tol
    if mode == 'll_equals':
        return tg.equals(rg)
    if mode == 'll_almost_equals':
        return _geom_almost_equals(tg, rg, tol)
    if mode == 'll_intersects':
        return tg.intersects(rg)
    if mode == 'll_touches':
        return tg.touches(rg)
    if mode == 'll_crosses':
        return tg.crosses(rg)
    if mode == 'll_near':
        return dist <= tol
    if mode == 'll_length_ratio':
        if tg.type() != QgsWkbTypes.LineGeometry or rg.type() != QgsWkbTypes.LineGeometry:
            return False
        try:
            tlen = float(tg.length())
        except Exception:
            tlen = 0.0
        if tlen <= 0:
            return False
        inter_len = _line_intersection_length(tg, rg)
        return (inter_len / tlen) * 100.0 >= mode_param_value(mode, param)
    if mode == 'll_buffer_overlap':
        if tg.type() != QgsWkbTypes.LineGeometry or rg.type() != QgsWkbTypes.LineGeometry:
            return False
        if tg.intersects(rg):
            return True
        if tol <= 0:
            return False
        b1 = _safe_buffer(tg, tol)
        b2 = _safe_buffer(rg, tol)
        if b1 is None or b2 is None:
            return False
        try:
            return b1.intersects(b2)
        except Exception:
            return False
    if mode in (
        'll_adjacent_seg_any',
        'll_adjacent_seg_all',
        'll_adjacent_seg_ratio',
        'll_adjacent_seg_any_and_near',
    ):
        if tg.type() != QgsWkbTypes.LineGeometry or rg.type() != QgsWkbTypes.LineGeometry:
            return False
        mc, tc, ml, tl = _line_adjacent_segment_stats(tg, rg, tol)
        if tc <= 0:
            return False
        if mode == 'll_adjacent_seg_any':
            return mc > 0
        if mode == 'll_adjacent_seg_all':
            return mc >= tc
        if mode == 'll_adjacent_seg_ratio':
            if tl <= 0:
                return False
            return (ml / tl) * 100.0 >= mode_param_value(mode, param)
        return (mc > 0) and (dist <= tol)
    if mode == 'lg_inside_length_ratio':
        if tg.type() != QgsWkbTypes.LineGeometry or rg.type() != QgsWkbTypes.PolygonGeometry:
            return False
        try:
            tlen = float(tg.length())
        except Exception:
            tlen = 0.0
        if tlen <= 0:
            return False
        inter_len = _line_intersection_length(tg, rg)
        return (inter_len / tlen) * 100.0 >= mode_param_value(mode, param)
    if mode == 'gl_inside_length_ratio':
        if tg.type() != QgsWkbTypes.PolygonGeometry or rg.type() != QgsWkbTypes.LineGeometry:
            return False
        try:
            rlen = float(rg.length())
        except Exception:
            rlen = 0.0
        if rlen <= 0:
            return False
        inter_len = _line_intersection_length(rg, tg)
        return (inter_len / rlen) * 100.0 >= mode_param_value(mode, param)
    if mode.startswith('lg_') and tg.type() == QgsWkbTypes.LineGeometry and rg.type() == QgsWkbTypes.PolygonGeometry:
        return _line_polygon_suffix_match(mode[3:], tg, rg, tol)
    if mode.startswith('gl_') and tg.type() == QgsWkbTypes.PolygonGeometry and rg.type() == QgsWkbTypes.LineGeometry:
        return _line_polygon_suffix_match(mode[3:], rg, tg, tol)
    if mode == 'gp_contains':
        return tg.contains(rg)
    if mode == 'gp_intersects':
        return tg.intersects(rg)
    if mode == 'gp_touches':
        return tg.touches(rg)
    if mode == 'gp_near':
        return dist <= tol
    if mode == 'gp_count_inside':
        if tg.type() != QgsWkbTypes.PolygonGeometry or rg.type() != QgsWkbTypes.PointGeometry:
            return False
        try:
            return tg.intersects(rg)
        except Exception:
            return False
    if mode == 'gg_equals':
        return tg.equals(rg)
    if mode == 'gg_almost_equals':
        return _geom_almost_equals(tg, rg, tol)
    if mode == 'gg_intersects':
        return tg.intersects(rg)
    if mode == 'gg_contains':
        return tg.contains(rg)
    if mode == 'gg_within':
        return tg.within(rg)
    if mode == 'gg_touches':
        return tg.touches(rg)
    if mode == 'gg_overlaps':
        return tg.overlaps(rg)
    if mode == 'gg_near':
        return dist <= tol
    if mode == 'gg_overlap_area_ratio':
        if tg.type() != QgsWkbTypes.PolygonGeometry or rg.type() != QgsWkbTypes.PolygonGeometry:
            return False
        ta = _polygon_area(tg)
        if ta <= 0:
            return False
        ia = _polygon_intersection_area(tg, rg)
        return (ia / ta) * 100.0 >= mode_param_value(mode, param)
    if mode == 'gg_buffer_inside':
        if tg.type() != QgsWkbTypes.PolygonGeometry or rg.type() != QgsWkbTypes.PolygonGeometry:
            return False
        try:
            if rg.contains(tg):
                return True
        except Exception:
            pass
        if tol <= 0:
            return False
        bf = _safe_buffer(rg, tol)
        if bf is None:
            return False
        try:
            return bf.contains(tg)
        except Exception:
            return False
    if mode == 'generic_tol':
        return dist <= tol
    return False


def _field_alias_of(field):
    try:
        alias = field.alias()
    except Exception:
        alias = ''
    return (alias or '').strip()


def field_display_label(field):
    name = field.name()
    alias = _field_alias_of(field)
    if alias and alias != name:
        return '{0}（{1}）'.format(alias, name)
    return name


def field_display_label_from_layer(layer, name):
    if layer is None or not name:
        return name or ''
    idx = layer.fields().indexOf(name)
    if idx < 0:
        return name
    return field_display_label(layer.fields().at(idx))


def resolve_field_name(layer_or_fields, key):
    if key is None:
        return None
    key = str(key).strip()
    if not key:
        return None
    inner = None
    outer = key
    if key.endswith('）') and '（' in key:
        inner = key[key.rfind('（') + 1:-1].strip()
        outer = key[:key.rfind('（')].strip()
    if hasattr(layer_or_fields, 'fields'):
        fields = layer_or_fields.fields()
    else:
        fields = layer_or_fields
    if fields is None:
        return None

    def _by_name(s):
        if not s:
            return None
        idx = fields.indexOf(s)
        if idx >= 0:
            return fields.at(idx).name()
        return None

    for candidate in (key, inner, outer):
        hit = _by_name(candidate)
        if hit:
            return hit
    key_low = key.lower()
    alias_exact = None
    name_ci = None
    alias_ci = None
    for i in range(fields.count()):
        f = fields.at(i)
        alias = _field_alias_of(f)
        if alias and (alias == key or alias == outer or (inner and alias == inner)):
            if alias_exact is None:
                alias_exact = f.name()
        if name_ci is None and f.name().lower() == key_low:
            name_ci = f.name()
        if alias_ci is None and alias and alias.lower() == key_low:
            alias_ci = f.name()
    return alias_exact or name_ci or alias_ci


def _field_intersection(layers):
    if not layers:
        return []
    names = None
    for lyr in layers:
        fs = lyr.fields()
        cur = {}
        for i in range(fs.count()):
            f = fs.at(i)
            cur[f.name()] = f
        if names is None:
            names = set(cur.keys())
        else:
            names &= set(cur.keys())
    if not names:
        return []
    first = layers[0].fields()
    out = []
    for i in range(first.count()):
        f = first.at(i)
        if f.name() in names:
            ok = True
            ref_type = f.type()
            for lyr in layers[1:]:
                o = lyr.fields().indexOf(f.name())
                if o < 0:
                    ok = False
                    break
                if lyr.fields().at(o).type() != ref_type:
                    ok = False
                    break
            if ok:
                out.append(f.name())
    return out


def _coerce_for_field(raw, qgs_field):
    if raw is None:
        return None
    t = qgs_field.type()
    if qtype_is(t, "String"):
        return str(raw)
    if any(qtype_is(t, n) for n in ("Int", "LongLong", "UInt", "ULongLong")):
        try:
            return int(raw)
        except Exception:
            return None
    if any(qtype_is(t, n) for n in ("Double")):
        try:
            return float(raw)
        except Exception:
            return None
    if qtype_is(t, "Bool"):
        if isinstance(raw, bool):
            return raw
        s = str(raw).lower()
        if s in ('1', 'true', 'yes', 'y'):
            return True
        if s in ('0', 'false', 'no', 'n'):
            return False
        return None
    if any(qtype_is(t, n) for n in ("Date", "Time", "DateTime")):
        return raw
    if qtype_is(t, "ByteArray"):
        if isinstance(raw, (bytes, bytearray)):
            return bytes(raw)
        try:
            return str(raw).encode('utf-8')
        except Exception:
            return None
    return str(raw)


def _raw_value_from_ref(entry, ref_source):
    layer = entry['layer']
    feat = entry['feature']
    if ref_source == LAYER_NAME_VALUE:
        return layer.name()
    resolved = resolve_field_name(layer, ref_source)
    idx = layer.fields().indexOf(resolved) if resolved else layer.fields().indexOf(ref_source)
    if idx < 0:
        return None
    return feat.attribute(idx)


def _is_blank(v):
    if v is None:
        return True
    try:
        if is_null_qvariant(v):
            return True
    except Exception:
        pass
    return str(v).strip() in ('', 'NULL')


def _overlap_measure(tg, rg, tol):
    """largest_overlap 用：面-面取重叠面积，线参与取重叠长度；点参与返回 None。"""
    t_type = tg.type()
    r_type = rg.type()
    if QgsWkbTypes.PointGeometry in (t_type, r_type):
        return None
    if t_type == QgsWkbTypes.PolygonGeometry and r_type == QgsWkbTypes.PolygonGeometry:
        return _polygon_intersection_area(tg, rg)
    if t_type == QgsWkbTypes.LineGeometry and r_type == QgsWkbTypes.PolygonGeometry:
        return _line_intersection_length(tg, rg)
    if t_type == QgsWkbTypes.PolygonGeometry and r_type == QgsWkbTypes.LineGeometry:
        return _line_intersection_length(rg, tg)
    return _line_len_within_buffer(tg, rg, tol)


def _value_sort_key_fn(vals):
    try:
        [float(v) for v in vals]
        return float
    except (TypeError, ValueError):
        return str


def _pick_values(entries, multi_strategy, join_sep, target_geom=None, tol=0.0):
    """返回 (选中的 hit 或 {'join': 文本}, 命中数)。选中值为 None 表示不写入。"""
    if not entries:
        return None, 0
    n = len(entries)
    if n == 1:
        return entries[0], 1
    by_dist = sorted(entries, key=lambda e: e['score'])
    if multi_strategy == 'skip_multi':
        return None, n
    if multi_strategy == 'first':
        return min(entries, key=lambda e: e['entry'].get('_ix', 0)), n
    if multi_strategy == 'largest_overlap' and target_geom is not None:
        scored = []
        for e in by_dist:
            m = _overlap_measure(target_geom, e['entry']['geom'], tol)
            if m is None:
                return by_dist[0], n
            scored.append((-m, e['score'], e))
        scored.sort(key=lambda x: (x[0], x[1]))
        return scored[0][2], n
    valued = [e for e in by_dist if not _is_blank(e['raw'])]
    if multi_strategy in ('join', 'join_unique'):
        vals = [str(e['raw']) for e in valued]
        if multi_strategy == 'join_unique':
            vals = list(dict.fromkeys(vals))
        if not vals:
            return None, n
        return {'join': join_sep.join(vals)}, n
    if multi_strategy == 'most_common':
        if not valued:
            return by_dist[0], n
        counts = {}
        for e in valued:
            key = str(e['raw'])
            counts[key] = counts.get(key, 0) + 1
        best = max(counts.values())
        return next(e for e in valued if counts[str(e['raw'])] == best), n
    if multi_strategy in ('min_value', 'max_value'):
        if not valued:
            return by_dist[0], n
        conv = _value_sort_key_fn([e['raw'] for e in valued])
        pick = min if multi_strategy == 'min_value' else max
        return pick(valued, key=lambda e: conv(e['raw'])), n
    return by_dist[0], n


def _check_crs(_iface, project, named_layers, ref_layers):
    result = {
        'has_warning': False,
        'message': '',
        'base_crs': None,
    }
    if not named_layers:
        return result
    base = named_layers[0].crs()
    result['base_crs'] = base.authid()
    warns = []
    tids = {lyr.crs().authid() for lyr in named_layers}
    rids = {lyr.crs().authid() for lyr in ref_layers}
    if len(tids) > 1:
        result['has_warning'] = True
        warns.append(tr('被命名图层包含不同坐标系，将以第一个图层为基准转换'))
    if len(rids) > 1:
        result['has_warning'] = True
        warns.append(tr('参考图层包含不同坐标系'))
    if tids != rids or len(tids | rids) > 1:
        result['has_warning'] = True
        warns.append(tr('图层间坐标系不一致时将转换到基准坐标系'))
    geo = sum(1 for lyr in named_layers + ref_layers if lyr.crs().isGeographic())
    prj = len(named_layers) + len(ref_layers) - geo
    if geo and prj:
        result['has_warning'] = True
        warns.append(tr('混合地理坐标与投影坐标可能导致偏差'))
    result['message'] = '\n'.join(warns)
    return result


def line_head_tail_xy(line_geom):
    """线要素的头、尾。多部件：第一个部件的起点，最后一个部件的终点。"""
    if line_geom is None or line_geom.isEmpty() or line_geom.type() != QgsWkbTypes.LineGeometry:
        return None, None
    if line_geom.isMultipart():
        parts = [p for p in (line_geom.asMultiPolyline() or []) if p]
        if not parts:
            return None, None
        return parts[0][0], parts[-1][-1]
    ln = line_geom.asPolyline() or []
    if not ln:
        return None, None
    return ln[0], ln[-1]


def _hits_at_vertex(pt_xy, ref_entries, cand_ids, tol, ref_source):
    hits = []
    if pt_xy is None:
        return hits
    ptg = QgsGeometry.fromPointXY(pt_xy)
    for cid in cand_ids:
        if cid < 0 or cid >= len(ref_entries):
            continue
        e = ref_entries[cid]
        g = e.get('geom')
        if g is None or g.isEmpty() or g.type() != QgsWkbTypes.PointGeometry:
            continue
        dist = _geom_distance(ptg, g)
        if dist <= tol:
            hits.append({
                'entry': e,
                'score': dist,
                'raw': _raw_value_from_ref(e, ref_source),
            })
    return hits


def _end_field_updates(line_geom, ref_entries, cand_ids, tol, end_plan, multi_strategy, join_sep):
    """end_plan: [{slot, ref_source, idx, field}]。返回 (idx->值, 写入字段数, 多命中端数)。"""
    head_xy, tail_xy = line_head_tail_xy(line_geom)
    xy_for = {'head': head_xy, 'tail': tail_xy}
    updates = {}
    written = 0
    multi = 0
    for spec in end_plan:
        hits = _hits_at_vertex(xy_for.get(spec['slot']), ref_entries, cand_ids, tol, spec['ref_source'])
        val, nh = _pick_values(hits, multi_strategy, join_sep, line_geom, tol)
        if nh > 1:
            multi += 1
        if val is None:
            continue
        raw = val['join'] if isinstance(val, dict) and 'join' in val else val['raw']
        coerced = _coerce_for_field(raw, spec['field'])
        if coerced is None:
            continue
        updates[spec['idx']] = coerced
        written += 1
    return updates, written, multi


def _build_ref_state(ref_layers, base_crs, project, category_filters=None):
    entries = []
    for layer in ref_layers:
        xf = None
        if layer.crs() != base_crs:
            xf = QgsCoordinateTransform(layer.crs(), base_crs, project)
        for feat in iter_features(layer, category_filters):
            g = feat.geometry()
            if g.isEmpty():
                continue
            gb = QgsGeometry(g)
            if xf:
                try:
                    gb.transform(xf)
                except Exception:
                    continue
            entries.append({
                'layer': layer,
                'fid': feat.id(),
                'feature': feat,
                'geom': gb,
            })
    idx = QgsSpatialIndex()
    for i, e in enumerate(entries):
        f = QgsFeature(i)
        f.setGeometry(e['geom'])
        idx.addFeature(f)
        e['_ix'] = i
    return entries, idx


def _unique_project_layer_name(project, base_name):
    if project is None:
        return base_name
    name = base_name
    idx = 2
    while project.mapLayersByName(name):
        name = f'{base_name}_{idx}'
        idx += 1
    return name


def _create_memory_clone(base_layer, name_suffix, project=None):
    gt = base_layer.geometryType()
    type_map = {
        QgsWkbTypes.PointGeometry: 'Point',
        QgsWkbTypes.LineGeometry: 'LineString',
        QgsWkbTypes.PolygonGeometry: 'Polygon',
    }
    type_str = type_map.get(gt, 'Point')
    uri = f'{type_str}?crs={base_layer.crs().authid()}'
    base_name = base_layer.name() + name_suffix
    uniq = _unique_project_layer_name(project, base_name) if project is not None else base_name
    out = QgsVectorLayer(uri, uniq, 'memory')
    fields = base_layer.fields()
    if fields.count():
        out.dataProvider().addAttributes(fields.toList())
        out.updateFields()
    return out


def _end_specs_from_params(params, named_layers, ref_layers):
    slots = (
        ('head', 'end_head_ref', 'end_head_named', tr('线头')),
        ('tail', 'end_tail_ref', 'end_tail_named', tr('线尾')),
    )
    specs = []
    for slot, ref_key, named_key, title in slots:
        ref_f = str(params.get(ref_key) or '').strip()
        named_f = str(params.get(named_key) or '').strip()
        if not ref_f and not named_f:
            continue
        if not ref_f or not named_f:
            return None, tr('{0}需要同时选择点字段和线字段，或都留空').format(title)
        resolved_ref = resolve_field_name(ref_layers[0], ref_f)
        resolved_named = resolve_field_name(named_layers[0], named_f)
        specs.append({
            'slot': slot,
            'ref_source': resolved_ref or ref_f,
            'named_field': resolved_named or named_f,
        })
    if not specs:
        return None, tr('请至少填写线头或线尾的一组字段')
    return specs, ''


def run_field_naming(iface, project, named_layers, ref_layers, params):
    quiet = bool(params.get('_quiet'))

    def _fail(msg):
        if not quiet:
            QMessageBox.warning(iface.mainWindow(), tr('提示'), msg)
        return {'ok': False, 'error': msg, 'written': 0}

    if not named_layers:
        return _fail(tr('请选择被命名图层'))
    if not ref_layers:
        return _fail(tr('请选择参考图层'))
    named_field = params.get('named_field')
    ref_source = params.get('ref_value_source')
    if named_field:
        resolved_named = resolve_field_name(named_layers[0], named_field)
        if resolved_named:
            named_field = resolved_named
    if ref_source and ref_source not in (LAYER_NAME_VALUE, REF_ELEMENT_COUNT):
        resolved_ref = resolve_field_name(ref_layers[0], ref_source) if ref_layers else None
        if resolved_ref:
            ref_source = resolved_ref
    spatial_mode = params.get('spatial_mode')
    multi_strategy = params.get('multi_strategy', 'nearest')
    tolerance = float(params.get('tolerance', 0.00001))
    join_sep = params.get('join_sep', ';')
    element_count_rule = params.get('element_count_rule') or default_element_count_rule()
    mode_param = params.get('mode_param')
    end_specs = []
    if spatial_mode == LP_END_FIELDS:
        end_specs, end_err = _end_specs_from_params(params, named_layers, ref_layers)
        if end_err:
            return _fail(end_err)
    elif not named_field or not ref_source or not spatial_mode:
        return _fail(tr('请选择字段与命名模式'))
    kinds_t = {_layer_geom_class(lyr) for lyr in named_layers}
    kinds_r = {_layer_geom_class(lyr) for lyr in ref_layers}
    kinds_t.discard(None)
    kinds_r.discard(None)
    if len(kinds_t) != 1:
        return _fail(tr('被命名图层一侧只能为同一几何类型'))
    if len(kinds_r) != 1:
        return _fail(tr('参考图层一侧只能为同一几何类型'))
    t0 = named_layers[0]
    r0 = ref_layers[0]
    valid_modes = {c[0] for c in spatial_mode_choices(t0, r0)}
    if spatial_mode not in valid_modes:
        return _fail(tr('当前几何组合不支持该命名模式'))
    if spatial_mode == LP_END_FIELDS:
        for lyr in named_layers:
            for spec in end_specs:
                if lyr.fields().indexOf(spec['named_field']) < 0:
                    return _fail(tr('被命名字段不存在'))
        for lyr in ref_layers:
            for spec in end_specs:
                if lyr.fields().indexOf(spec['ref_source']) < 0:
                    return _fail(tr('参考字段不存在'))
    else:
        for lyr in named_layers:
            if lyr.fields().indexOf(named_field) < 0:
                return _fail(tr('被命名字段不存在'))
        if ref_source not in (LAYER_NAME_VALUE, REF_ELEMENT_COUNT):
            for lyr in ref_layers:
                if lyr.fields().indexOf(ref_source) < 0:
                    return _fail(tr('参考字段不存在'))
    crs_info = _check_crs(iface, project, named_layers, ref_layers)
    if crs_info['has_warning'] and not quiet:
        reply = QMessageBox.question(
            iface.mainWindow(),
            tr('坐标系警告'),
            crs_info['message'] + '\n\n' + tr('是否继续执行？'),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.No:
            return _fail(tr('用户取消执行'))
    base_crs = named_layers[0].crs()
    cat_target = params.get('_category_target')
    cat_ref = params.get('_category_ref')
    ref_entries, ref_idx = _build_ref_state(ref_layers, base_crs, project, cat_ref)
    if not ref_entries:
        if not quiet:
            QMessageBox.information(iface.mainWindow(), tr('提示'), tr('参考图层无有效要素'))
        return {'ok': False, 'error': tr('参考图层无有效要素'), 'written': 0, 'error_code': ERR_NO_REF_FEATURES}
    output_direct = params.get('field_output_mode', 'direct') == 'direct'
    if output_direct:
        for lyr in named_layers:
            pl = project.mapLayer(lyr.id())
            if not isinstance(pl, QgsVectorLayer):
                return _fail(tr('直接修改仅支持已加入工程的矢量图层，请改用生成临时图层或先将数据加入工程。'))
    total = sum(lyr.featureCount() for lyr in named_layers)
    progress = None
    if not quiet:
        progress = QProgressDialog(tr('正在处理...'), tr('取消'), 0, max(total, 1), iface.mainWindow())
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)

    def _tick():
        if progress is None:
            return False
        progress.setValue(min(done, total))
        return progress.wasCanceled()
    done = 0
    written = 0
    skipped = 0
    multi_hits = 0
    created = []
    canceled = False
    fail_msg = None
    t_start = time.time()
    for src_lyr in named_layers:
        if output_direct:
            t_layer = project.mapLayer(src_lyr.id())
        else:
            t_layer = src_lyr
        xf_to = None
        if t_layer.crs() != base_crs:
            xf_to = QgsCoordinateTransform(t_layer.crs(), base_crs, project)
        xf_back = None
        if t_layer.crs() != base_crs:
            xf_back = QgsCoordinateTransform(base_crs, t_layer.crs(), project)
        end_plan = []
        nf_idx = -1
        nf_def = None
        if spatial_mode == LP_END_FIELDS:
            for spec in end_specs:
                idx = t_layer.fields().indexOf(spec['named_field'])
                end_plan.append({
                    'slot': spec['slot'],
                    'ref_source': spec['ref_source'],
                    'idx': idx,
                    'field': t_layer.fields().at(idx),
                })
        else:
            nf_idx = t_layer.fields().indexOf(named_field)
            nf_def = t_layer.fields().at(nf_idx)
        if output_direct:
            batch_map = {}
            out_layer = None
            out_feats = None
        else:
            batch_map = None
            out_layer = _create_memory_clone(t_layer, tr('_字段命名'), project=project)
            out_feats = []
        layer_canceled = False
        for feat in iter_features(t_layer, cat_target):
            done += 1
            if _tick():
                canceled = True
                layer_canceled = True
                break
            g = feat.geometry()
            if g.isEmpty():
                continue
            gb = QgsGeometry(g)
            if xf_to:
                try:
                    gb.transform(xf_to)
                except Exception:
                    skipped += 1
                    if not output_direct:
                        new_f = QgsFeature(out_layer.fields())
                        new_f.setAttributes(list(feat.attributes()))
                        new_f.setGeometry(feat.geometry())
                        out_feats.append(new_f)
                    continue
            rect = _rect_grow(gb.boundingBox(), tolerance)
            cand_ids = ref_idx.intersects(rect)
            attrs = list(feat.attributes())
            if spatial_mode == LP_END_FIELDS:
                updates, n_w, n_m = _end_field_updates(
                    gb, ref_entries, list(cand_ids), tolerance, end_plan, multi_strategy, join_sep,
                )
                multi_hits += n_m
                if not updates:
                    skipped += 1
                    if not output_direct:
                        new_f = QgsFeature(out_layer.fields())
                        new_f.setAttributes(attrs)
                        new_f.setGeometry(feat.geometry())
                        out_feats.append(new_f)
                    continue
                for idx, val in updates.items():
                    attrs[idx] = val
                written += n_w
                if output_direct:
                    batch_map[feat.id()] = updates
                else:
                    new_f = QgsFeature(out_layer.fields())
                    new_f.setAttributes(attrs)
                    new_f.setGeometry(feat.geometry())
                    out_feats.append(new_f)
                continue
            if ref_source == REF_ELEMENT_COUNT:
                cand_list = list(cand_ids)
                if spatial_mode in AGGREGATE_LINE_POINT_MODES and gb.type() == QgsWkbTypes.LineGeometry:
                    cnt = count_aggregate_line_point_matches(
                        gb, ref_entries, cand_list, tolerance, spatial_mode, mode_param
                    )
                else:
                    cnt = 0
                    for cid in cand_list:
                        if cid < 0 or cid >= len(ref_entries):
                            continue
                        e = ref_entries[cid]
                        rg = e['geom']
                        if not _mode_ok(spatial_mode, gb, rg, tolerance, mode_param):
                            continue
                        cnt += 1
                raw_out = apply_element_count_rule(cnt, element_count_rule)
                if raw_out is None:
                    skipped += 1
                    if not output_direct:
                        new_f = QgsFeature(out_layer.fields())
                        new_f.setAttributes(attrs)
                        new_f.setGeometry(feat.geometry())
                        out_feats.append(new_f)
                    continue
                coerced = _coerce_for_field(raw_out, nf_def)
            else:
                cand_list = list(cand_ids)
                if spatial_mode in AGGREGATE_LINE_POINT_MODES and gb.type() == QgsWkbTypes.LineGeometry:
                    hits = aggregate_line_point_field_hits(
                        spatial_mode, gb, ref_entries, cand_list, tolerance, ref_source, mode_param
                    )
                elif spatial_mode == PP_KTH_NEAREST_MODE and gb.type() == QgsWkbTypes.PointGeometry:
                    pick = _pp_kth_nearest_pick(
                        gb, ref_entries, cand_list, tolerance, int(mode_param_value(spatial_mode, mode_param))
                    )
                    hits = []
                    if pick is not None:
                        e2 = pick['entry']
                        raw = _raw_value_from_ref(e2, ref_source)
                        hits.append({'entry': e2, 'score': pick['score'], 'raw': raw})
                else:
                    hits = []
                    for cid in cand_list:
                        if cid < 0 or cid >= len(ref_entries):
                            continue
                        e = ref_entries[cid]
                        rg = e['geom']
                        if not _mode_ok(spatial_mode, gb, rg, tolerance, mode_param):
                            continue
                        sc = _geom_distance(gb, rg)
                        raw = _raw_value_from_ref(e, ref_source)
                        hits.append({'entry': e, 'score': sc, 'raw': raw})
                val, nh = _pick_values(hits, multi_strategy, join_sep, gb, tolerance)
                if nh > 1:
                    multi_hits += 1
                if val is None:
                    skipped += 1
                    if not output_direct:
                        new_f = QgsFeature(out_layer.fields())
                        new_f.setAttributes(attrs)
                        new_f.setGeometry(feat.geometry())
                        out_feats.append(new_f)
                    continue
                if isinstance(val, dict) and 'join' in val:
                    coerced = _coerce_for_field(val['join'], nf_def)
                else:
                    coerced = _coerce_for_field(val['raw'], nf_def)
            if coerced is None:
                skipped += 1
                if not output_direct:
                    new_f = QgsFeature(out_layer.fields())
                    new_f.setAttributes(attrs)
                    new_f.setGeometry(feat.geometry())
                    out_feats.append(new_f)
                continue
            attrs[nf_idx] = coerced
            written += 1
            if output_direct:
                batch_map[feat.id()] = coerced
            else:
                new_f = QgsFeature(out_layer.fields())
                new_f.setAttributes(attrs)
                new_f.setGeometry(feat.geometry())
                out_feats.append(new_f)
        if output_direct:
            if batch_map and not layer_canceled:
                if not t_layer.startEditing():
                    fail_msg = tr('无法进入编辑模式，请关闭其他占用该图层的操作后重试。')
                    if not quiet:
                        QMessageBox.warning(iface.mainWindow(), tr('提示'), fail_msg)
                else:
                    write_ok = True
                    for _fid, _val in batch_map.items():
                        if spatial_mode == LP_END_FIELDS:
                            for _idx, _one in _val.items():
                                if not t_layer.changeAttributeValue(_fid, _idx, _one):
                                    write_ok = False
                                    break
                            if not write_ok:
                                break
                        elif not t_layer.changeAttributeValue(_fid, nf_idx, _val):
                            write_ok = False
                            break
                    if not write_ok:
                        t_layer.rollBack()
                        fail_msg = tr('属性写入失败，已回滚。')
                        if not quiet:
                            QMessageBox.warning(iface.mainWindow(), tr('提示'), fail_msg)
                    elif not t_layer.commitChanges():
                        t_layer.rollBack()
                        fail_msg = tr('提交修改失败，已回滚。')
                        if not quiet:
                            QMessageBox.warning(iface.mainWindow(), tr('提示'), fail_msg)
        elif out_feats:
            out_layer.dataProvider().addFeatures(out_feats)
            try:
                from .cdet_memory_style import apply_memory_output_style
            except ImportError:
                from cdet_memory_style import apply_memory_output_style
            apply_memory_output_style(out_layer)
            try:
                from .cdet_output_tree import add_layer_to_output_tree
            except ImportError:
                from cdet_output_tree import add_layer_to_output_tree
            add_layer_to_output_tree(project, out_layer)
            created.append(out_layer.name())
        if canceled:
            break
    if progress is not None:
        progress.close()
    elapsed = time.time() - t_start
    if canceled:
        return {'ok': False, 'error': tr('已取消'), 'written': written, 'skipped': skipped, 'created': created}
    msg = tr('处理完成，用时 {0} 秒\n写入字段次数：{1}\n未写入或跳过：{2}\n多命中统计次数：{3}\n').format(
        f'{elapsed:.2f}', written, skipped, multi_hits)
    if created:
        msg += tr('输出图层：\n') + '\n'.join('  → ' + n for n in created)
    elif output_direct and written > 0:
        msg += tr('已直接写入工程图层的指定字段。\n')
    if not quiet:
        QMessageBox.information(iface.mainWindow(), tr('字段命名'), msg)
    return {
        'ok': fail_msg is None,
        'error': fail_msg,
        'written': written,
        'skipped': skipped,
        'created': created,
    }


def collect_folder_layers(folder_path, geom_filter):
    folder = Path(folder_path)
    paths = []
    paths.extend(folder.glob('**/*.shp'))
    paths.extend(folder.glob('**/*.gpkg'))
    paths.extend(folder.glob('**/*.geojson'))
    layers = []
    seen = set()
    for p in paths:
        s = str(p)
        if s in seen:
            continue
        seen.add(s)
        lyr = QgsVectorLayer(s, p.stem, 'ogr')
        if lyr.isValid() and lyr.featureCount() >= 0:
            layers.append(lyr)
    if geom_filter is None:
        return layers
    out = []
    for lyr in layers:
        k = _geom_kind(lyr.wkbType())
        if k == geom_filter:
            out.append(lyr)
    return out


def folder_geometry_classes(folder_path):
    lyrs = collect_folder_layers(folder_path, None)
    kinds = set()
    for lyr in lyrs:
        kinds.add(_geom_kind(lyr.wkbType()))
    kinds.discard(None)
    return lyrs, kinds
