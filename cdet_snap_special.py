# -*- coding: utf-8 -*-
"""吸附模式特殊参考：基于 EXP.txt 的面检测、线长度规则、组内重叠。"""
from collections import OrderedDict, defaultdict

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor

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
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsMarkerSymbol,
    QgsPalLayerSettings,
    QgsVectorLayerSimpleLabeling,
    QgsTextFormat,
    QgsTextBufferSettings,
    QgsProperty,
)

try:
    from .cdet_polygon_inspect import (
        gather_polygon_workspace,
        intersecting_overlap_details,
        detect_holes_gaps,
        hit_ids_from_overlap_pairs,
    )
    from .cdet_memory_style import apply_memory_output_style
    from .cdet_output_tree import add_layer_to_output_tree
    from .cdet_category import iter_features
    from .cdet_field_naming import (
        _layer_geom_class,
        _build_ref_state,
        _rect_grow,
        normalize_count_attach,
        point_hits_line,
        line_head_tail_xy,
    )
except ImportError:
    from cdet_polygon_inspect import (
        gather_polygon_workspace,
        intersecting_overlap_details,
        detect_holes_gaps,
        hit_ids_from_overlap_pairs,
    )
    from cdet_memory_style import apply_memory_output_style
    from cdet_output_tree import add_layer_to_output_tree
    from cdet_category import iter_features
    from cdet_field_naming import (
        _layer_geom_class,
        _build_ref_state,
        _rect_grow,
        normalize_count_attach,
        point_hits_line,
        line_head_tail_xy,
    )
from .i18n import tr as _i18n_tr
from .errors import NO_REF_FEATURES as ERR_NO_REF_FEATURES
from .qtutil import run_dialog, run_menu, qvariant_type, qtype_is, is_null_qvariant, AppMessageBox as QMessageBox


def _tr(t):
    return _i18n_tr(t)


POLYGON_SUB_OVERLAP_HIT = 'poly_overlap_pick'
POLYGON_SUB_HOLES_LAYER = 'poly_holes'
POLYGON_SUB_GAPS_LAYER = 'poly_gaps'
POLYGON_SUB_GAPS_INTERNAL = 'poly_gaps_internal'
POLYGON_SUB_GAPS_EDGE = 'poly_gaps_edge'
POLYGON_OUT_HOLES_CENTER = 'poly_holes_center'
POLYGON_OUT_GAPS_CENTER = 'poly_gaps_center'
POLYGON_OUT_GAPS_INTERNAL_CENTER = 'poly_gaps_internal_centers'
POLYGON_OUT_GAPS_EDGE_CENTER = 'poly_gaps_edge_centers'
POLYGON_OUT_CENTROID_HIT = 'poly_centroid_overlap'
POLYGON_OUT_CENTROID_ALL = 'poly_centroid_all'
POLYGON_OUT_OVERLAP_FRAGMENTS = 'poly_overlap_fragments'
POLYGON_OUT_OVERLAP_FRAG_CENTER = 'poly_overlap_frag_centers'

POLYGON_OUTPUT_CODES = frozenset({
    POLYGON_SUB_OVERLAP_HIT,
    POLYGON_SUB_HOLES_LAYER,
    POLYGON_SUB_GAPS_INTERNAL,
    POLYGON_SUB_GAPS_EDGE,
    POLYGON_OUT_HOLES_CENTER,
    POLYGON_OUT_GAPS_INTERNAL_CENTER,
    POLYGON_OUT_GAPS_EDGE_CENTER,
    POLYGON_OUT_CENTROID_HIT,
    POLYGON_OUT_CENTROID_ALL,
    POLYGON_OUT_OVERLAP_FRAGMENTS,
    POLYGON_OUT_OVERLAP_FRAG_CENTER,
})

SNAP_KIND_STANDARD = 'standard'
SNAP_KIND_POLYGON = 'polygon_inspect'
SNAP_KIND_LINE_LENGTH = 'line_length'
SNAP_KIND_OVERLAP = 'overlap_self'


def _polyline_length_meters(geom, da):
    if geom.type() != QgsWkbTypes.LineGeometry or geom.isEmpty():
        return None
    try:
        if geom.isMultipart():
            mp = geom.asMultiPolyline()
            m = 0.0
            for part in mp:
                for i in range(len(part) - 1):
                    m += da.measureLine(part[i], part[i + 1])
            return m
        pts = geom.asPolyline()
        if len(pts) < 2:
            return 0.0
        m = 0.0
        for i in range(len(pts) - 1):
            m += da.measureLine(pts[i], pts[i + 1])
        return m
    except Exception:
        try:
            return float(geom.length())
        except Exception:
            return None


def _unique_project_layer_name(project, base_name):
    name = base_name
    idx = 2
    while project.mapLayersByName(name):
        name = f'{base_name}_{idx}'
        idx += 1
    return name


def _snap_memory_output_basename(layer_name, params, snap_enabled):
    """与 cdet_core 标准吸附一致：{图层名}_{方案名}{_已吸附|_未吸附}，无方案名时仅 {图层名}{后缀}。"""
    main_suffix = _tr('_已吸附') if snap_enabled else _tr('_未吸附')
    output_tag = (params.get('_output_tag') or '').strip()
    if output_tag:
        return f'{layer_name}_{output_tag}{main_suffix}'
    return f'{layer_name}{main_suffix}'


def evaluate_length_rule(meters, rule):
    if meters is None or rule is None:
        return False
    k = rule.get('kind', 'le')
    if k == 'le':
        return meters <= float(rule.get('threshold', 0))
    if k == 'ge':
        return meters >= float(rule.get('threshold', 0))
    if k == 'between':
        lo = float(rule.get('t_min', 0))
        hi = float(rule.get('t_max', 1e300))
        return lo <= meters <= hi
    if k == 'eq':
        return abs(meters - float(rule.get('threshold', 0))) < 1e-9
    return meters <= float(rule.get('threshold', 0))


def evaluate_count_rule(count, rule):
    try:
        x = float(count)
    except (TypeError, ValueError):
        return False
    return evaluate_length_rule(x, rule)


def _normalize_polygon_output_codes(seq):
    out = []
    for x in seq:
        sx = str(x)
        if sx == POLYGON_SUB_GAPS_LAYER:
            out.extend([POLYGON_SUB_GAPS_INTERNAL, POLYGON_SUB_GAPS_EDGE])
        elif sx == POLYGON_OUT_GAPS_CENTER:
            out.extend([POLYGON_OUT_GAPS_INTERNAL_CENTER, POLYGON_OUT_GAPS_EDGE_CENTER])
        else:
            out.append(sx)
    seen = set()
    dedup = []
    for z in out:
        if z not in seen:
            seen.add(z)
            dedup.append(z)
    return dedup


def expand_polygon_output_codes_for_tasks(seq):
    """供界面/方案回填：兼容旧字段 poly_gaps / poly_gaps_center。"""
    norm = _normalize_polygon_output_codes([str(x) for x in (seq or [])])
    return [x for x in norm if x in POLYGON_OUTPUT_CODES]


def _polygon_outputs_from_params(params):
    raw = params.get('_polygon_outputs')
    if isinstance(raw, (list, tuple, set)):
        out = expand_polygon_output_codes_for_tasks(raw)
        if out:
            return out
    sub = params.get('_polygon_submode')
    if sub:
        out = expand_polygon_output_codes_for_tasks([sub])
        if out:
            return out
    return [POLYGON_SUB_OVERLAP_HIT]


def _append_gap_poly_and_centers(
    project,
    crs_auth,
    gap_pairs,
    poly_base_name,
    pt_base_name,
    kind_label,
    want_poly,
    want_centers,
    output_tag,
    layers_created,
    placement_key,
):
    """gap_pairs: [(面积㎡, QgsGeometry_polygon), …]"""
    if not gap_pairs:
        return
    if want_poly:
        gap_layer = QgsVectorLayer(f'Polygon?crs={crs_auth}', poly_base_name, 'memory')
        pr = gap_layer.dataProvider()
        pr.addAttributes(
            [
                QgsField('Area_m2', qvariant_type("Double")),
                QgsField('GapKind', qvariant_type("String")),
            ]
        )
        gap_layer.updateFields()
        for a, gm in gap_pairs:
            fx = QgsFeature(gap_layer.fields())
            fx.setGeometry(gm)
            fx.setAttributes([float(a), kind_label])
            pr.addFeature(fx)
        if output_tag:
            gap_layer.setName(f'{gap_layer.name()}_{output_tag}')
        apply_memory_output_style(gap_layer)
        add_layer_to_output_tree(project, gap_layer, placement=placement_key)
        layers_created.append(gap_layer.name())
    if want_centers:
        gp = QgsVectorLayer(f'Point?crs={crs_auth}', pt_base_name, 'memory')
        ppr = gp.dataProvider()
        ppr.addAttributes(
            [
                QgsField('Area_m2', qvariant_type("Double")),
                QgsField('GapKind', qvariant_type("String")),
            ]
        )
        gp.updateFields()
        for a, gm in gap_pairs:
            cg = gm.centroid()
            if cg.isEmpty():
                continue
            pf = QgsFeature(gp.fields())
            pf.setGeometry(cg)
            pf.setAttributes([float(a), kind_label])
            ppr.addFeature(pf)
        if output_tag:
            gp.setName(f'{gp.name()}_{output_tag}')
        apply_memory_output_style(gp)
        add_layer_to_output_tree(project, gp, placement=placement_key)
        layers_created.append(gp.name())


def _append_point_centroid_layer(
    project,
    crs_auth,
    base_name,
    tmpl_lyr,
    pairs_source,
    output_tag,
    layers_created,
    placement='polygon_inspect',
):
    """pairs_source: list of (layer, QgsFeature) 原面要素，输出其质心点。"""
    if not pairs_source:
        return
    extra = [
        QgsField('CentroidX', qvariant_type("Double")),
        QgsField('CentroidY', qvariant_type("Double")),
    ]
    nf = QgsVectorLayer(f'Point?crs={crs_auth}', base_name, 'memory')
    prv = nf.dataProvider()
    flds = tmpl_lyr.fields().toList() + extra
    prv.addAttributes(flds)
    nf.updateFields()
    for lyr, rf in pairs_source:
        g = QgsGeometry(rf.geometry())
        if g.isEmpty():
            continue
        try:
            c = g.centroid()
        except Exception:
            continue
        if c.isEmpty() or c.type() != QgsWkbTypes.PointGeometry:
            continue
        pt = c.asPoint()
        ox = QgsFeature(nf.fields())
        al = list(rf.attributes())[: tmpl_lyr.fields().count()]
        while len(al) < tmpl_lyr.fields().count():
            al.append(None)
        al.extend([float(pt.x()), float(pt.y())])
        ox.setAttributes(al)
        ox.setGeometry(c)
        prv.addFeature(ox)
    if output_tag:
        nf.setName(f'{nf.name()}_{output_tag}')
    apply_memory_output_style(nf)
    add_layer_to_output_tree(project, nf, placement=placement)
    layers_created.append(nf.name())


def run_polygon_snap_branch(iface, project, target_layers, params):
    snap_enabled = params.get('snap_enabled', False)
    outs = _polygon_outputs_from_params(params)
    area_tol = float(params.get('_polygon_area_tol_m2', 1.0))
    output_tag = (params.get('_output_tag') or '').strip()
    show_m = params.get('_show_messages', True)
    mw = iface.mainWindow() if iface else None

    base_crs = target_layers[0].crs()
    valid_geoms, meta, extent_rect, spat_index = gather_polygon_workspace(
        target_layers, base_crs, project, params.get('_category_target')
    )
    if not valid_geoms:
        err = _tr('无有效面要素')
        if show_m and mw:
            QMessageBox.information(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__'}

    ctx = project.transformContext()
    da = QgsDistanceArea()
    da.setSourceCrs(base_crs, ctx)
    try:
        da.setEllipsoid(base_crs.ellipsoidAcronym())
    except Exception:
        pass

    crs_auth = base_crs.authid()
    overlap_details = intersecting_overlap_details(valid_geoms, spat_index, area_tol, da)
    best_pair_area = {}
    for fid, cid, a_m2, _gm, _pidx in overlap_details:
        key = tuple(sorted((fid, cid)))
        if a_m2 > best_pair_area.get(key, 0):
            best_pair_area[key] = a_m2
    overlaps = [(k[0], k[1], v) for k, v in sorted(best_pair_area.items())]
    holes, gaps = detect_holes_gaps(valid_geoms, extent_rect, area_tol, da)
    hit_ids = hit_ids_from_overlap_pairs(overlaps)

    layers_created = []
    summary_bits = []

    def _overlap_face_pairs():
        pairs = []
        for idx in meta:
            lyr, fid, _ = meta[idx]
            inc = idx in hit_ids
            ok = inc if snap_enabled else not inc
            if ok:
                f = lyr.getFeature(fid)
                if f.hasGeometry():
                    pairs.append((lyr, f))
        return pairs

    _place = 'polygon_inspect'

    if POLYGON_OUT_OVERLAP_FRAGMENTS in outs or POLYGON_OUT_OVERLAP_FRAG_CENTER in outs:
        if overlap_details:
            if POLYGON_OUT_OVERLAP_FRAGMENTS in outs:
                frag_lyr = QgsVectorLayer(
                    f'Polygon?crs={crs_auth}', _tr('相交重叠面片'), 'memory'
                )
                prv = frag_lyr.dataProvider()
                prv.addAttributes([
                    QgsField('IdxW1', qvariant_type("Int")),
                    QgsField('IdxW2', qvariant_type("Int")),
                    QgsField('PieceIdx', qvariant_type("Int")),
                    QgsField('SrcFid1', qvariant_type("LongLong")),
                    QgsField('SrcFid2', qvariant_type("LongLong")),
                    QgsField('Layer1', qvariant_type("String")),
                    QgsField('Layer2', qvariant_type("String")),
                    QgsField('Area_m2', qvariant_type("Double")),
                ])
                frag_lyr.updateFields()
                for iw1, iw2, a_m2, g_piece, piece_idx in overlap_details:
                    lyr1, sf1, n1 = meta[iw1]
                    lyr2, sf2, n2 = meta[iw2]
                    fx = QgsFeature(frag_lyr.fields())
                    fx.setGeometry(g_piece)
                    fx.setAttributes(
                        [iw1, iw2, piece_idx, int(sf1), int(sf2), n1 or '', n2 or '', float(a_m2)]
                    )
                    prv.addFeature(fx)
                if output_tag:
                    frag_lyr.setName(f'{frag_lyr.name()}_{output_tag}')
                apply_memory_output_style(frag_lyr)
                add_layer_to_output_tree(project, frag_lyr, placement=_place)
                layers_created.append(frag_lyr.name())
            if POLYGON_OUT_OVERLAP_FRAG_CENTER in outs:
                pt_lyr = QgsVectorLayer(f'Point?crs={crs_auth}', _tr('相交重叠片质心'), 'memory')
                ppr = pt_lyr.dataProvider()
                ppr.addAttributes([
                    QgsField('IdxW1', qvariant_type("Int")),
                    QgsField('IdxW2', qvariant_type("Int")),
                    QgsField('PieceIdx', qvariant_type("Int")),
                    QgsField('Area_m2', qvariant_type("Double")),
                    QgsField('CentroidX', qvariant_type("Double")),
                    QgsField('CentroidY', qvariant_type("Double")),
                ])
                pt_lyr.updateFields()
                for iw1, iw2, a_m2, g_piece, piece_idx in overlap_details:
                    c = g_piece.centroid()
                    if c.isEmpty():
                        continue
                    pxy = c.asPoint()
                    pf = QgsFeature(pt_lyr.fields())
                    pf.setGeometry(c)
                    pf.setAttributes(
                        [
                            iw1,
                            iw2,
                            piece_idx,
                            float(a_m2),
                            float(pxy.x()),
                            float(pxy.y()),
                        ]
                    )
                    ppr.addFeature(pf)
                if output_tag:
                    pt_lyr.setName(f'{pt_lyr.name()}_{output_tag}')
                apply_memory_output_style(pt_lyr)
                add_layer_to_output_tree(project, pt_lyr, placement=_place)
                layers_created.append(pt_lyr.name())
        summary_bits.append(
            _tr('相交重叠面片：{0} 块').format(len(overlap_details))
        )

    if POLYGON_SUB_OVERLAP_HIT in outs:
        pairs = _overlap_face_pairs()
        if pairs:
            tmpl_lyr, _rf = pairs[0]
            nf = QgsVectorLayer(f'Polygon?crs={crs_auth}', _tr('重叠面'), 'memory')
            prv = nf.dataProvider()
            prv.addAttributes(tmpl_lyr.fields().toList())
            nf.updateFields()
            for lyr, rf in pairs:
                ox = QgsFeature(nf.fields())
                al = list(rf.attributes())[: nf.fields().count()]
                while len(al) < nf.fields().count():
                    al.append(None)
                ox.setAttributes(al)
                ox.setGeometry(rf.geometry())
                prv.addFeature(ox)
            if output_tag:
                nf.setName(f'{nf.name()}_{output_tag}')
            apply_memory_output_style(nf)
            add_layer_to_output_tree(project, nf, placement=_place)
            layers_created.append(nf.name())
        summary_bits.append(_tr('重叠面：{0} 对，输出 {1} 个面').format(len(overlaps), len(pairs)))

    if POLYGON_SUB_HOLES_LAYER in outs and holes:
        hole_layer = QgsVectorLayer(f'Polygon?crs={crs_auth}', _tr('内部孔洞'), 'memory')
        pr = hole_layer.dataProvider()
        pr.addAttributes([QgsField('Area_m2', qvariant_type("Double"))])
        hole_layer.updateFields()
        for a, gm in holes:
            fx = QgsFeature(hole_layer.fields())
            fx.setGeometry(gm)
            fx.setAttributes([float(a)])
            pr.addFeature(fx)
        if output_tag:
            hole_layer.setName(f'{hole_layer.name()}_{output_tag}')
        apply_memory_output_style(hole_layer)
        add_layer_to_output_tree(project, hole_layer, placement=_place)
        layers_created.append(hole_layer.name())
    if POLYGON_OUT_HOLES_CENTER in outs and holes:
        hp = QgsVectorLayer(f'Point?crs={crs_auth}', _tr('孔洞中心坐标'), 'memory')
        ppr = hp.dataProvider()
        ppr.addAttributes([QgsField('Area_m2', qvariant_type("Double"))])
        hp.updateFields()
        for a, gm in holes:
            cg = gm.centroid()
            if cg.isEmpty():
                continue
            pf = QgsFeature(hp.fields())
            pf.setGeometry(cg)
            pf.setAttributes([float(a)])
            ppr.addFeature(pf)
        if output_tag:
            hp.setName(f'{hp.name()}_{output_tag}')
        apply_memory_output_style(hp)
        add_layer_to_output_tree(project, hp, placement=_place)
        layers_created.append(hp.name())
    if POLYGON_SUB_HOLES_LAYER in outs or POLYGON_OUT_HOLES_CENTER in outs:
        summary_bits.append(_tr('内部孔洞：{0} 个').format(len(holes)))

    gaps_inner = [(a, g) for a, g, is_outer in gaps if not is_outer]
    gaps_outer = [(a, g) for a, g, is_outer in gaps if is_outer]

    lbl_inner = _tr('斑块间空隙')
    lbl_edge = _tr('外缘留白')
    if POLYGON_SUB_GAPS_INTERNAL in outs or POLYGON_OUT_GAPS_INTERNAL_CENTER in outs:
        _append_gap_poly_and_centers(
            project,
            crs_auth,
            gaps_inner,
            _tr('面间空隙（斑块间）'),
            _tr('斑块间空隙中心'),
            lbl_inner,
            POLYGON_SUB_GAPS_INTERNAL in outs,
            POLYGON_OUT_GAPS_INTERNAL_CENTER in outs,
            output_tag,
            layers_created,
            _place,
        )
    if POLYGON_SUB_GAPS_EDGE in outs or POLYGON_OUT_GAPS_EDGE_CENTER in outs:
        _append_gap_poly_and_centers(
            project,
            crs_auth,
            gaps_outer,
            _tr('面间空隙（外缘）'),
            _tr('外缘留白中心'),
            lbl_edge,
            POLYGON_SUB_GAPS_EDGE in outs,
            POLYGON_OUT_GAPS_EDGE_CENTER in outs,
            output_tag,
            layers_created,
            _place,
        )
    summary_bits.append(_tr('斑块间空隙：{0} 片').format(len(gaps_inner)))
    summary_bits.append(_tr('外缘留白：{0} 片').format(len(gaps_outer)))

    tmpl0 = None
    for idx in sorted(meta.keys()):
        lyr0, fid0, _ = meta[idx]
        f0 = lyr0.getFeature(fid0)
        if f0.hasGeometry():
            tmpl0 = lyr0
            break

    def _pairs_for_centroid_hit():
        """与重叠面图层同一命中规则的点集（质心）。"""
        return _overlap_face_pairs()

    def _pairs_for_centroid_all():
        out = []
        for idx in meta:
            lyr, fid, _ = meta[idx]
            f = lyr.getFeature(fid)
            if f.hasGeometry():
                out.append((lyr, f))
        return out

    if POLYGON_OUT_CENTROID_HIT in outs:
        pch = _pairs_for_centroid_hit()
        if tmpl0 and pch:
            _append_point_centroid_layer(
                project,
                crs_auth,
                _tr('重叠相关面质心'),
                tmpl0,
                pch,
                output_tag,
                layers_created,
            )
        summary_bits.append(_tr('重叠相关质心点：{0} 个').format(len(pch)))

    if POLYGON_OUT_CENTROID_ALL in outs:
        pall = _pairs_for_centroid_all()
        if tmpl0 and pall:
            _append_point_centroid_layer(
                project,
                crs_auth,
                _tr('全部面质心'),
                tmpl0,
                pall,
                output_tag,
                layers_created,
            )
        summary_bits.append(_tr('全部面质心：{0} 个').format(len(pall)))

    if not summary_bits:
        summary_bits = [_tr('未勾选任何输出项')]
    return {
        'ok': True,
        'results': {'layers_created': layers_created},
        'spatial_mode': '__special__',
        'summary_lines': summary_bits,
    }


def run_line_length_snap(iface, project, target_layers, params):
    snap_enabled = params.get('snap_enabled', False)
    rule = params.get('_line_length_rule') or {'kind': 'le', 'threshold': 0}
    base_crs = target_layers[0].crs()

    ctx = project.transformContext()
    da = QgsDistanceArea()
    da.setSourceCrs(base_crs, ctx)
    try:
        da.setEllipsoid(base_crs.ellipsoidAcronym())
    except Exception:
        pass

    pairs = []
    for lyr in target_layers:
        xf = QgsCoordinateTransform(lyr.crs(), base_crs, project) if lyr.crs() != base_crs else None
        for f in iter_features(lyr, params.get('_category_target')):
            g = QgsGeometry(f.geometry())
            if xf:
                try:
                    g.transform(xf)
                except Exception:
                    continue
            mlen = _polyline_length_meters(g, da)
            ok_rule = evaluate_length_rule(mlen, rule)
            want = ok_rule if snap_enabled else not ok_rule
            if want:
                pairs.append((lyr, f))

    layers_created = []
    by_lyr = OrderedDict()
    for lyr, rf in pairs:
        if lyr not in by_lyr:
            by_lyr[lyr] = []
        by_lyr[lyr].append(rf)

    for lyr in by_lyr:
        features = by_lyr[lyr]
        base_name = _snap_memory_output_basename(lyr.name(), params, snap_enabled)
        uniq = _unique_project_layer_name(project, base_name)
        nf = QgsVectorLayer(f'LineString?crs={lyr.crs().authid()}', uniq, 'memory')
        prv = nf.dataProvider()
        prv.addAttributes(lyr.fields().toList())
        nf.updateFields()
        for rf in features:
            ox = QgsFeature(nf.fields())
            al = list(rf.attributes())[: nf.fields().count()]
            while len(al) < nf.fields().count():
                al.append(None)
            ox.setAttributes(al)
            ox.setGeometry(rf.geometry())
            prv.addFeature(ox)
        apply_memory_output_style(nf)
        add_layer_to_output_tree(project, nf)
        layers_created.append(nf.name())

    summary_lines = [_tr('【筛选】按线长度筛选：输出线要素 {0} 个（图层数：{1}）').format(len(pairs), len(by_lyr))]
    return {
        'ok': True,
        'results': {'layers_created': layers_created},
        'spatial_mode': '__special__',
        'summary_lines': summary_lines,
    }


def _gather_points_workspace(layers, base_crs, project, category_filters=None):
    pts = []
    xf_cache = {}

    def _xf(lyr):
        if lyr.crs() == base_crs:
            return None
        k = lyr.crs().authid()
        if k not in xf_cache:
            xf_cache[k] = QgsCoordinateTransform(lyr.crs(), base_crs, project)
        return xf_cache[k]

    for lyr in layers:
        xf = _xf(lyr)
        for f in iter_features(lyr, category_filters):
            g = QgsGeometry(f.geometry())
            if g.isEmpty():
                continue
            if xf:
                try:
                    g.transform(xf)
                except Exception:
                    continue
            if g.type() != QgsWkbTypes.PointGeometry:
                continue
            if g.isMultipart():
                mq = g.asMultiPoint()
            else:
                mq = [g.asPoint()]
            for pq in mq:
                pts.append((lyr, int(f.id()), QgsPointXY(pq)))
    return pts


def _gather_lines_workspace(layers, base_crs, project, category_filters=None):
    items = []
    xf_cache = {}

    def _xf(lyr):
        if lyr.crs() == base_crs:
            return None
        k = lyr.crs().authid()
        if k not in xf_cache:
            xf_cache[k] = QgsCoordinateTransform(lyr.crs(), base_crs, project)
        return xf_cache[k]

    for lyr in layers:
        xf = _xf(lyr)
        for f in iter_features(lyr, category_filters):
            g = QgsGeometry(f.geometry())
            if g.isEmpty():
                continue
            if xf:
                try:
                    g.transform(xf)
                except Exception:
                    continue
            if g.type() != QgsWkbTypes.LineGeometry:
                continue
            idx = len(items)
            items.append((idx, lyr, int(f.id()), g))
    meta = {i[0]: (i[1], i[2]) for i in items}
    geoms = {i[0]: i[3] for i in items}
    return geoms, meta


def _planar_pt_distance(pi, pj):
    return QgsGeometry.fromPointXY(pi).distance(QgsGeometry.fromPointXY(pj))


def _pts_close(pi, pj, tol):
    return _planar_pt_distance(pi, pj) <= tol


def _dedupe_consecutive_polyline(pts, tol):
    if not pts:
        return []
    out = [pts[0]]
    for p in pts[1:]:
        if not _pts_close(p, out[-1], tol):
            out.append(p)
    return out


def _normalize_closed_ring_vertices(pts, tol):
    pts = _dedupe_consecutive_polyline(pts, tol)
    if len(pts) >= 2 and _pts_close(pts[0], pts[-1], tol):
        pts = pts[:-1]
    return pts


def _cyclic_vertex_match(a, b, tol):
    n = len(a)
    if n != len(b) or n == 0:
        return False
    for off in range(n):
        ok = True
        for i in range(n):
            if not _pts_close(a[(i + off) % n], b[i], tol):
                ok = False
                break
        if ok:
            return True
    return False


def _ring_vertices_coincident(ring_a, ring_b, tol):
    ra = _normalize_closed_ring_vertices([QgsPointXY(p) for p in ring_a], tol)
    rb = _normalize_closed_ring_vertices([QgsPointXY(p) for p in ring_b], tol)
    if len(ra) != len(rb) or len(ra) < 3:
        return False
    if _cyclic_vertex_match(ra, rb, tol):
        return True
    return _cyclic_vertex_match(ra, list(reversed(rb)), tol)


def _open_polyline_coincident(va, vb, tol):
    a = _dedupe_consecutive_polyline(va, tol)
    b = _dedupe_consecutive_polyline(vb, tol)
    if len(a) != len(b) or len(a) < 2:
        return False
    if all(_pts_close(a[i], b[i], tol) for i in range(len(a))):
        return True
    br = list(reversed(b))
    return all(_pts_close(a[i], br[i], tol) for i in range(len(a)))


def _polyline_closed_like(pts, tol):
    return len(pts) >= 4 and _pts_close(pts[0], pts[-1], tol)


def _line_vertices_by_parts(geom):
    """折线/多折线：按部件拆成顶点序列列表；曲线尝试 segmentize。"""
    g = QgsGeometry(geom)
    if g.isEmpty() or g.type() != QgsWkbTypes.LineGeometry:
        return []
    out = []
    try:
        if g.isMultipart():
            for pl in g.asMultiPolyline():
                pts = [QgsPointXY(p) for p in pl]
                if len(pts) >= 2:
                    out.append(pts)
        else:
            pl = g.asPolyline()
            if len(pl) >= 2:
                out.append([QgsPointXY(p) for p in pl])
    except Exception:
        out = []
    if not out:
        try:
            seg = QgsGeometry(geom)
            seg = seg.segmentize()
            if not seg.isEmpty() and seg.type() == QgsWkbTypes.LineGeometry:
                return _line_vertices_by_parts(seg)
        except Exception:
            pass
    return out


def _line_pair_vertices_coincident(g1, g2, tol):
    p1 = _line_vertices_by_parts(g1)
    p2 = _line_vertices_by_parts(g2)
    if not p1 or not p2 or len(p1) != len(p2):
        return False
    for va, vb in zip(p1, p2):
        if len(va) != len(vb):
            return False
        ca = _polyline_closed_like(va, tol)
        cb = _polyline_closed_like(vb, tol)
        if ca != cb:
            return False
        if ca:
            ra = _normalize_closed_ring_vertices(va, tol)
            rb = _normalize_closed_ring_vertices(vb, tol)
            if len(ra) != len(rb) or len(ra) < 3:
                return False
            if _cyclic_vertex_match(ra, rb, tol):
                continue
            if _cyclic_vertex_match(ra, list(reversed(rb)), tol):
                continue
            return False
        if not _open_polyline_coincident(va, vb, tol):
            return False
    return True


def _polygon_single_part_match(poly1, poly2, tol):
    if len(poly1) != len(poly2):
        return False
    for r1, r2 in zip(poly1, poly2):
        if not _ring_vertices_coincident(r1, r2, tol):
            return False
    return True


def _polygon_pair_vertices_coincident(g1, g2, tol):
    if g1.isEmpty() or g2.isEmpty():
        return False
    if g1.type() != QgsWkbTypes.PolygonGeometry or g2.type() != QgsWkbTypes.PolygonGeometry:
        return False
    try:
        if g1.isMultipart():
            mp1 = g1.asMultiPolygon()
            mp2 = g2.asMultiPolygon()
            if len(mp1) != len(mp2):
                return False
            return all(_polygon_single_part_match(a, b, tol) for a, b in zip(mp1, mp2))
        return _polygon_single_part_match(g1.asPolygon(), g2.asPolygon(), tol)
    except Exception:
        return False


def _index_candidate_pairs(geoms, tol, spat_index=None):
    """geoms: int→QgsGeometry。用空间索引产出 bbox(扩容差) 相交的 (i, j)，i < j。
    spat_index 为 None 时自建；自带索引须以 geoms 的键作为要素 ID。"""
    if spat_index is None:
        spat_index = QgsSpatialIndex()
        for i, g in geoms.items():
            stub = QgsFeature(int(i))
            stub.setGeometry(g)
            spat_index.addFeature(stub)
    for i in sorted(geoms.keys()):
        try:
            rect = QgsRectangle(geoms[i].boundingBox())
            rect.grow(max(tol, 1e-12))
        except Exception:
            continue
        for j in spat_index.intersects(rect):
            if j > i and j in geoms:
                yield i, j


def compute_overlap_pairs(target_layers, params, base_crs, project, da):
    """返回需输出的 (图层, 要素)；不弹窗。"""
    snap_enabled = params.get('snap_enabled', False)
    tol = float(params.get('tolerance', 0.000001))
    overlap_kind = (params.get('_overlap_kind') or 'polygon').strip()
    pairs_out = []

    if overlap_kind == 'polygon':
        valid_geoms, meta, _extent_rect, spat_index = gather_polygon_workspace(
            target_layers, base_crs, project, params.get('_category_target')
        )
        if not valid_geoms:
            return pairs_out
        hit_ids = set()
        for iai, jbj in _index_candidate_pairs(valid_geoms, tol, spat_index):
            gi = valid_geoms[iai]
            gj = valid_geoms[jbj]
            lyr1, fid1, _n1 = meta[iai]
            lyr2, fid2, _n2 = meta[jbj]
            if lyr2.id() == lyr1.id() and fid2 == fid1:
                continue
            try:
                if _polygon_pair_vertices_coincident(gi, gj, tol):
                    hit_ids.add(iai)
                    hit_ids.add(jbj)
            except Exception:
                continue
        for idx in meta:
            lyr, fid, _ = meta[idx]
            inc = idx in hit_ids
            ok = inc if snap_enabled else not inc
            if ok:
                f = lyr.getFeature(fid)
                if f.hasGeometry():
                    pairs_out.append((lyr, f))
    elif overlap_kind == 'point':
        pts = _gather_points_workspace(
            target_layers, base_crs, project, params.get('_category_target')
        )
        hit_map = {}
        pt_geoms = {i: QgsGeometry.fromPointXY(p) for i, (_l, _f, p) in enumerate(pts)}
        for i, j in _index_candidate_pairs(pt_geoms, tol):
            lyr_i, fid_i, p_i = pts[i]
            lyr_j, fid_j, p_j = pts[j]
            if lyr_j.id() == lyr_i.id() and fid_j == fid_i:
                continue
            if _planar_pt_distance(p_i, p_j) <= tol:
                hit_map[(lyr_i.id(), fid_i)] = True
                hit_map[(lyr_j.id(), fid_j)] = True
        seen = set()
        for lyr, fid, _ in pts:
            key = (lyr.id(), fid)
            if key in seen:
                continue
            inc = hit_map.get(key, False)
            ok = inc if snap_enabled else not inc
            if ok:
                f = lyr.getFeature(fid)
                if f.hasGeometry():
                    pairs_out.append((lyr, f))
                    seen.add(key)
    else:
        geoms, meta = _gather_lines_workspace(
            target_layers, base_crs, project, params.get('_category_target')
        )
        ks = sorted(geoms.keys())
        hit_idx = set()
        for iai, jbj in _index_candidate_pairs(geoms, tol):
            g1 = geoms[iai]
            g2 = geoms[jbj]
            lyr1, fid1 = meta[iai]
            lyr2, fid2 = meta[jbj]
            if lyr2.id() == lyr1.id() and fid2 == fid1:
                continue
            try:
                if _line_pair_vertices_coincident(g1, g2, tol):
                    hit_idx.add(iai)
                    hit_idx.add(jbj)
            except Exception:
                continue
        for i in ks:
            lyr, fid = meta[i]
            inc = i in hit_idx
            ok = inc if snap_enabled else not inc
            if ok:
                f = lyr.getFeature(fid)
                if f.hasGeometry():
                    pairs_out.append((lyr, f))
    return pairs_out


def _write_overlap_memory_layer(project, crs_auth, pairs_out, output_tag):
    geom_map = {
        QgsWkbTypes.PointGeometry: 'Point',
        QgsWkbTypes.LineGeometry: 'LineString',
        QgsWkbTypes.PolygonGeometry: 'Polygon',
    }
    if not pairs_out:
        return None
    tmpl, _ = pairs_out[0]
    gtype = _layer_geom_class(tmpl)
    uri_type = geom_map.get(gtype, 'Polygon')
    lyr_mem = QgsVectorLayer(f'{uri_type}?crs={crs_auth}', _tr('组内重叠'), 'memory')
    prv = lyr_mem.dataProvider()
    prv.addAttributes(tmpl.fields().toList())
    lyr_mem.updateFields()
    for lyr, rf in pairs_out:
        ox = QgsFeature(lyr_mem.fields())
        al = list(rf.attributes())[: lyr_mem.fields().count()]
        while len(al) < lyr_mem.fields().count():
            al.append(None)
        ox.setAttributes(al)
        ox.setGeometry(rf.geometry())
        prv.addFeature(ox)
    if output_tag:
        lyr_mem.setName(f'{lyr_mem.name()}_{output_tag}')
    apply_memory_output_style(lyr_mem)
    add_layer_to_output_tree(project, lyr_mem)
    return lyr_mem.name()


def normalize_overlap_scope(scope):
    """统一四种：单独/集合 × 输出分文件/单文件。旧值 merged → 集合+集合(merged_group)。"""
    s = (scope or 'per_layer').strip()
    if s == 'merged':
        return 'merged_group'
    if s in ('per_layer', 'merged_group', 'merged_concat', 'group_per_layer'):
        return s
    return 'per_layer'


def run_overlap_snap(iface, project, target_layers, params):
    overlap_kind = (params.get('_overlap_kind') or 'polygon').strip()
    output_tag = (params.get('_output_tag') or '').strip()
    scope = normalize_overlap_scope(params.get('_overlap_scope'))
    show_m = params.get('_show_messages', True)
    mw = iface.mainWindow() if iface else None
    # 与主界面「提取已吸附」解耦：重叠检测始终输出「命中重叠关系」的要素，避免误输出大量非重叠要素
    params = dict(params)
    params['snap_enabled'] = True

    type_groups = OrderedDict()
    for lyr in target_layers:
        gk = _layer_geom_class(lyr)
        if gk is None:
            continue
        if gk not in type_groups:
            type_groups[gk] = []
        type_groups[gk].append(lyr)
    if not type_groups:
        err = _tr('无有效判断图层')
        if show_m and mw:
            QMessageBox.warning(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__'}

    wanted_gs = []
    if overlap_kind == 'auto':
        wanted_gs = list(type_groups.keys())
    else:
        kind_to_geom = {
            'point': QgsWkbTypes.PointGeometry,
            'line': QgsWkbTypes.LineGeometry,
            'polygon': QgsWkbTypes.PolygonGeometry,
        }
        wk = kind_to_geom.get(overlap_kind)
        if wk is None:
            wk = QgsWkbTypes.PolygonGeometry
        wanted_gs = [wk]

    base_crs = target_layers[0].crs()
    ctx = project.transformContext()
    da = QgsDistanceArea()
    da.setSourceCrs(base_crs, ctx)
    try:
        da.setEllipsoid(base_crs.ellipsoidAcronym())
    except Exception:
        pass

    crs_auth = base_crs.authid()
    layers_created = []
    total_out = 0

    def _sanitize(s):
        t = ''.join(c if c.isalnum() or c in '_-' else '_' for c in (s or '')[:120])
        return t.strip('_') or 'layer'

    for geom_k in wanted_gs:
        sub_layers = type_groups.get(geom_k) or []
        if not sub_layers:
            continue
        kind_tag = {
            QgsWkbTypes.PointGeometry: 'point',
            QgsWkbTypes.LineGeometry: 'line',
            QgsWkbTypes.PolygonGeometry: 'polygon',
        }.get(geom_k, 'unk')
        p_kind = dict(params)
        p_kind['_overlap_kind'] = kind_tag

        # —— 集合判断（同几何类型的 sub_layers 合一索引；自动模式下点/线/面各为一轮）——
        if scope in ('merged_group', 'group_per_layer'):
            sub_tag_merged = '_'.join(
                [_sanitize(output_tag), _sanitize(kind_tag)] if output_tag else [_sanitize(kind_tag)]
            )
            p_m = dict(p_kind)
            p_m['_output_tag'] = sub_tag_merged[:200]
            pairs_all = compute_overlap_pairs(sub_layers, p_m, base_crs, project, da)
            if scope == 'merged_group':
                total_out += len(pairs_all)
                name = _write_overlap_memory_layer(project, crs_auth, pairs_all, sub_tag_merged[:180])
                if name:
                    layers_created.append(name)
            else:
                # group_per_layer：集合判断，按来源图层分别写出
                by_id = defaultdict(list)
                for lyr_i, feat in pairs_all:
                    by_id[lyr_i.id()].append((lyr_i, feat))
                for lyr in sub_layers:
                    pairs_out = by_id.get(lyr.id(), [])
                    total_out += len(pairs_out)
                    sub_tag = '_'.join(
                        [_sanitize(output_tag), _sanitize(kind_tag), _sanitize(lyr.name())]
                        if output_tag
                        else [_sanitize(kind_tag), _sanitize(lyr.name())]
                    )
                    name = _write_overlap_memory_layer(project, crs_auth, pairs_out, sub_tag[:180])
                    if name:
                        layers_created.append(name)
            continue

        # —— 单独判断：仅各图层内部 ——
        pairs_by_layer = []
        for lyr in sub_layers:
            p_one = dict(p_kind)
            pairs_L = compute_overlap_pairs([lyr], p_one, base_crs, project, da)
            pairs_by_layer.append((lyr, pairs_L))

        if scope == 'per_layer':
            for lyr, pairs_out in pairs_by_layer:
                total_out += len(pairs_out)
                sub_tag = '_'.join(
                    [_sanitize(output_tag), _sanitize(kind_tag), _sanitize(lyr.name())]
                    if output_tag
                    else [_sanitize(kind_tag), _sanitize(lyr.name())]
                )
                name = _write_overlap_memory_layer(project, crs_auth, pairs_out, sub_tag[:180])
                if name:
                    layers_created.append(name)
        else:
            # merged_concat：单独判断 + 集合输出
            combined = []
            for _lyr, pairs_L in pairs_by_layer:
                combined.extend(pairs_L)
            total_out += len(combined)
            sub_tag_one = '_'.join(
                [_sanitize(output_tag), _sanitize(kind_tag)] if output_tag else [_sanitize(kind_tag)]
            )
            name = _write_overlap_memory_layer(project, crs_auth, combined, sub_tag_one[:180])
            if name:
                layers_created.append(name)

    _scope_labels = {
        'per_layer': _tr('单独判断 + 单独输出'),
        'merged_concat': _tr('单独判断 + 集合输出'),
        'group_per_layer': _tr('集合判断 + 单独输出'),
        'merged_group': _tr('集合判断 + 集合输出'),
    }
    mode_txt = _scope_labels.get(scope, scope)
    summary_lines = [
        _tr('{0}｜重叠相关输出要素总数：{1}（输出图层数：{2}）').format(mode_txt, total_out, len(layers_created)),
    ]
    miss_names = params.get('_missing_target_names') or []
    if miss_names:
        summary_lines.append(
            _tr('未在项目中找到的图层（已跳过）：{0}').format(', '.join(str(x) for x in miss_names))
        )
    return {
        'ok': True,
        'results': {'layers_created': layers_created},
        'spatial_mode': '__special__',
        'summary_lines': summary_lines,
    }


def _count_attach_of(params):
    return normalize_count_attach((params or {}).get('_count_attach'))


def _count_output_mates_of(params):
    return bool((params or {}).get('_count_output_mates'))


def _emit_count_feature_groups(project, params, snap_enabled, by_lyr, layers_created, extra_tag=''):
    """by_lyr: OrderedDict[layer, list[QgsFeature]]。extra_tag 非空时追加到临时图层名。"""
    type_map = {
        QgsWkbTypes.PointGeometry: 'Point',
        QgsWkbTypes.LineGeometry: 'LineString',
        QgsWkbTypes.PolygonGeometry: 'Polygon',
    }
    for lyr in by_lyr:
        features = by_lyr[lyr]
        if not features:
            continue
        base_name = _snap_memory_output_basename(lyr.name(), params, snap_enabled)
        if extra_tag:
            base_name = '{}_{}'.format(base_name, extra_tag)
        uniq = _unique_project_layer_name(project, base_name)
        type_str = type_map.get(_layer_geom_class(lyr), 'Point')
        nf = QgsVectorLayer(f'{type_str}?crs={lyr.crs().authid()}', uniq, 'memory')
        prv = nf.dataProvider()
        prv.addAttributes(lyr.fields().toList())
        nf.updateFields()
        for rf in features:
            ox = QgsFeature(nf.fields())
            al = list(rf.attributes())[: nf.fields().count()]
            while len(al) < nf.fields().count():
                al.append(None)
            ox.setAttributes(al)
            ox.setGeometry(rf.geometry())
            prv.addFeature(ox)
        apply_memory_output_style(nf)
        add_layer_to_output_tree(project, nf)
        layers_created.append(nf.name())


def _add_mate_entry(by_lyr, seen_keys, entry):
    lyr = entry.get('layer')
    feat = entry.get('feature')
    if lyr is None or feat is None:
        return
    key = (lyr.id(), int(entry.get('fid', feat.id())))
    if key in seen_keys:
        return
    seen_keys.add(key)
    if lyr not in by_lyr:
        by_lyr[lyr] = []
    by_lyr[lyr].append(feat)


def _lines_hitting_point(ptg, ref_entries, ref_idx, tol, attach):
    rect = _rect_grow(ptg.boundingBox(), tol)
    cand_ids = ref_idx.intersects(rect)
    n_line = 0
    mates = []
    seen = set()
    for cid in cand_ids:
        if cid < 0 or cid >= len(ref_entries):
            continue
        e = ref_entries[cid]
        if e['geom'].type() != QgsWkbTypes.LineGeometry:
            continue
        key = (e['layer'].id(), int(e['fid']))
        if key in seen:
            continue
        if not point_hits_line(ptg, e['geom'], tol, attach):
            continue
        seen.add(key)
        n_line += 1
        mates.append(e)
    return n_line, mates


def _points_hitting_line(line_g, ref_entries, ref_idx, tol, attach):
    rect = _rect_grow(line_g.boundingBox(), tol)
    cand_ids = ref_idx.intersects(rect)
    n_pt = 0
    mates = []
    seen = set()
    for cid in cand_ids:
        if cid < 0 or cid >= len(ref_entries):
            continue
        e = ref_entries[cid]
        if e['geom'].type() != QgsWkbTypes.PointGeometry:
            continue
        key = (e['layer'].id(), int(e['fid']))
        if key in seen:
            continue
        if not point_hits_line(e['geom'], line_g, tol, attach):
            continue
        seen.add(key)
        n_pt += 1
        mates.append(e)
    return n_pt, mates


def run_point_line_count_snap(iface, project, target_layers, ref_layers, params):
    """判断图层：点；参考：线。按挂接位置统计关联线件数，再以个数规则筛选，输出点图层。"""
    tol = float(params.get('tolerance', 0))
    rule = params.get('_snap_count_rule') or {'kind': 'le', 'threshold': 0}
    snap_enabled = bool(params.get('snap_enabled', True))
    attach = _count_attach_of(params)
    want_mates = _count_output_mates_of(params)
    show_m = params.get('_show_messages', True)
    mw = iface.mainWindow() if iface else None

    if not target_layers:
        err = _tr('未选择判断图层')
        if show_m and mw:
            QMessageBox.warning(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__'}
    if not ref_layers:
        err = _tr('【计数】点上接了几条线：请选择参考线图层')
        if show_m and mw:
            QMessageBox.warning(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__'}
    for lyr in target_layers:
        if _layer_geom_class(lyr) != QgsWkbTypes.PointGeometry:
            err = _tr('【计数】点上接了几条线：判断图层须为点图层')
            if show_m and mw:
                QMessageBox.warning(mw, _tr('提示'), err)
            return {'ok': False, 'error': err, 'spatial_mode': '__special__'}
    for lyr in ref_layers:
        if _layer_geom_class(lyr) != QgsWkbTypes.LineGeometry:
            err = _tr('【计数】点上接了几条线：参考图层须均为线图层')
            if show_m and mw:
                QMessageBox.warning(mw, _tr('提示'), err)
            return {'ok': False, 'error': err, 'spatial_mode': '__special__'}

    base_crs = target_layers[0].crs()
    ref_entries, ref_idx = _build_ref_state(
        ref_layers, base_crs, project, params.get('_category_ref')
    )
    if not ref_entries:
        err = _tr('参考线图层无有效要素')
        if show_m and mw:
            QMessageBox.warning(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__', 'error_code': ERR_NO_REF_FEATURES}

    pairs = []
    mate_by_lyr = OrderedDict()
    mate_seen = set()
    for lyr in target_layers:
        xf = QgsCoordinateTransform(lyr.crs(), base_crs, project) if lyr.crs() != base_crs else None
        for f in iter_features(lyr, params.get('_category_target')):
            g = QgsGeometry(f.geometry())
            if g.isEmpty():
                continue
            if xf:
                try:
                    g.transform(xf)
                except Exception:
                    continue
            if g.type() != QgsWkbTypes.PointGeometry:
                continue
            mq = g.asMultiPoint() if g.isMultipart() else [g.asPoint()]
            max_n = 0
            hit_mates = []
            for pq in mq:
                ptg = QgsGeometry.fromPointXY(pq)
                n_line, mates = _lines_hitting_point(ptg, ref_entries, ref_idx, tol, attach)
                max_n = max(max_n, n_line)
                hit_mates.extend(mates)
            ok_rule = evaluate_count_rule(max_n, rule)
            want = ok_rule if snap_enabled else (not ok_rule)
            if want:
                pairs.append((lyr, f))
                if want_mates:
                    for e in hit_mates:
                        _add_mate_entry(mate_by_lyr, mate_seen, e)

    layers_created = []
    by_lyr = OrderedDict()
    for lyr, rf in pairs:
        if lyr not in by_lyr:
            by_lyr[lyr] = []
        by_lyr[lyr].append(rf)
    _emit_count_feature_groups(project, params, snap_enabled, by_lyr, layers_created)
    if want_mates:
        _emit_count_feature_groups(
            project, params, snap_enabled, mate_by_lyr, layers_created, extra_tag=_tr('关联线')
        )

    summary_lines = [
        _tr('【计数】点上接了几条线：输出点要素 {0}（临时图层数 {1}）').format(len(pairs), len(layers_created)),
    ]
    return {
        'ok': True,
        'results': {'layers_created': layers_created},
        'spatial_mode': '__special__',
        'summary_lines': summary_lines,
    }


def run_line_point_count_snap(iface, project, target_layers, ref_layers, params):
    """判断图层：线；参考：点。按挂接位置统计线上点数，再以个数规则筛选，输出线图层。"""
    tol = float(params.get('tolerance', 0))
    rule = params.get('_snap_count_rule') or {'kind': 'le', 'threshold': 0}
    snap_enabled = bool(params.get('snap_enabled', True))
    attach = _count_attach_of(params)
    want_mates = _count_output_mates_of(params)
    show_m = params.get('_show_messages', True)
    mw = iface.mainWindow() if iface else None

    if not target_layers:
        err = _tr('未选择判断图层')
        if show_m and mw:
            QMessageBox.warning(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__'}
    if not ref_layers:
        err = _tr('【计数】线上挂了几个点：请选择参考点图层')
        if show_m and mw:
            QMessageBox.warning(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__'}
    for lyr in target_layers:
        if _layer_geom_class(lyr) != QgsWkbTypes.LineGeometry:
            err = _tr('【计数】线上挂了几个点：判断图层须为线图层')
            if show_m and mw:
                QMessageBox.warning(mw, _tr('提示'), err)
            return {'ok': False, 'error': err, 'spatial_mode': '__special__'}
    for lyr in ref_layers:
        if _layer_geom_class(lyr) != QgsWkbTypes.PointGeometry:
            err = _tr('【计数】线上挂了几个点：参考图层须均为点图层')
            if show_m and mw:
                QMessageBox.warning(mw, _tr('提示'), err)
            return {'ok': False, 'error': err, 'spatial_mode': '__special__'}

    base_crs = target_layers[0].crs()
    ref_entries, ref_idx = _build_ref_state(
        ref_layers, base_crs, project, params.get('_category_ref')
    )
    if not ref_entries:
        err = _tr('参考点图层无有效要素')
        if show_m and mw:
            QMessageBox.warning(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__', 'error_code': ERR_NO_REF_FEATURES}

    pairs = []
    mate_by_lyr = OrderedDict()
    mate_seen = set()
    for lyr in target_layers:
        xf = QgsCoordinateTransform(lyr.crs(), base_crs, project) if lyr.crs() != base_crs else None
        for f in iter_features(lyr, params.get('_category_target')):
            g = QgsGeometry(f.geometry())
            if g.isEmpty():
                continue
            if xf:
                try:
                    g.transform(xf)
                except Exception:
                    continue
            if g.type() != QgsWkbTypes.LineGeometry:
                continue
            n_pt, mates = _points_hitting_line(g, ref_entries, ref_idx, tol, attach)
            ok_rule = evaluate_count_rule(n_pt, rule)
            want = ok_rule if snap_enabled else (not ok_rule)
            if want:
                pairs.append((lyr, f))
                if want_mates:
                    for e in mates:
                        _add_mate_entry(mate_by_lyr, mate_seen, e)

    layers_created = []
    by_lyr = OrderedDict()
    for lyr, rf in pairs:
        if lyr not in by_lyr:
            by_lyr[lyr] = []
        by_lyr[lyr].append(rf)
    _emit_count_feature_groups(project, params, snap_enabled, by_lyr, layers_created)
    if want_mates:
        _emit_count_feature_groups(
            project, params, snap_enabled, mate_by_lyr, layers_created, extra_tag=_tr('关联点')
        )

    summary_lines = [
        _tr('【计数】线上挂了几个点：输出线要素 {0}（临时图层数 {1}）').format(len(pairs), len(layers_created)),
    ]
    return {
        'ok': True,
        'results': {'layers_created': layers_created},
        'spatial_mode': '__special__',
        'summary_lines': summary_lines,
    }


def run_polygon_point_count_snap(iface, project, target_layers, ref_layers, params):
    """判断图层：面；参考：点。统计与面相交（含边界）的参考点件数，输出面图层。"""
    tol = float(params.get('tolerance', 0))
    rule = params.get('_snap_count_rule') or {'kind': 'le', 'threshold': 0}
    snap_enabled = bool(params.get('snap_enabled', True))
    show_m = params.get('_show_messages', True)
    mw = iface.mainWindow() if iface else None

    if not target_layers:
        err = _tr('未选择判断图层')
        if show_m and mw:
            QMessageBox.warning(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__'}
    if not ref_layers:
        err = _tr('【计数】面内有几个点：请选择参考点图层')
        if show_m and mw:
            QMessageBox.warning(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__'}
    for lyr in target_layers:
        if _layer_geom_class(lyr) != QgsWkbTypes.PolygonGeometry:
            err = _tr('【计数】面内有几个点：判断图层须为面图层')
            if show_m and mw:
                QMessageBox.warning(mw, _tr('提示'), err)
            return {'ok': False, 'error': err, 'spatial_mode': '__special__'}
    for lyr in ref_layers:
        if _layer_geom_class(lyr) != QgsWkbTypes.PointGeometry:
            err = _tr('【计数】面内有几个点：参考图层须均为点图层')
            if show_m and mw:
                QMessageBox.warning(mw, _tr('提示'), err)
            return {'ok': False, 'error': err, 'spatial_mode': '__special__'}

    base_crs = target_layers[0].crs()
    ref_entries, ref_idx = _build_ref_state(
        ref_layers, base_crs, project, params.get('_category_ref')
    )
    if not ref_entries:
        err = _tr('参考点图层无有效要素')
        if show_m and mw:
            QMessageBox.warning(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__', 'error_code': ERR_NO_REF_FEATURES}

    pairs = []
    for lyr in target_layers:
        xf = QgsCoordinateTransform(lyr.crs(), base_crs, project) if lyr.crs() != base_crs else None
        for f in iter_features(lyr, params.get('_category_target')):
            g = QgsGeometry(f.geometry())
            if g.isEmpty():
                continue
            if xf:
                try:
                    g.transform(xf)
                except Exception:
                    continue
            if g.type() != QgsWkbTypes.PolygonGeometry:
                continue
            rect = _rect_grow(g.boundingBox(), tol)
            cand_ids = ref_idx.intersects(rect)
            seen = set()
            n_pt = 0
            for cid in cand_ids:
                if cid < 0 or cid >= len(ref_entries):
                    continue
                e = ref_entries[cid]
                if e['geom'].type() != QgsWkbTypes.PointGeometry:
                    continue
                key = (e['layer'].id(), int(e['fid']))
                if key in seen:
                    continue
                try:
                    hit = g.intersects(e['geom'])
                except Exception:
                    hit = False
                if hit:
                    seen.add(key)
                    n_pt += 1
            ok_rule = evaluate_count_rule(n_pt, rule)
            want = ok_rule if snap_enabled else (not ok_rule)
            if want:
                pairs.append((lyr, f))

    layers_created = []
    by_lyr = OrderedDict()
    for lyr, rf in pairs:
        if lyr not in by_lyr:
            by_lyr[lyr] = []
        by_lyr[lyr].append(rf)

    for lyr in by_lyr:
        features = by_lyr[lyr]
        base_name = _snap_memory_output_basename(lyr.name(), params, snap_enabled)
        uniq = _unique_project_layer_name(project, base_name)
        nf = QgsVectorLayer(f'Polygon?crs={lyr.crs().authid()}', uniq, 'memory')
        prv = nf.dataProvider()
        prv.addAttributes(lyr.fields().toList())
        nf.updateFields()
        for rf in features:
            ox = QgsFeature(nf.fields())
            al = list(rf.attributes())[: nf.fields().count()]
            while len(al) < nf.fields().count():
                al.append(None)
            ox.setAttributes(al)
            ox.setGeometry(rf.geometry())
            prv.addFeature(ox)
        apply_memory_output_style(nf)
        add_layer_to_output_tree(project, nf)
        layers_created.append(nf.name())

    summary_lines = [
        _tr('【计数】面内有几个点：输出面要素 {0}（临时图层数 {1}）').format(len(pairs), len(by_lyr)),
    ]
    return {
        'ok': True,
        'results': {'layers_created': layers_created},
        'spatial_mode': '__special__',
        'summary_lines': summary_lines,
    }


def run_polygon_line_count_snap(iface, project, target_layers, ref_layers, params):
    """判断图层：面；参考：线。统计与面相交的参考线件数，输出面图层。"""
    tol = float(params.get('tolerance', 0))
    rule = params.get('_snap_count_rule') or {'kind': 'le', 'threshold': 0}
    snap_enabled = bool(params.get('snap_enabled', True))
    show_m = params.get('_show_messages', True)
    mw = iface.mainWindow() if iface else None

    if not target_layers:
        err = _tr('未选择判断图层')
        if show_m and mw:
            QMessageBox.warning(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__'}
    if not ref_layers:
        err = _tr('【计数】与面相交的线有几条：请选择参考线图层')
        if show_m and mw:
            QMessageBox.warning(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__'}
    for lyr in target_layers:
        if _layer_geom_class(lyr) != QgsWkbTypes.PolygonGeometry:
            err = _tr('【计数】与面相交的线有几条：判断图层须为面图层')
            if show_m and mw:
                QMessageBox.warning(mw, _tr('提示'), err)
            return {'ok': False, 'error': err, 'spatial_mode': '__special__'}
    for lyr in ref_layers:
        if _layer_geom_class(lyr) != QgsWkbTypes.LineGeometry:
            err = _tr('【计数】与面相交的线有几条：参考图层须均为线图层')
            if show_m and mw:
                QMessageBox.warning(mw, _tr('提示'), err)
            return {'ok': False, 'error': err, 'spatial_mode': '__special__'}

    base_crs = target_layers[0].crs()
    ref_entries, ref_idx = _build_ref_state(
        ref_layers, base_crs, project, params.get('_category_ref')
    )
    if not ref_entries:
        err = _tr('参考线图层无有效要素')
        if show_m and mw:
            QMessageBox.warning(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__', 'error_code': ERR_NO_REF_FEATURES}

    pairs = []
    for lyr in target_layers:
        xf = QgsCoordinateTransform(lyr.crs(), base_crs, project) if lyr.crs() != base_crs else None
        for f in iter_features(lyr, params.get('_category_target')):
            g = QgsGeometry(f.geometry())
            if g.isEmpty():
                continue
            if xf:
                try:
                    g.transform(xf)
                except Exception:
                    continue
            if g.type() != QgsWkbTypes.PolygonGeometry:
                continue
            rect = _rect_grow(g.boundingBox(), tol)
            cand_ids = ref_idx.intersects(rect)
            seen = set()
            n_ln = 0
            for cid in cand_ids:
                if cid < 0 or cid >= len(ref_entries):
                    continue
                e = ref_entries[cid]
                if e['geom'].type() != QgsWkbTypes.LineGeometry:
                    continue
                key = (e['layer'].id(), int(e['fid']))
                if key in seen:
                    continue
                try:
                    hit = g.intersects(e['geom'])
                except Exception:
                    hit = False
                if hit:
                    seen.add(key)
                    n_ln += 1
            ok_rule = evaluate_count_rule(n_ln, rule)
            want = ok_rule if snap_enabled else (not ok_rule)
            if want:
                pairs.append((lyr, f))

    layers_created = []
    by_lyr = OrderedDict()
    for lyr, rf in pairs:
        if lyr not in by_lyr:
            by_lyr[lyr] = []
        by_lyr[lyr].append(rf)

    for lyr in by_lyr:
        features = by_lyr[lyr]
        base_name = _snap_memory_output_basename(lyr.name(), params, snap_enabled)
        uniq = _unique_project_layer_name(project, base_name)
        nf = QgsVectorLayer(f'Polygon?crs={lyr.crs().authid()}', uniq, 'memory')
        prv = nf.dataProvider()
        prv.addAttributes(lyr.fields().toList())
        nf.updateFields()
        for rf in features:
            ox = QgsFeature(nf.fields())
            al = list(rf.attributes())[: nf.fields().count()]
            while len(al) < nf.fields().count():
                al.append(None)
            ox.setAttributes(al)
            ox.setGeometry(rf.geometry())
            prv.addFeature(ox)
        apply_memory_output_style(nf)
        add_layer_to_output_tree(project, nf)
        layers_created.append(nf.name())

    summary_lines = [
        _tr('【计数】与面相交的线有几条：输出面要素 {0}（临时图层数 {1}）').format(len(pairs), len(by_lyr)),
    ]
    return {
        'ok': True,
        'results': {'layers_created': layers_created},
        'spatial_mode': '__special__',
        'summary_lines': summary_lines,
    }


def _line_end_color(index):
    """按黄金角取色，相邻线颜色分开，同一条线的头尾同色。"""
    hue = int(((max(index, 1) - 1) * 137.508) % 360)
    return QColor.fromHsv(hue, 210, 230)


def _style_line_end_points(layer, pair_count):
    base = QgsMarkerSymbol.createSimple({
        'name': 'circle',
        'size': '3.2',
        'outline_width': '0.45',
        'color': '#339af0',
        'outline_color': '#1864ab',
    })
    try:
        from qgis.core import QgsSimpleMarkerSymbolLayer
        base.symbolLayer(0).setDataDefinedProperty(
            QgsSimpleMarkerSymbolLayer.PropertyShape,
            QgsProperty.fromExpression("if(\"端\"='起点','circle','square')"),
        )
    except Exception:
        pass
    categories = []
    for n in range(1, int(pair_count) + 1):
        sym = base.clone()
        color = _line_end_color(n)
        sym.setColor(color)
        try:
            sym.symbolLayer(0).setStrokeColor(color.darker(130))
        except Exception:
            pass
        categories.append(QgsRendererCategory(n, sym, str(n), True))
    layer.setRenderer(QgsCategorizedSymbolRenderer('序号', categories))
    try:
        pal = QgsPalLayerSettings()
        pal.fieldName = '标记'
        pal.enabled = True
        try:
            pal.placement = QgsPalLayerSettings.OverPoint
        except Exception:
            pass
        try:
            from qgis.core import QgsUnitTypes
            pal.yOffset = 2.4
            pal.offsetUnits = QgsUnitTypes.RenderMillimeters
        except Exception:
            pass
        fmt = QgsTextFormat()
        fmt.setSize(9)
        fmt.setColor(QColor('#212529'))
        try:
            from qgis.PyQt.QtGui import QFont
            font = QFont()
            font.setBold(True)
            fmt.setFont(font)
        except Exception:
            pass
        buf = QgsTextBufferSettings()
        buf.setEnabled(True)
        buf.setSize(1.0)
        buf.setColor(QColor(255, 255, 255, 230))
        fmt.setBuffer(buf)
        pal.setFormat(fmt)
        try:
            color_key = getattr(QgsPalLayerSettings, 'Color', None)
            if color_key is None:
                color_key = QgsPalLayerSettings.Property.Color
            pal.dataDefinedProperties().setProperty(
                color_key,
                QgsProperty.fromField('颜色'),
            )
        except Exception:
            pass
        layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
        layer.setLabelsEnabled(True)
    except Exception:
        pass
    layer.triggerRepaint()


def run_line_ends_snap(iface, project, target_layers, params):
    """每条线输出两个临时点：起点N、终点N，同号同色。圆点是头，方点是尾。"""
    cat = params.get('_category_target')
    created = []
    marked = 0
    for lyr in target_layers or []:
        if _layer_geom_class(lyr) != QgsWkbTypes.LineGeometry:
            continue
        pending = []
        n = 0
        for feat in iter_features(lyr, cat):
            geom = feat.geometry()
            head, tail = line_head_tail_xy(geom)
            if head is None or tail is None:
                continue
            n += 1
            color_hex = _line_end_color(n).name()
            pending.append((n, '起点', head, '起点%d' % n, feat.id(), color_hex))
            pending.append((n, '终点', tail, '终点%d' % n, feat.id(), color_hex))
        if not pending:
            continue
        authid = lyr.crs().authid() if lyr.crs().isValid() else ''
        uri = 'Point?crs=%s' % authid if authid else 'Point'
        name = _unique_project_layer_name(project, _tr('{0}_线头尾').format(lyr.name()))
        mem = QgsVectorLayer(uri, name, 'memory')
        if not mem.isValid():
            continue
        mem.dataProvider().addAttributes([
            QgsField('标记', qvariant_type("String")),
            QgsField('序号', qvariant_type("Int")),
            QgsField('端', qvariant_type("String")),
            QgsField('来源FID', qvariant_type("LongLong")),
            QgsField('颜色', qvariant_type("String")),
        ])
        mem.updateFields()
        feats = []
        for seq, end_name, pt, label, fid, color_hex in pending:
            f = QgsFeature(mem.fields())
            f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(pt)))
            f.setAttributes([label, seq, end_name, fid, color_hex])
            feats.append(f)
        mem.dataProvider().addFeatures(feats)
        mem.updateExtents()
        _style_line_end_points(mem, n)
        add_layer_to_output_tree(project, mem)
        created.append(mem.name())
        marked += n
    if not created:
        return {
            'ok': False,
            'error': _tr('没有可标注线头线尾的线'),
            'spatial_mode': '__special__',
        }
    return {
        'ok': True,
        'results': {'layers_created': created},
        'spatial_mode': '__special__',
        'summary_lines': [
            _tr('线头尾：标注 {0} 条线，临时点图层 {1} 个').format(marked, len(created)),
        ],
    }


def _iter_linestring_parts(geom):
    """从相交结果里只取出线部件。点相交、纯端点相接不会进入结果。"""
    if geom is None or geom.isEmpty():
        return
    try:
        gtype = QgsWkbTypes.geometryType(geom.wkbType())
    except Exception:
        return
    if gtype == QgsWkbTypes.LineGeometry:
        if QgsWkbTypes.isMultiType(geom.wkbType()):
            try:
                for sub in geom.asGeometryCollection():
                    for part in _iter_linestring_parts(sub):
                        yield part
            except Exception:
                return
        else:
            yield QgsGeometry(geom)
        return
    try:
        subs = geom.asGeometryCollection()
    except Exception:
        return
    for sub in subs or []:
        for part in _iter_linestring_parts(sub):
            yield part


def _as_2d_line(geom):
    """去掉高程/M，曲线打成折线，避免相交结果为空或长度被算成 0。"""
    g = QgsGeometry(geom)
    if g.isEmpty():
        return g
    try:
        if QgsWkbTypes.isCurvedType(g.wkbType()):
            seg = g.segmentize()
            if seg is not None and not seg.isEmpty():
                g = seg
    except Exception:
        pass
    try:
        ag = g.get()
        if ag is not None:
            if QgsWkbTypes.hasZ(g.wkbType()):
                ag.dropZValue()
            if QgsWkbTypes.hasM(g.wkbType()):
                ag.dropMValue()
    except Exception:
        pass
    return g


def _geom_length_m(geom, da):
    try:
        m = da.measureLength(geom)
        if m is not None and float(m) > 0:
            return float(m)
    except Exception:
        pass
    return _polyline_length_meters(geom, da)


def _line_chainage_segments(geom):
    """折线按相邻顶点拆段，附带沿线累计里程。"""
    out = []
    chain = 0.0
    for pts in _line_vertices_by_parts(geom):
        if len(pts) < 2:
            continue
        for k in range(len(pts) - 1):
            p0, p1 = pts[k], pts[k + 1]
            seg_len = _planar_pt_distance(p0, p1)
            if seg_len <= 0:
                continue
            out.append((p0, p1, chain, chain + seg_len, seg_len))
            chain += seg_len
    return out


def _pt_line_distance_xy(px, py, ax, ay, bx, by):
    dx = bx - ax
    dy = by - ay
    ll = dx * dx + dy * dy
    if ll <= 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / ll))
    qx = ax + t * dx
    qy = ay + t * dy
    return ((px - qx) ** 2 + (py - qy) ** 2) ** 0.5


def _project_scalar(px, py, ox, oy, ux, uy):
    return (px - ox) * ux + (py - oy) * uy


def _parallel_segment_overlap_on_a(p0, p1, a0, a1, tol):
    """两折线段是否有一段贴在一起走。分叉/十字交叉时方向不一致，直接否。"""
    ax, ay = p0.x(), p0.y()
    bx, by = p1.x(), p1.y()
    cx, cy = a0.x(), a0.y()
    dx, dy = a1.x(), a1.y()
    sdx = bx - ax
    sdy = by - ay
    slen = (sdx * sdx + sdy * sdy) ** 0.5
    tdx = dx - cx
    tdy = dy - cy
    tlen = (tdx * tdx + tdy * tdy) ** 0.5
    if slen <= 0 or tlen <= 0:
        return None
    ux, uy = sdx / slen, sdy / slen
    vx, vy = tdx / tlen, tdy / tlen
    if abs(ux * vx + uy * vy) < 0.966:  # 约 15° 内视为同向/反向共线
        return None
    if _pt_line_distance_xy(cx, cy, ax, ay, bx, by) > tol:
        return None
    if _pt_line_distance_xy(dx, dy, ax, ay, bx, by) > tol:
        return None
    t_vals = [
        _project_scalar(cx, cy, ax, ay, ux, uy),
        _project_scalar(dx, dy, ax, ay, ux, uy),
    ]
    lo = max(0.0, min(t_vals))
    hi = min(slen, max(t_vals))
    if hi - lo <= 0:
        return None
    return lo, hi


def _merge_chainage_intervals(intervals, gap=0.0):
    if not intervals:
        return []
    iv = sorted(intervals, key=lambda x: x[0])
    merged = [list(iv[0])]
    for lo, hi in iv[1:]:
        if lo <= merged[-1][1] + gap:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return [(a, b) for a, b in merged if b > a]


def _substring_by_chainage(geom, start_d, end_d):
    if end_d <= start_d:
        return None
    try:
        sub = geom.curveSubstring(start_d, end_d)
        if sub is not None and not sub.isEmpty():
            return sub
    except Exception:
        pass
    try:
        p0 = geom.interpolate(start_d).asPoint()
        p1 = geom.interpolate(end_d).asPoint()
        return QgsGeometry.fromPolylineXY([QgsPointXY(p0), QgsPointXY(p1)])
    except Exception:
        return None


def _parallel_line_overlap_intervals(g_ref, g_other, tol):
    """在 g_ref 上找与 g_other 平行且横向≤容差的重叠区间（里程）。"""
    segs_ref = _line_chainage_segments(g_ref)
    segs_other = _line_chainage_segments(g_other)
    if not segs_ref or not segs_other:
        return []
    hits = []
    for p0, p1, c0, c1, _ in segs_ref:
        for q0, q1, _d0, _d1, _ in segs_other:
            ov = _parallel_segment_overlap_on_a(p0, p1, q0, q1, tol)
            if ov is None:
                continue
            lo, hi = ov
            hits.append((c0 + lo, c0 + hi))
    return _merge_chainage_intervals(hits, gap=tol * 0.5 if tol > 0 else 0.0)


def _overlap_midpoint(line_geom):
    try:
        length = float(line_geom.length())
    except Exception:
        length = 0.0
    if length > 0:
        try:
            mid = line_geom.interpolate(length * 0.5)
            if mid is not None and not mid.isEmpty() and mid.type() == QgsWkbTypes.PointGeometry:
                return mid
        except Exception:
            pass
    try:
        c = line_geom.centroid()
        if c is not None and not c.isEmpty():
            return c
    except Exception:
        pass
    return None


def run_line_overlap_centers_snap(iface, project, target_layers, params):
    """线图层：端点相接、交叉成点不算重叠。两线有一段重合（含同起点同向只叠很短）时，
    在重叠段中心输出临时点。多条线叠在同一段上合并成一个点。"""
    show_m = params.get('_show_messages', True)
    mw = iface.mainWindow() if iface else None
    try:
        min_len_m = float(params.get('_line_overlap_min_length', 1.0))
    except (TypeError, ValueError):
        min_len_m = 1.0
    if min_len_m < 0:
        min_len_m = 0.0
    tol = float(params.get('tolerance', 0) or 0)
    if tol < 0:
        tol = 0.0

    line_layers = [lyr for lyr in (target_layers or []) if _layer_geom_class(lyr) == QgsWkbTypes.LineGeometry]
    if not line_layers:
        err = _tr('【线】两线重叠段：请选择线图层')
        if show_m and mw:
            QMessageBox.warning(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__'}

    base_crs = line_layers[0].crs()
    ctx = project.transformContext()
    da = QgsDistanceArea()
    da.setSourceCrs(base_crs, ctx)
    try:
        da.setEllipsoid(base_crs.ellipsoidAcronym())
    except Exception:
        pass

    geoms, meta = _gather_lines_workspace(
        line_layers, base_crs, project, params.get('_category_target')
    )
    keys = sorted(geoms.keys())
    if len(keys) < 2:
        err = _tr('【线】两线重叠段：至少需要两条线')
        if show_m and mw:
            QMessageBox.warning(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__'}

    for i in keys:
        geoms[i] = _as_2d_line(geoms[i])

    index = QgsSpatialIndex()
    for i in keys:
        stub = QgsFeature()
        stub.setId(int(i) + 1)
        stub.setGeometry(geoms[i])
        index.addFeature(stub)

    pieces = []
    eff_tol = tol if tol > 0 else 1e-9
    for i in keys:
        g1 = geoms[i]
        lyr1, fid1 = meta[i]
        try:
            rect = QgsRectangle(g1.boundingBox())
            if eff_tol > 0:
                rect.grow(eff_tol)
        except Exception:
            continue
        for jid in index.intersects(rect):
            j = int(jid) - 1
            if j <= i or j not in geoms:
                continue
            lyr2, fid2 = meta[j]
            if lyr2.id() == lyr1.id() and fid2 == fid1:
                continue
            g2 = geoms[j]
            for c0, c1 in _parallel_line_overlap_intervals(g1, g2, eff_tol):
                sub = _substring_by_chainage(g1, c0, c1)
                if sub is None:
                    continue
                length_m = _geom_length_m(sub, da)
                if length_m is None or length_m < min_len_m:
                    continue
                pieces.append(sub)
            for c0, c1 in _parallel_line_overlap_intervals(g2, g1, eff_tol):
                sub = _substring_by_chainage(g2, c0, c1)
                if sub is None:
                    continue
                length_m = _geom_length_m(sub, da)
                if length_m is None or length_m < min_len_m:
                    continue
                pieces.append(sub)

    merged_parts = []
    if pieces:
        try:
            merged = QgsGeometry.unaryUnion(pieces)
        except Exception:
            merged = None
        src = merged if merged is not None and not merged.isEmpty() else None
        if src is None:
            walk = pieces
        else:
            walk = list(_iter_linestring_parts(src)) or pieces
        seen_xy = []
        for part in walk:
            length_m = _geom_length_m(part, da)
            if length_m is None or length_m < min_len_m:
                continue
            mid = _overlap_midpoint(part)
            if mid is None or mid.isEmpty():
                continue
            try:
                pt = mid.asPoint()
            except Exception:
                continue
            if any(_planar_pt_distance(pt, old) <= 1e-6 for old in seen_xy):
                continue
            seen_xy.append(QgsPointXY(pt))
            merged_parts.append((QgsGeometry.fromPointXY(QgsPointXY(pt)), float(length_m)))

    if not merged_parts:
        return {
            'ok': True,
            'results': {'layers_created': []},
            'spatial_mode': '__special__',
            'summary_lines': [_tr('【线】两线重叠段：没有线段重合，未输出点')],
        }

    authid = base_crs.authid() if base_crs.isValid() else ''
    uri = 'Point?crs=%s' % authid if authid else 'Point'
    tag = (params.get('_output_tag') or '').strip()
    base_name = _tr('线重叠中心') if not tag else _tr('线重叠中心_{0}').format(tag)
    name = _unique_project_layer_name(project, base_name)
    mem = QgsVectorLayer(uri, name, 'memory')
    if not mem.isValid():
        err = _tr('无法创建线重叠中心点图层')
        if show_m and mw:
            QMessageBox.warning(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__'}
    mem.dataProvider().addAttributes([
        QgsField('序号', qvariant_type("Int")),
        QgsField('重叠长_m', qvariant_type("Double")),
    ])
    mem.updateFields()
    out_feats = []
    for n, (pt_geom, length_m) in enumerate(merged_parts, start=1):
        f = QgsFeature(mem.fields())
        f.setGeometry(pt_geom)
        f.setAttributes([n, length_m])
        out_feats.append(f)
    mem.dataProvider().addFeatures(out_feats)
    mem.updateExtents()
    apply_memory_output_style(mem)
    add_layer_to_output_tree(project, mem)
    return {
        'ok': True,
        'results': {'layers_created': [mem.name()]},
        'spatial_mode': '__special__',
        'summary_lines': [
            _tr('【线】两线重叠段：输出 {0} 个重叠段中心点').format(len(merged_parts)),
        ],
    }


def _tips(*lines):
    return '\n'.join(str(x) for x in lines if x)


SPECIAL_MODE_INFO = OrderedDict([
    ('polygon_inspect', (
        '【面】重叠 / 孔洞 / 空隙检查',
        (
            '判断图层：面。不需要参考图层。',
            '一次找出：面与面重叠的部分、面中间的孔洞、面与面之间的空隙（缝）。',
            '小于「面积阈值」的重叠、孔洞、空隙忽略不计。',
            '输出哪些图层，在右侧「面检测输出」清单里勾选。',
            '「提取已吸附」只影响「参与重叠的面要素」和「重叠相关面质心」：勾选输出有重叠的面，不勾选输出没有重叠的面。',
        ),
    )),
    ('poly_point_count', (
        '【计数】面内有几个点（含边界）',
        (
            '判断图层：面；参考图层：点。',
            '统计每个面内部或边界上有几个参考点，再按「个数规则」筛选面。',
            '按坐标精确判断，不使用容差。',
            '用途：找没有门牌点的地块（个数 = 0），或点多于一个的地块。',
        ),
    )),
    ('poly_line_count', (
        '【计数】与面相交的线有几条',
        (
            '判断图层：面；参考图层：线。',
            '统计与每个面有接触的参考线条数（穿过、在面内、只碰到边界都算），再按「个数规则」筛选面。',
            '按坐标精确判断，不使用容差。',
        ),
    )),
    ('line_length', (
        '【筛选】按线长度筛选（米）',
        (
            '判断图层：线。不需要参考图层。',
            '按椭球计算每条线的实际长度（米），与「线长规则」比较。',
            '勾选「提取已吸附」输出满足规则的线，不勾选输出不满足的线。',
            '用途：找过短的碎线、超长的异常线。',
        ),
    )),
    ('line_ends', (
        '【标注】标出每条线的起点和终点',
        (
            '判断图层：线。不需要参考图层。',
            '每条线输出两个临时点：「起点N」「终点N」，同一条线同一颜色。',
            '圆点是起点（线头），方点是终点（线尾），用来检查线的绘制方向。',
        ),
    )),
    ('line_overlap_pt', (
        '【线】两线重叠段，输出中心点',
        (
            '判断图层：线。不需要参考图层。',
            '两条线有一段贴在一起走（方向夹角 ≤ 15°，横向距离 ≤ 吸附容差），就在重叠段中间输出一个点。',
            '端点相接、十字交叉、从一个节点往各方向分叉都不算；两线顶点不必对齐。',
            '重叠长度小于「最短重叠」的忽略；多条线叠在同一段上只输出一个点。',
        ),
    )),
    ('line_point_count', (
        '【计数】线上挂了几个点',
        (
            '判断图层：线；参考图层：点。',
            '按「挂接位置」统计每条线上有几个参考点（端点 / 任意折点 / 沿线身，距离 ≤ 容差），再按「个数规则」筛选线。',
            '用途：找两端没有节点的线（端点，个数 < 2）。',
        ),
    )),
    ('point_line_chain', (
        '【拓扑】从点出发的连续线段数（≥N）',
        (
            '判断图层：点；参考图层：线。只用线的两个端点建立连接关系。',
            '从每个判断点出发，沿每个方向顺着线走：经过「只连两条线」的普通节点继续走，遇到分叉或另一个判断点就停。',
            '数一路走过的线段条数，取各方向中最多的一个，与 N 比较。',
            '勾选「提取已吸附」：输出段数 ≥ N 的点和那条链上的线；不勾选：输出段数 < N 的点和它直接连着的线。',
            '用途：两个设备点之间最多只能串几段线之类的检查。',
        ),
    )),
    ('point_line_count', (
        '【计数】点上接了几条线',
        (
            '判断图层：点；参考图层：线。',
            '按「挂接位置」统计每个点接了几条参考线（端点 / 任意折点 / 沿线身，距离 ≤ 容差），再按「个数规则」筛选点。',
            '用途：找孤立节点（个数 = 0）、只接一条线的末端点（个数 = 1）。',
        ),
    )),
    ('line_dangles', (
        '【拓扑】悬挂端点（线头没接上）',
        (
            '判断图层：线。不需要参考图层。',
            '线的起点或终点在吸附容差内碰不到任何别的线（端点或线身都算接上），就输出这个端点。',
            '闭合线的首尾、多部件线的其它部件、绕回本线线身的端点都算接上。',
            '用途：找没接到路网上的断头线、画短了/画过了的线头。',
            '输出点图层（图层、来源FID、起点/终点），「提取已吸附」不起作用。',
        ),
    )),
    ('line_cross_nonode', (
        '【拓扑】两线交叉但没打断（交点缺节点）',
        (
            '判断图层：线。不需要参考图层。',
            '求两条线的交点；交点在吸附容差内找不到某条线的顶点，就说明这条线在交点处没打断。',
            '线头搭在另一条线身上（T 形）而那条线没有节点，也会报出来。',
            '两线重叠走的一段不在这里检查，请用「【线】两线重叠段」。',
            '输出交点（图层1/FID1/图层2/FID2/缺节点的是哪条），「提取已吸附」不起作用。',
        ),
    )),
    ('geom_validity', (
        '【质检】无效几何（自相交 / 空几何 等）',
        (
            '判断图层：点 / 线 / 面。不需要参考图层。',
            '用 GEOS 检查几何有效性：面自相交、环方向/嵌套错误、重复点导致的无效等；另外检查空几何、长度或面积为 0、线自相交。',
            '可选：把多部件要素也当问题报出。',
            '勾选「提取已吸附」：输出有问题的要素（附 CDET_问题 字段）；不勾选：输出没问题的要素。',
            '能定位到的问题另外输出「无效几何位置」点图层。',
        ),
    )),
    ('poly_area', (
        '【筛选】按面积筛选（平方米）',
        (
            '判断图层：面。不需要参考图层。',
            '按椭球计算每个面的实际面积（平方米），与「面积规则」比较。',
            '勾选「提取已吸附」输出满足规则的面，不勾选输出不满足的面；输出附「面积_m2」字段。',
            '用途：找碎面、面积异常大的面。',
        ),
    )),
    ('vertex_quality', (
        '【质检】尖角 / 回头线 / 过密顶点',
        (
            '判断图层：线 / 面。不需要参考图层。',
            '尖角：某个顶点前后两段的夹角小于「尖角阈值」（度）；夹角小于 1° 标为「回头线」（线走过去又折回来）。阈值设 0 不查尖角。',
            '过密顶点：相邻两个顶点的距离小于「最小间距」（米）；距离为 0 标为「重复顶点」（总会检查）。',
            '输出问题点（图层、来源FID、问题、角度_度、间距_m），「提取已吸附」不起作用。',
        ),
    )),
    ('point_near', (
        '【距离】点与点过近',
        (
            '判断图层：点。不需要参考图层（所选点图层之间、图层内部互相比较）。',
            '某个点在「过近距离」（米）内还有别的点，就算过近。',
            '默认不算吸附容差内的点（那属于重复点，请用「【重复】完全重复的要素」）；勾选「容差内也算」则一并算上。',
            '勾选「提取已吸附」：输出过近的点（附最近距离、最近图层、最近FID）；不勾选：输出周围没有近邻的点。',
        ),
    )),
    ('overlap_grp', (
        '【重复】完全重复的要素（坐标一致）',
        (
            '判断图层：点 / 线 / 面。不需要参考图层。',
            '点：两点距离 ≤ 容差。线：顶点个数相同，且逐个顶点在容差内对得上（方向相反也算）。',
            '面：每个环的顶点逐个对得上（起点不同、方向相反也算）。',
            '注意：只是部分重叠的不算重复；面与面的面积重叠请用「【面】重叠 / 孔洞 / 空隙检查」。',
            '固定输出重复的要素，「提取已吸附」不起作用。',
        ),
    )),
])


def special_mode_label_source(key):
    """Chinese source title; used for category ranking (language-stable 【类别】)."""
    info = SPECIAL_MODE_INFO.get(key)
    return info[0] if info else str(key or '')


def special_mode_label(key):
    info = SPECIAL_MODE_INFO.get(key)
    return _tr(info[0]) if info else str(key or '')


def special_mode_tip(key):
    info = SPECIAL_MODE_INFO.get(key)
    if not info:
        return ''
    tip = info[1]
    if isinstance(tip, (list, tuple)):
        return _tips(*(_tr(x) for x in tip if x))
    return _tr(tip) if tip else ''


QUALITY_KEYS = ('line_dangles', 'line_cross_nonode', 'geom_validity', 'poly_area', 'vertex_quality', 'point_near')

SPECIAL_KEYS_NO_REF = frozenset({
    'polygon_inspect', 'line_length', 'line_ends', 'overlap_grp', 'line_overlap_pt',
} | set(QUALITY_KEYS))
SPECIAL_KEYS = frozenset({
    'polygon_inspect',
    'line_length',
    'line_ends',
    'line_overlap_pt',
    'overlap_grp',
    'point_line_chain',
    'point_line_count',
    'line_point_count',
    'poly_point_count',
    'poly_line_count',
} | set(QUALITY_KEYS))

_P, _L, _G = 'point', 'line', 'polygon'
SPECIAL_TARGET_GEOMS = {
    'polygon_inspect': (_G,),
    'poly_point_count': (_G,),
    'poly_line_count': (_G,),
    'poly_area': (_G,),
    'line_length': (_L,),
    'line_ends': (_L,),
    'line_overlap_pt': (_L,),
    'line_point_count': (_L,),
    'line_dangles': (_L,),
    'line_cross_nonode': (_L,),
    'vertex_quality': (_L, _G),
    'point_line_chain': (_P,),
    'point_line_count': (_P,),
    'point_near': (_P,),
    'overlap_grp': (_P, _L, _G),
    'geom_validity': (_P, _L, _G),
}
SPECIAL_REF_GEOM = {
    'poly_point_count': _P,
    'poly_line_count': _L,
    'line_point_count': _P,
    'point_line_chain': _L,
    'point_line_count': _L,
}
SPECIAL_KEYS_NO_SNAP_FILTER = frozenset({
    'line_ends', 'line_overlap_pt', 'overlap_grp', 'line_dangles', 'line_cross_nonode', 'vertex_quality',
})
SPECIAL_EXTRA_DEFAULTS = OrderedDict([
    ('_poly_area_rule', {'kind': 'le', 'threshold': 0.0}),
    ('_spike_angle', 10.0),
    ('_dense_min_dist', 0.05),
    ('_near_dist_m', 1.0),
    ('_near_include_same', False),
    ('_validity_multipart', False),
])


def special_modes_for_geom(geom_name):
    """按 SPECIAL_MODE_INFO 的顺序列出支持该几何类型（'point'/'line'/'polygon'）的特殊检测。"""
    return [k for k in SPECIAL_MODE_INFO if geom_name in SPECIAL_TARGET_GEOMS.get(k, ())]


def _cluster_union_find(points, tol, judgment_anchor_count=0):
    """points: list of QgsPointXY。返回每个点所属簇编号 list[int]，簇号已压缩为 0..k-1。
    judgment_anchor_count：前若干个索引为判断图层上的点；其后为线端点索引。
    若 >0，在常规距离聚类之后，将「落在任一判断点容差内的每个线端点」并入距离最近的判断点索引簇。
    用于消除 Hub 处判断点坐标与线端点因浮点/数字化微小偏差分裂成多簇，从而产生多出关联方向或偏大深度的问题。"""
    n = len(points)
    if n == 0:
        return []
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(n):
        for j in range(i + 1, n):
            if _planar_pt_distance(points[i], points[j]) <= tol:
                union(i, j)

    jac = int(judgment_anchor_count) if judgment_anchor_count else 0
    if jac > 0:
        jac = min(jac, n)
        for i in range(jac, n):
            best_j = -1
            best_d = None
            for j in range(jac):
                d = _planar_pt_distance(points[i], points[j])
                if d <= tol and (best_d is None or d < best_d):
                    best_d = d
                    best_j = j
            if best_j >= 0:
                union(i, best_j)

    root_to_c = {}
    cid_list = []
    nxt = 0
    for i in range(n):
        r = find(i)
        if r not in root_to_c:
            root_to_c[r] = nxt
            nxt += 1
        cid_list.append(root_to_c[r])
    return cid_list


def _edge_key(lyr, fid, part_idx):
    return (lyr.id(), int(fid), int(part_idx))


def _walk_chain_from(adj, ui, vn):
    """从节点 ui 沿邻接 vn 走出第一步，遇分叉（degree≠2）停止。返回 (段数, edge_key 集合)。"""
    ek0 = None
    for v2, ek in adj[ui]:
        if v2 == vn:
            ek0 = ek
            break
    if ek0 is None:
        return 0, set()
    edges = {ek0}
    count = 1
    prev, cur = ui, vn
    while True:
        opts = [(v, e) for v, e in adj[cur] if v != prev]
        if len(opts) != 1:
            break
        nxt, ek = opts[0]
        edges.add(ek)
        count += 1
        prev, cur = cur, nxt
    return count, edges


def _cluster_unique_neighbors(c, adj):
    return {nb for nb, _ in adj[c]}


def _judgment_cluster_is_endpoint_leaf(c, adj, judgment_clusters):
    """判断点簇若在线段拓扑上仅连接一个邻簇，视为链端（叶），进入该簇的边可计入深度。"""
    if c not in judgment_clusters:
        return False
    return len(_cluster_unique_neighbors(c, adj)) <= 1


def _walk_chain_from_judgment(adj, ui, vn, start_cluster, judgment_clusters):
    """
    与 _walk_chain_from 类似，但在「进入另一处判断点簇」时：
    - 若该簇为链端叶（唯一邻接簇）：计入进入该簇的边并结束（最长分支末端的判断点）；
    - 否则：不计量进入该簇的边并结束（路径中途的其他判断点，避免从链尾往回把整条链算进深度）。
    这样「深度」表示相邻判断点之间的链段长度习惯，而非图上任意两点间的最长路径。
    """
    ek0 = None
    for v2, ek in adj[ui]:
        if v2 == vn:
            ek0 = ek
            break
    if ek0 is None:
        return 0, set()

    edges = set()
    count = 0
    prev, cur, ek = ui, vn, ek0

    while True:
        if cur in judgment_clusters and cur != start_cluster:
            if _judgment_cluster_is_endpoint_leaf(cur, adj, judgment_clusters):
                edges.add(ek)
                count += 1
                break
            break
        edges.add(ek)
        count += 1
        opts = [(v2, e) for v2, e in adj[cur] if v2 != prev]
        if len(opts) != 1:
            break
        prev, cur = cur, opts[0][0]
        ek = opts[0][1]
    return count, edges


def run_point_line_chain_snap(iface, project, target_layers, ref_layers, params):
    """
    判断图层：点（可多图层）；参考图层：线（可多图层）。
    仅以线的两端点参与拓扑；参数仅「最小段数」阈值为大于等于语义；
    聚类时对折线串先去重点，并对线端点做「最近判断点」锚定合并（见 _cluster_union_find），减轻 Hub 处多簇分裂导致的偏多分支/偏大深度。
    深度按相邻判断点簇之间的链段计量：进入「另一判断点」所在簇时，仅当该簇为链端叶（唯一邻接簇）
    才计入进入边；否则在该簇前停止，避免从链尾沿整条线往回累计导致与「关联线数」不一致。
    snap_enabled True：输出 max 方向段数 ≥ 阈值的点及对应命中方向的线段；
    False：输出 max 段数 < 阈值的点及其处的接线（仅与该点相连的线段）。
    同一容差簇内多个点要素只保留一处输出。
    """
    tol = float(params.get('tolerance', 0.000001))
    thr = int(params.get('_point_line_chain_min_seg', 1))
    thr = max(1, thr)
    snap_enabled = bool(params.get('snap_enabled', True))
    show_m = params.get('_show_messages', True)
    mw = iface.mainWindow() if iface else None

    if not target_layers:
        err = _tr('未选择判断图层')
        if show_m and mw:
            QMessageBox.warning(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__'}
    if not ref_layers:
        err = _tr('【拓扑】从点出发的连续线段数：请选择参考线图层')
        if show_m and mw:
            QMessageBox.warning(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__'}
    for lyr in target_layers:
        if _layer_geom_class(lyr) != QgsWkbTypes.PointGeometry:
            err = _tr('【拓扑】从点出发的连续线段数：判断图层须为点图层')
            if show_m and mw:
                QMessageBox.warning(mw, _tr('提示'), err)
            return {'ok': False, 'error': err, 'spatial_mode': '__special__'}
    for lyr in ref_layers:
        if _layer_geom_class(lyr) != QgsWkbTypes.LineGeometry:
            err = _tr('【拓扑】从点出发的连续线段数：参考图层须为线图层')
            if show_m and mw:
                QMessageBox.warning(mw, _tr('提示'), err)
            return {'ok': False, 'error': err, 'spatial_mode': '__special__'}

    base_crs = target_layers[0].crs()
    xf_cache = {}

    def _xf(lyr):
        if lyr.crs() == base_crs:
            return None
        k = lyr.crs().authid()
        if k not in xf_cache:
            xf_cache[k] = QgsCoordinateTransform(lyr.crs(), base_crs, project)
        return xf_cache[k]

    raw_points = []
    jp_meta = []
    line_end_refs = []

    for lyr in target_layers:
        xf = _xf(lyr)
        for f in iter_features(lyr, params.get('_category_target')):
            g = QgsGeometry(f.geometry())
            if g.isEmpty():
                continue
            if xf:
                try:
                    g.transform(xf)
                except Exception:
                    continue
            if g.type() != QgsWkbTypes.PointGeometry:
                continue
            pts = g.asMultiPoint() if g.isMultipart() else [g.asPoint()]
            for pq in pts:
                raw_points.append(QgsPointXY(pq))
                jp_meta.append((lyr, int(f.id())))

    part_idx = 0
    for lyr in ref_layers:
        xf = _xf(lyr)
        for f in iter_features(lyr, params.get('_category_ref')):
            g = QgsGeometry(f.geometry())
            if g.isEmpty():
                continue
            if xf:
                try:
                    g.transform(xf)
                except Exception:
                    continue
            if g.type() != QgsWkbTypes.LineGeometry:
                continue
            try:
                if g.isMultipart():
                    for pl in g.asMultiPolyline():
                        pl = _dedupe_consecutive_polyline(pl, tol)
                        if len(pl) < 2:
                            continue
                        i0 = len(raw_points)
                        raw_points.append(QgsPointXY(pl[0]))
                        i1 = len(raw_points)
                        raw_points.append(QgsPointXY(pl[-1]))
                        line_end_refs.append((i0, i1, lyr, int(f.id()), part_idx))
                        part_idx += 1
                else:
                    pl = g.asPolyline()
                    pl = _dedupe_consecutive_polyline(pl, tol)
                    if len(pl) < 2:
                        continue
                    i0 = len(raw_points)
                    raw_points.append(QgsPointXY(pl[0]))
                    i1 = len(raw_points)
                    raw_points.append(QgsPointXY(pl[-1]))
                    line_end_refs.append((i0, i1, lyr, int(f.id()), 0))
            except Exception:
                continue

    if not raw_points:
        err = _tr('无有效点或线端点')
        if show_m and mw:
            QMessageBox.warning(mw, _tr('提示'), err)
        return {'ok': False, 'error': err, 'spatial_mode': '__special__'}

    njp = len(jp_meta)
    cid = _cluster_union_find(raw_points, tol, judgment_anchor_count=njp)
    adj = defaultdict(list)
    for i0, i1, lyr, fid, pidx in line_end_refs:
        u, v = cid[i0], cid[i1]
        ek = _edge_key(lyr, fid, pidx)
        adj[u].append((v, ek))
        adj[v].append((u, ek))

    judgment_clusters = frozenset({cid[i] for i in range(njp)})

    def cluster_stats(c_node):
        if c_node not in adj:
            return 0, set(), set()
        best_m = 0
        hit_edges = set()
        seen_nb = set()
        for nb, _ in adj[c_node]:
            if nb in seen_nb:
                continue
            seen_nb.add(nb)
            cnt, eds = _walk_chain_from_judgment(
                adj, c_node, nb, c_node, judgment_clusters
            )
            best_m = max(best_m, cnt)
            if cnt >= thr:
                hit_edges |= eds
        inc_edges = {ek for nb, ek in adj[c_node]}
        return best_m, hit_edges, inc_edges

    jp_clusters = {cid[i] for i in range(njp)}
    c_metrics = {}
    c_hit_edges = {}
    c_inc_edges = {}
    for cn in jp_clusters:
        m, he, inc = cluster_stats(cn)
        c_metrics[cn] = m
        c_hit_edges[cn] = he
        c_inc_edges[cn] = inc

    want_pts = []
    line_keys_acc = set()
    clusters_out = set()
    for ji in range(njp):
        cn = cid[ji]
        m = c_metrics[cn]
        pick = (m >= thr) if snap_enabled else (m < thr)
        if not pick:
            continue
        if cn in clusters_out:
            continue
        clusters_out.add(cn)
        want_pts.append(jp_meta[ji])
        if snap_enabled:
            line_keys_acc |= c_hit_edges[cn]
        else:
            line_keys_acc |= c_inc_edges[cn]

    layers_created = []
    crs_auth = base_crs.authid()
    layer_by_id = {lyr.id(): lyr for lyr in ref_layers}

    seen_pt = set()
    out_pts_layer_name = None
    if want_pts:
        tmpl_lyr = want_pts[0][0]
        primary_name = target_layers[0].name()
        if len(target_layers) > 1:
            primary_name = _tr('{0}_等{1}判断层').format(primary_name, len(target_layers))
        base_pts = _snap_memory_output_basename(primary_name, params, snap_enabled)
        uniq = _unique_project_layer_name(project, _tr('{0}_点线链点').format(base_pts))
        lyr_mem = QgsVectorLayer(f'Point?crs={crs_auth}', uniq, 'memory')
        prv = lyr_mem.dataProvider()
        prv.addAttributes(tmpl_lyr.fields().toList())
        lyr_mem.updateFields()
        for lyr_src, fid in want_pts:
            k = (lyr_src.id(), fid)
            if k in seen_pt:
                continue
            seen_pt.add(k)
            rf = lyr_src.getFeature(fid)
            if not rf.hasGeometry():
                continue
            gg = QgsGeometry(rf.geometry())
            xf_pt = _xf(lyr_src)
            if xf_pt:
                try:
                    gg.transform(xf_pt)
                except Exception:
                    continue
            ox = QgsFeature(lyr_mem.fields())
            al = list(rf.attributes())[: lyr_mem.fields().count()]
            while len(al) < lyr_mem.fields().count():
                al.append(None)
            ox.setAttributes(al)
            ox.setGeometry(gg)
            prv.addFeature(ox)
        apply_memory_output_style(lyr_mem)
        add_layer_to_output_tree(project, lyr_mem)
        layers_created.append(lyr_mem.name())
        out_pts_layer_name = lyr_mem.name()

    by_lyr_pick = defaultdict(set)
    for ek in line_keys_acc:
        lid, fid, pidx = ek
        lyr_o = layer_by_id.get(lid)
        if lyr_o:
            by_lyr_pick[lyr_o].add((fid, pidx))

    for lyr_src, pair_set in by_lyr_pick.items():
        base_ln = _snap_memory_output_basename(lyr_src.name(), params, snap_enabled)
        uniq = _unique_project_layer_name(project, _tr('{0}_点线链线').format(base_ln))
        nf = QgsVectorLayer(f'LineString?crs={crs_auth}', uniq, 'memory')
        prv = nf.dataProvider()
        prv.addAttributes(lyr_src.fields().toList())
        nf.updateFields()
        n_feat = 0
        for fid, pidx in pair_set:
            rf = lyr_src.getFeature(fid)
            if not rf.hasGeometry():
                continue
            g0 = QgsGeometry(rf.geometry())
            xf_ln = _xf(lyr_src)
            if xf_ln:
                try:
                    g0.transform(xf_ln)
                except Exception:
                    continue
            try:
                if g0.isMultipart():
                    mp = g0.asMultiPolyline()
                    if pidx < 0 or pidx >= len(mp) or len(mp[pidx]) < 2:
                        continue
                    seg = QgsGeometry.fromPolylineXY(mp[pidx])
                else:
                    if pidx != 0:
                        continue
                    seg = QgsGeometry(g0)
            except Exception:
                continue
            if seg.isEmpty():
                continue
            ox = QgsFeature(nf.fields())
            al = list(rf.attributes())[: nf.fields().count()]
            while len(al) < nf.fields().count():
                al.append(None)
            ox.setAttributes(al)
            ox.setGeometry(seg)
            if prv.addFeature(ox):
                n_feat += 1
        if n_feat == 0:
            continue
        apply_memory_output_style(nf)
        add_layer_to_output_tree(project, nf)
        layers_created.append(nf.name())

    summary_lines = [
        _tr('【拓扑】从点出发的连续线段数：阈值≥{0} 段；输出点数：{1}；线段键数：{2}；临时图层数：{3}').format(
            thr,
            len(seen_pt),
            len(line_keys_acc),
            len(layers_created),
        ),
    ]
    return {
        'ok': True,
        'results': {'layers_created': layers_created},
        'spatial_mode': '__special__',
        'summary_lines': summary_lines,
    }


def dispatch_snap_special(iface, project, snap_key, target_layers, ref_layers, params):
    if snap_key == 'polygon_inspect':
        return run_polygon_snap_branch(iface, project, target_layers, params)
    if snap_key == 'line_length':
        return run_line_length_snap(iface, project, target_layers, params)
    if snap_key == 'line_ends':
        return run_line_ends_snap(iface, project, target_layers, params)
    if snap_key == 'line_overlap_pt':
        return run_line_overlap_centers_snap(iface, project, target_layers, params)
    if snap_key == 'overlap_grp':
        return run_overlap_snap(iface, project, target_layers, params)
    if snap_key == 'point_line_chain':
        return run_point_line_chain_snap(iface, project, target_layers, ref_layers, params)
    if snap_key == 'point_line_count':
        return run_point_line_count_snap(iface, project, target_layers, ref_layers, params)
    if snap_key == 'line_point_count':
        return run_line_point_count_snap(iface, project, target_layers, ref_layers, params)
    if snap_key == 'poly_point_count':
        return run_polygon_point_count_snap(iface, project, target_layers, ref_layers, params)
    if snap_key == 'poly_line_count':
        return run_polygon_line_count_snap(iface, project, target_layers, ref_layers, params)
    if snap_key in QUALITY_KEYS:
        try:
            from .cdet_snap_quality import QUALITY_RUNNERS
        except ImportError:
            from cdet_snap_quality import QUALITY_RUNNERS
        return QUALITY_RUNNERS[snap_key](iface, project, target_layers, ref_layers, params)
    err = _tr('未知模式')
    if params.get('_show_messages', True) and iface:
        QMessageBox.warning(iface.mainWindow(), _tr('提示'), err)
    return {'ok': False, 'error': err, 'spatial_mode': '__special__'}
