# -*- coding: utf-8 -*-
import time

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QProgressDialog
from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsProject,
    QgsWkbTypes,
    QgsCoordinateTransform,
)

try:
    from .cdet_field_naming import (
        _build_ref_state,
        _mode_ok,
        _rect_grow,
        _layer_geom_class,
        spatial_mode_choices,
        AGGREGATE_LINE_POINT_MODES,
        line_point_aggregate_ok,
        count_aggregate_line_point_matches,
        ref_point_geoms_from_candidates,
        PP_KTH_NEAREST_MODE,
        mode_param_value,
        _pp_kth_nearest_pick,
    )
except ImportError:
    from cdet_field_naming import (
        _build_ref_state,
        _mode_ok,
        _rect_grow,
        _layer_geom_class,
        spatial_mode_choices,
        AGGREGATE_LINE_POINT_MODES,
        line_point_aggregate_ok,
        count_aggregate_line_point_matches,
        ref_point_geoms_from_candidates,
        PP_KTH_NEAREST_MODE,
        mode_param_value,
        _pp_kth_nearest_pick,
    )
try:
    from .cdet_category import iter_features
except ImportError:
    from cdet_category import iter_features

try:
    from .cdet_memory_style import apply_memory_output_style
except ImportError:
    from cdet_memory_style import apply_memory_output_style

try:
    from .cdet_output_tree import add_layer_to_output_tree
except ImportError:
    from cdet_output_tree import add_layer_to_output_tree

try:
    from .cdet_snap_special import SPECIAL_KEYS, dispatch_snap_special
except ImportError:
    from cdet_snap_special import SPECIAL_KEYS, dispatch_snap_special
from .i18n import tr as _i18n_tr
from .qtutil import AppMessageBox as QMessageBox
from .errors import (
    CANCELLED as ERR_CANCELLED,
    GEOM_MISMATCH as ERR_GEOM_MISMATCH,
    INVALID_MODE as ERR_INVALID_MODE,
    NO_REF_FEATURES as ERR_NO_REF_FEATURES,
    NO_REF_LAYER as ERR_NO_REF_LAYER,
    NO_TARGET_FEATURES as ERR_NO_TARGET_FEATURES,
    NO_TARGET_LAYER as ERR_NO_TARGET_LAYER,
)


class CDETCore:
    SEGMENT_OUTPUT_LINE_MODES = frozenset({
        'll_adjacent_seg_any',
        'll_adjacent_seg_all',
        'll_adjacent_seg_ratio',
        'll_adjacent_seg_any_and_near',
    })

    def __init__(self, iface):
        self.iface = iface
        self.project = QgsProject.instance()
        self.ref_feature_count = 0
        self.crs_warnings = []

    def tr(self, text):
        if getattr(self, '_i18n_raw', False):
            return text
        return _i18n_tr(text)

    @staticmethod
    def _mode_name_for_layer(mode):
        mp = {
            'll_adjacent_seg_any': '任一段匹配',
            'll_adjacent_seg_all': '全部段匹配',
            'll_adjacent_seg_ratio': '段长占比',
            'll_adjacent_seg_any_and_near': '任一段且近距',
        }
        if mode in mp:
            return _i18n_tr(mp[mode])
        if not mode:
            return _i18n_tr('模式')
        return str(mode)

    @staticmethod
    def _line_segments_xy(line_geom):
        if line_geom.isEmpty() or line_geom.type() != QgsWkbTypes.LineGeometry:
            return []
        out = []
        parts = line_geom.asMultiPolyline() if line_geom.isMultipart() else [line_geom.asPolyline()]
        for part in parts:
            if len(part) < 2:
                continue
            for i in range(len(part) - 1):
                out.append((part[i], part[i + 1]))
        return out

    @staticmethod
    def _segment_pair_match(a1, a2, b1, b2, tol):
        da1 = QgsGeometry.fromPointXY(a1)
        da2 = QgsGeometry.fromPointXY(a2)
        db1 = QgsGeometry.fromPointXY(b1)
        db2 = QgsGeometry.fromPointXY(b2)
        d11 = da1.distance(db1)
        d22 = da2.distance(db2)
        if d11 <= tol and d22 <= tol:
            return True
        d12 = da1.distance(db2)
        d21 = da2.distance(db1)
        return d12 <= tol and d21 <= tol

    def _line_segment_match_flags(self, tg_line, ref_entries, ref_idx, tol, exclude_ref_layer_id=None, exclude_ref_fid=None):
        segs = self._line_segments_xy(tg_line)
        if not segs:
            return []
        flags = []
        for a1, a2 in segs:
            gseg = QgsGeometry.fromPolylineXY([a1, a2])
            rect = _rect_grow(gseg.boundingBox(), tol)
            cand_ids = list(ref_idx.intersects(rect))
            matched = False
            for cid in cand_ids:
                if cid < 0 or cid >= len(ref_entries):
                    continue
                e = ref_entries[cid]
                if exclude_ref_layer_id is not None and exclude_ref_fid is not None:
                    if e['layer'].id() == exclude_ref_layer_id and int(e['fid']) == int(exclude_ref_fid):
                        continue
                rg = e['geom']
                if rg.type() != QgsWkbTypes.LineGeometry or rg.isEmpty():
                    continue
                for b1, b2 in self._line_segments_xy(rg):
                    if self._segment_pair_match(a1, a2, b1, b2, tol):
                        matched = True
                        break
                if matched:
                    break
            flags.append(matched)
        return flags

    def _segment_near_any_ref_line(
        self,
        a1,
        a2,
        ref_entries,
        ref_idx,
        tol,
        exclude_ref_layer_id=None,
        exclude_ref_fid=None,
    ):
        gseg = QgsGeometry.fromPolylineXY([a1, a2])
        rect = _rect_grow(gseg.boundingBox(), tol)
        cand_ids = list(ref_idx.intersects(rect))
        for cid in cand_ids:
            if cid < 0 or cid >= len(ref_entries):
                continue
            e = ref_entries[cid]
            if exclude_ref_layer_id is not None and exclude_ref_fid is not None:
                if e['layer'].id() == exclude_ref_layer_id and int(e['fid']) == int(exclude_ref_fid):
                    continue
            rg = e['geom']
            if rg.type() != QgsWkbTypes.LineGeometry or rg.isEmpty():
                continue
            try:
                if gseg.distance(rg) <= tol:
                    return True
            except Exception:
                continue
        return False

    def _soften_corner_unmatched_segments(
        self,
        seg_flags,
        check_segs,
        ref_entries,
        ref_idx,
        tol,
        exclude_ref_layer_id=None,
        exclude_ref_fid=None,
    ):
        """
        拐角容错：抑制很短、且贴近参考线、并与已匹配段相邻的“伪未匹配段”。
        目标是避免并行偏移/转角处出现用户不期望的短黑段。
        """
        if not seg_flags or not check_segs:
            return seg_flags
        out = list(seg_flags)
        short_len = max(float(tol) * 3.0, float(tol) + 1e-12)
        n = min(len(out), len(check_segs))
        for i in range(n):
            if out[i]:
                continue
            a1, a2 = check_segs[i]
            try:
                seg_len = QgsGeometry.fromPointXY(a1).distance(QgsGeometry.fromPointXY(a2))
            except Exception:
                seg_len = 0.0
            if seg_len > short_len:
                continue
            prev_ok = (i > 0 and out[i - 1])
            next_ok = (i + 1 < n and out[i + 1])
            if not (prev_ok or next_ok):
                continue
            if self._segment_near_any_ref_line(
                a1,
                a2,
                ref_entries,
                ref_idx,
                tol,
                exclude_ref_layer_id=exclude_ref_layer_id,
                exclude_ref_fid=exclude_ref_fid,
            ):
                out[i] = True
        return out

    def run(self, target_layers, ref_layers, params):
        show_messages = bool(params.get('_show_messages', True))
        show_summary = bool(params.get('_show_summary', True))
        confirm_crs = bool(params.get('_confirm_crs', True))
        show_progress = bool(params.get('_show_progress', True))
        progress_cb = params.get('_progress_cb')
        output_tag = (params.get('_output_tag') or '').strip()
        self._mode_param = params.get('mode_param')

        def _warn(msg):
            if show_messages:
                QMessageBox.warning(self.iface.mainWindow(), self.tr('提示'), msg)

        def _info(msg):
            if show_messages:
                QMessageBox.information(self.iface.mainWindow(), self.tr('提示'), msg)

        if not target_layers:
            msg = self.tr('请选择判断图层！')
            _warn(msg)
            return {'ok': False, 'error': msg, 'error_code': ERR_NO_TARGET_LAYER}

        snap_special = params.get('_snap_special') or ''
        if snap_special in SPECIAL_KEYS:
            start_time = time.time()
            ret = dispatch_snap_special(
                self.iface, self.project, snap_special, target_layers, ref_layers, params
            )
            elapsed = time.time() - start_time
            if not ret.get('ok') and show_messages:
                err_s = ret.get('error')
                if err_s:
                    _warn(str(err_s))
            elif ret.get('ok') and show_summary:
                layers_done = (ret.get('results') or {}).get('layers_created') or []
                msg = self.tr('特殊检测完成，用时 {0:.2f} 秒').format(elapsed)
                extra_ln = ret.get('summary_lines') or []
                if extra_ln:
                    msg += '\n' + '\n'.join(str(x) for x in extra_ln)
                if layers_done:
                    msg += '\n' + self.tr('输出图层：') + '\n' + '\n'.join(
                        f'  → {n}' for n in layers_done
                    )
                _info(msg)
            return {
                'ok': bool(ret.get('ok')),
                'results': ret.get('results') or {},
                'elapsed': elapsed,
                'snap_enabled': params.get('snap_enabled', False),
                'error': ret.get('error'),
                'error_code': ret.get('error_code'),
            }

        if not ref_layers:
            msg = self.tr('请选择参考图层！')
            _warn(msg)
            return {'ok': False, 'error': msg, 'error_code': ERR_NO_REF_LAYER}

        self.crs_warnings = []
        crs_check = self._check_crs_consistency(target_layers, ref_layers)

        if crs_check['has_warning'] and confirm_crs:
            reply = QMessageBox.question(
                self.iface.mainWindow(),
                self.tr('坐标系警告'),
                crs_check['message'] + self.tr('\n\n是否继续执行？'),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return {'ok': False, 'error': self.tr('用户取消执行'), 'error_code': ERR_CANCELLED}

        start_time = time.time()

        snap_enabled = params.get('snap_enabled', False)
        tolerance = float(params.get('tolerance', 0.00001))
        spatial_mode = params.get('spatial_mode')
        if spatial_mode != '__special__' and not spatial_mode:
            msg = self.tr('请选择空间命名模式')
            _warn(msg)
            return {'ok': False, 'error': msg, 'error_code': ERR_INVALID_MODE}
        # 走标准吸附时 spatial_mode 必须是具体关系代码；误传 __special__ 会导致全部要素判定未命中
        if spatial_mode == '__special__':
            msg = self.tr(
                '空间命名模式无效，请展开「吸附选项」中的「空间命名模式」下拉框重新选择一项后再执行。'
                '（若曾切换检测方式，也需确认当前为「标准」且已选对线-线关系。）'
            )
            _warn(msg)
            return {'ok': False, 'error': msg, 'error_code': ERR_INVALID_MODE}

        kinds_t = {_layer_geom_class(lyr) for lyr in target_layers}
        kinds_r = {_layer_geom_class(lyr) for lyr in ref_layers}
        kinds_t.discard(None)
        kinds_r.discard(None)
        if len(kinds_t) != 1:
            msg = self.tr('判断图层一侧只能为同一几何类型')
            _warn(msg)
            return {'ok': False, 'error': msg, 'error_code': ERR_GEOM_MISMATCH}
        if len(kinds_r) != 1:
            msg = self.tr('参考图层一侧只能为同一几何类型')
            _warn(msg)
            return {'ok': False, 'error': msg, 'error_code': ERR_GEOM_MISMATCH}

        t0 = target_layers[0]
        r0 = ref_layers[0]
        valid_modes = {c[0] for c in spatial_mode_choices(t0, r0)}
        if spatial_mode != '__special__' and spatial_mode not in valid_modes:
            msg = self.tr('当前几何组合不支持该空间命名模式')
            _warn(msg)
            return {'ok': False, 'error': msg, 'error_code': ERR_INVALID_MODE}

        base_crs = target_layers[0].crs()

        cat_target = params.get('_category_target')
        cat_ref = params.get('_category_ref')
        ref_entries, ref_idx = _build_ref_state(ref_layers, base_crs, self.project, cat_ref)
        self.ref_feature_count = len(ref_entries)
        if not ref_entries:
            msg = self.tr('参考图层无有效要素')
            _info(msg)
            return {'ok': False, 'error': msg, 'error_code': ERR_NO_REF_FEATURES}

        total_features = sum(layer.featureCount() for layer in target_layers)
        if total_features == 0:
            msg = self.tr('判断图层中没有要素！')
            _info(msg)
            return {'ok': False, 'error': msg, 'error_code': ERR_NO_TARGET_FEATURES}

        progress = None
        if show_progress:
            progress = QProgressDialog(
                self.tr('正在处理...'),
                self.tr('取消'),
                0, total_features,
                self.iface.mainWindow()
            )
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)

        results = {
            'processed': 0,
            'snapped': 0,
            'not_snapped': 0,
            'multi_target': 0,
            'layers_created': [],
            'by_layer': {},
            'crs_info': crs_check
        }

        processed_count = 0

        for layer in target_layers:
            if progress and progress.wasCanceled():
                break

            layer_result = self._process_single_layer(
                layer,
                ref_entries,
                ref_idx,
                tolerance,
                snap_enabled,
                spatial_mode,
                progress,
                processed_count,
                base_crs,
                total_features,
                progress_cb,
                output_tag,
                cat_target,
            )

            processed_count = layer_result['processed_count']
            results['processed'] += layer_result['total']
            results['snapped'] += layer_result['snapped']
            results['not_snapped'] += layer_result['not_snapped']
            results['multi_target'] += layer_result['multi_target']
            results['seg_snapped'] = results.get('seg_snapped', 0) + layer_result.get('seg_snapped', 0)
            results['seg_not_snapped'] = results.get('seg_not_snapped', 0) + layer_result.get('seg_not_snapped', 0)
            results['layers_created'].extend(layer_result['layers_created'])
            results['by_layer'][layer.name()] = {
                'total': layer_result['total'],
                'snapped': layer_result['snapped'],
                'not_snapped': layer_result['not_snapped'],
                'seg_snapped': layer_result.get('seg_snapped', 0),
                'seg_not_snapped': layer_result.get('seg_not_snapped', 0),
            }

        if progress:
            progress.close()

        elapsed = time.time() - start_time
        if show_summary:
            self._show_summary(results, snap_enabled, elapsed)
        return {
            'ok': True,
            'results': results,
            'elapsed': elapsed,
            'snap_enabled': snap_enabled,
        }

    def _check_crs_consistency(self, target_layers, ref_layers):
        result = {
            'has_warning': False,
            'message': '',
            'base_crs': None,
            'target_crs_list': [],
            'ref_crs_list': [],
            'mixed_target': False,
            'mixed_ref': False,
            'target_ref_diff': False
        }

        if not target_layers:
            return result

        base_crs = target_layers[0].crs()
        result['base_crs'] = base_crs.authid()

        target_crs_set = set()
        for layer in target_layers:
            crs_id = layer.crs().authid()
            target_crs_set.add(crs_id)
            result['target_crs_list'].append(f"{layer.name()}: {crs_id}")

        ref_crs_set = set()
        for layer in ref_layers:
            crs_id = layer.crs().authid()
            ref_crs_set.add(crs_id)
            result['ref_crs_list'].append(f"{layer.name()}: {crs_id}")

        warnings = []

        if len(target_crs_set) > 1:
            result['mixed_target'] = True
            result['has_warning'] = True
            warnings.append(self.tr('⚠ 判断图层包含不同坐标系：') + ', '.join(target_crs_set))
            warnings.append(self.tr('   将以第一个图层的坐标系为基准进行转换'))

        if len(ref_crs_set) > 1:
            result['mixed_ref'] = True
            result['has_warning'] = True
            warnings.append(self.tr('⚠ 参考图层包含不同坐标系：') + ', '.join(ref_crs_set))

        all_crs = target_crs_set.union(ref_crs_set)
        if len(all_crs) > 1:
            result['target_ref_diff'] = True
            if not result['mixed_target'] and not result['mixed_ref']:
                result['has_warning'] = True
                warnings.append(self.tr('⚠ 判断图层与参考图层坐标系不同'))

            warnings.append(self.tr('   基准坐标系：{0}').format(base_crs.authid()))
            warnings.append(self.tr('   所有参考图层将自动转换到基准坐标系'))

        geographic_count = 0
        projected_count = 0
        for layer in target_layers + ref_layers:
            if layer.crs().isGeographic():
                geographic_count += 1
            else:
                projected_count += 1

        if geographic_count > 0 and projected_count > 0:
            result['has_warning'] = True
            warnings.append(self.tr('⚠ 混合使用地理坐标系和投影坐标系'))
            warnings.append(self.tr('   建议：统一使用同一类型坐标系以获得更准确的结果'))

        result['message'] = '\n'.join(warnings)
        return result

    def _process_single_layer(
        self,
        layer,
        ref_entries,
        ref_idx,
        tolerance,
        snap_enabled,
        spatial_mode,
        progress,
        processed_count,
        base_crs,
        total_features,
        progress_cb,
        output_tag,
        category_filters=None,
    ):
        result = {
            'processed_count': processed_count,
            'total': 0,
            'snapped': 0,
            'not_snapped': 0,
            'multi_target': 0,
            'seg_snapped': 0,
            'seg_not_snapped': 0,
            'layers_created': []
        }

        geom_type = layer.geometryType()
        layer_crs = layer.crs()

        transform_to_base = None
        if layer_crs != base_crs:
            transform_to_base = QgsCoordinateTransform(
                layer_crs, base_crs, self.project
            )

        main_suffix = self.tr('_已吸附') if snap_enabled else self.tr('_未吸附')
        mode_tag = ''
        if geom_type == QgsWkbTypes.LineGeometry and spatial_mode in self.SEGMENT_OUTPUT_LINE_MODES:
            mode_tag = self._mode_name_for_layer(spatial_mode)
        if output_tag:
            base_name = f'{layer.name()}_{mode_tag}_{output_tag}{main_suffix}' if mode_tag else f'{layer.name()}_{output_tag}{main_suffix}'
        else:
            base_name = f'{layer.name()}_{mode_tag}{main_suffix}' if mode_tag else (layer.name() + main_suffix)
        main_layer = self._create_memory_layer(
            self._unique_output_layer_name(base_name), geom_type, layer_crs, layer.fields()
        )

        main_features = []

        for feature in iter_features(layer, category_filters):
            result['processed_count'] += 1
            if progress:
                progress.setValue(result['processed_count'])
                if progress.wasCanceled():
                    break
            if callable(progress_cb):
                try:
                    progress_cb(result['processed_count'], total_features, layer.name())
                except Exception:
                    pass

            if progress and progress.wasCanceled():
                break

            geom = feature.geometry()
            if geom.isEmpty():
                continue

            check_geom = QgsGeometry(geom)
            if transform_to_base:
                try:
                    check_geom.transform(transform_to_base)
                except Exception:
                    continue

            result['total'] += 1

            snap_check = self._check_spatial_relation(
                check_geom,
                ref_entries,
                ref_idx,
                spatial_mode,
                tolerance,
                exclude_ref_layer_id=layer.id(),
                exclude_ref_fid=feature.id(),
            )

            if snap_check['is_snapped']:
                result['snapped'] += 1
            else:
                result['not_snapped'] += 1

            result['multi_target'] += snap_check['multi_target_count']

            if geom_type == QgsWkbTypes.LineGeometry and spatial_mode in self.SEGMENT_OUTPUT_LINE_MODES:
                if spatial_mode == 'll_adjacent_seg_any_and_near' and not snap_check['is_snapped']:
                    # “任一段且近距”未通过时，整条线各段都按未命中处理（避免与模式定义不一致）。
                    seg_flags = [False] * len(self._line_segments_xy(check_geom))
                else:
                    seg_flags = self._line_segment_match_flags(
                        check_geom,
                        ref_entries,
                        ref_idx,
                        tolerance,
                        exclude_ref_layer_id=layer.id(),
                        exclude_ref_fid=feature.id(),
                    )
                check_segs = self._line_segments_xy(check_geom)
                if not snap_enabled:
                    seg_flags = self._soften_corner_unmatched_segments(
                        seg_flags,
                        check_segs,
                        ref_entries,
                        ref_idx,
                        tolerance,
                        exclude_ref_layer_id=layer.id(),
                        exclude_ref_fid=feature.id(),
                    )
                src_segs = self._line_segments_xy(geom)
                for idx, ok in enumerate(seg_flags):
                    if ok:
                        result['seg_snapped'] += 1
                    else:
                        result['seg_not_snapped'] += 1
                    want = ok if snap_enabled else (not ok)
                    if not want:
                        continue
                    if idx >= len(src_segs):
                        continue
                    a1, a2 = src_segs[idx]
                    new_feat = QgsFeature(layer.fields())
                    new_feat.setAttributes(feature.attributes())
                    new_feat.setGeometry(QgsGeometry.fromPolylineXY([a1, a2]))
                    main_features.append(new_feat)
            else:
                include = (snap_enabled and snap_check['is_snapped']) or (
                    not snap_enabled and not snap_check['is_snapped']
                )
                if include:
                    new_feat = QgsFeature(layer.fields())
                    new_feat.setAttributes(feature.attributes())
                    new_feat.setGeometry(geom)
                    main_features.append(new_feat)

        if main_features:
            main_layer.dataProvider().addFeatures(main_features)
            apply_memory_output_style(main_layer)
            add_layer_to_output_tree(self.project, main_layer)
            result['layers_created'].append(main_layer.name())

        return result

    def _check_spatial_relation(
        self,
        tg,
        ref_entries,
        ref_idx,
        spatial_mode,
        tol,
        exclude_ref_layer_id=None,
        exclude_ref_fid=None,
    ):
        result = {
            'is_snapped': False,
            'multi_target_count': 0,
        }
        if tg.isEmpty() or not ref_entries:
            return result
        rect = _rect_grow(tg.boundingBox(), tol)
        cand_ids = ref_idx.intersects(rect)
        cand_list = list(cand_ids)
        # 判断图层与参考图层为同一图层时，勿把当前要素与参考集中「自身」配对，
        # 否则线与自身相交恒成立，会误判为已吸附。
        if exclude_ref_layer_id is not None and exclude_ref_fid is not None:
            cand_list = [
                cid
                for cid in cand_list
                if 0 <= cid < len(ref_entries)
                and not (
                    ref_entries[cid]['layer'].id() == exclude_ref_layer_id
                    and int(ref_entries[cid]['fid']) == int(exclude_ref_fid)
                )
            ]
        if spatial_mode in AGGREGATE_LINE_POINT_MODES:
            if tg.type() != QgsWkbTypes.LineGeometry:
                return result
            rpg = ref_point_geoms_from_candidates(ref_entries, cand_list)
            mp = getattr(self, '_mode_param', None)
            if line_point_aggregate_ok(spatial_mode, tg, rpg, tol, mp):
                result['is_snapped'] = True
                n_pts = count_aggregate_line_point_matches(tg, ref_entries, cand_list, tol, spatial_mode, mp)
                result['multi_target_count'] = max(0, n_pts - 1)
            return result
        if spatial_mode == PP_KTH_NEAREST_MODE:
            if tg.type() != QgsWkbTypes.PointGeometry:
                return result
            pick = _pp_kth_nearest_pick(
                tg, ref_entries, cand_list, tol,
                int(mode_param_value(spatial_mode, getattr(self, '_mode_param', None))),
            )
            if pick is not None:
                result['is_snapped'] = True
                result['multi_target_count'] = 0
            return result
        hits = 0
        for cid in cand_list:
            if cid < 0 or cid >= len(ref_entries):
                continue
            rg = ref_entries[cid]['geom']
            if _mode_ok(spatial_mode, tg, rg, tol, getattr(self, '_mode_param', None)):
                hits += 1
        if hits > 0:
            result['is_snapped'] = True
            result['multi_target_count'] = max(0, hits - 1)
        return result

    def _create_memory_layer(self, name, geom_type, crs, fields):
        type_map = {
            QgsWkbTypes.PointGeometry: 'Point',
            QgsWkbTypes.LineGeometry: 'LineString',
            QgsWkbTypes.PolygonGeometry: 'Polygon'
        }
        type_str = type_map.get(geom_type, 'Point')
        uri = f'{type_str}?crs={crs.authid()}'

        layer = QgsVectorLayer(uri, name, 'memory')
        if fields and fields.count() > 0:
            layer.dataProvider().addAttributes(fields.toList())
            layer.updateFields()

        return layer

    def _unique_output_layer_name(self, base_name):
        name = base_name
        idx = 2
        while self.project.mapLayersByName(name):
            name = f'{base_name}_{idx}'
            idx += 1
        return name

    def _show_summary(self, results, snap_enabled, elapsed):
        mode = self.tr('提取已吸附') if snap_enabled else self.tr('提取未吸附')
        seg_mode = (results.get('seg_snapped', 0) + results.get('seg_not_snapped', 0)) > 0
        output_count = (
            results.get('seg_snapped', 0) if snap_enabled else results.get('seg_not_snapped', 0)
        ) if seg_mode else (results['snapped'] if snap_enabled else results['not_snapped'])

        detail_lines = []
        for layer_name, stats in results['by_layer'].items():
            cnt = (
                stats.get('seg_snapped', 0) if snap_enabled else stats.get('seg_not_snapped', 0)
            ) if seg_mode else (stats['snapped'] if snap_enabled else stats['not_snapped'])
            detail_lines.append(self.tr('    - {0}: {1}个').format(layer_name, cnt))

        details = '\n'.join(detail_lines)

        snapped_pct = self._percent(results['snapped'], results['processed'])
        not_snapped_pct = self._percent(results['not_snapped'], results['processed'])

        msg = (
            self.tr('处理结果统计：') + '\n'
            + self.tr('  ▸ 判断图层总要素数：{0}').format(results['processed']) + '\n'
            + self.tr('  ▸ 参考有效要素数：{0}').format(self.ref_feature_count) + '\n'
            + self.tr('  ▸ 成功吸附要素数：{0} ({1})').format(results['snapped'], snapped_pct) + '\n'
            + self.tr('  ▸ 未吸附要素数：{0} ({1})').format(results['not_snapped'], not_snapped_pct) + '\n'
        )
        if seg_mode:
            seg_total = results.get('seg_snapped', 0) + results.get('seg_not_snapped', 0)
            seg_snapped_pct = self._percent(results.get('seg_snapped', 0), seg_total)
            seg_not_snapped_pct = self._percent(results.get('seg_not_snapped', 0), seg_total)
            msg += self.tr('  ▸ 段级命中数：{0} ({1})').format(results.get('seg_snapped', 0), seg_snapped_pct) + '\n'
            msg += self.tr('  ▸ 段级未命中数：{0} ({1})').format(results.get('seg_not_snapped', 0), seg_not_snapped_pct) + '\n'

        if detail_lines:
            if snap_enabled:
                msg += self.tr('  ▸ 各图层已吸附数：') + '\n' + details + '\n'
            else:
                msg += self.tr('  ▸ 各图层未吸附数：') + '\n' + details + '\n'

        if snap_enabled:
            msg += '\n' + self.tr('✓ 共筛选出 {0} 个已吸附要素').format(output_count) + '\n'
        else:
            msg += '\n' + self.tr('✓ 共筛选出 {0} 个未吸附要素').format(output_count) + '\n'
        msg += self.tr('✓ 执行完成，用时 {0:.2f} 秒').format(elapsed) + '\n'

        if results['layers_created']:
            msg += '\n' + self.tr('输出图层：') + '\n'
            for lname in results['layers_created']:
                msg += '  → {0}\n'.format(lname)

        if results['multi_target'] > 0:
            msg += '\n' + self.tr(
                '⚠ 注意：{0} 个要素在当前空间模式下匹配到多个参考要素（统计用）。'
            ).format(results['multi_target'])

        crs_info = results.get('crs_info', {})
        if crs_info.get('has_warning'):
            msg += '\n\n' + self.tr('📍 坐标系信息：基准CRS为 {0}').format(crs_info.get('base_crs', 'N/A'))

        QMessageBox.information(
            self.iface.mainWindow(),
            self.tr('执行结果'),
            msg
        )

    def _percent(self, part, total):
        if total == 0:
            return "0%"
        return f"{100.0 * part / total:.2f}%"
