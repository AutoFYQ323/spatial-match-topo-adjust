# -*- coding: utf-8 -*-
"""2.1：模式阈值输入行、新特殊检测的参数表单、按类别分组的模式下拉。"""
import copy

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QDoubleSpinBox, QCheckBox, QPushButton, QDialog,
    QSizePolicy,
)

try:
    from .cdet_field_naming import mode_param_spec, mode_param_value, mode_category
    from .cdet_snap_special import SPECIAL_EXTRA_DEFAULTS
    from .cdet_line_length_dialog import CdetLineLengthRuleDialog
except ImportError:
    from cdet_field_naming import mode_param_spec, mode_param_value, mode_category
    from cdet_snap_special import SPECIAL_EXTRA_DEFAULTS
    from cdet_line_length_dialog import CdetLineLengthRuleDialog
from .i18n import tr as _i18n_tr
from .qtutil import run_dialog, run_menu


def tr(text):
    return _i18n_tr(text)


def add_mode_items(combo, entries):
    """entries: [(code, label, tip)]。逐项加入下拉并设浮动说明；类别（【】里的文字）变化处插分隔线。"""
    prev_cat = None
    for code, label, tip in entries:
        cat = mode_category(label)
        if combo.count() > 0 and prev_cat is not None and cat != prev_cat:
            combo.insertSeparator(combo.count())
        combo.addItem(label, code)
        if tip:
            combo.setItemData(combo.count() - 1, tip, Qt.ToolTipRole)
        prev_cat = cat


def _make_spin(lo, hi, decimals, step, suffix=''):
    sp = QDoubleSpinBox()
    sp.setRange(lo, hi)
    sp.setDecimals(decimals)
    sp.setSingleStep(step)
    if suffix:
        sp.setSuffix(suffix)
    return sp


class ModeParamRow(QWidget):
    """当前空间模式需要阈值时显示「标签在上、数值框在下」，否则隐藏。"""

    def __init__(self, parent=None, on_changed=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(3)
        self.label = QLabel()
        font = self.label.font()
        font.setBold(True)
        try:
            if font.pointSize() > 0:
                font.setPointSize(max(font.pointSize() + 1, 10))
        except Exception:
            pass
        self.label.setFont(font)
        self.label.setWordWrap(True)
        self.label.setStyleSheet('font-size: 12px; font-weight: 700; color: #212529;')
        self.spin = _make_spin(0.0, 100.0, 1, 5.0)
        self.spin.setMinimumWidth(0)
        self.spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        lay.addWidget(self.label)
        lay.addWidget(self.spin)
        self._code = None
        self._on_changed = on_changed
        self.spin.valueChanged.connect(self._emit)
        self.setVisible(False)

    def _emit(self, _v):
        if self._code and self._on_changed:
            self._on_changed(self._code, self.value())

    def set_mode(self, code, value=None):
        spec = mode_param_spec(code)
        self._code = code if spec else None
        self.setVisible(spec is not None)
        if spec is None:
            return
        self.spin.blockSignals(True)
        self.spin.setRange(spec['min'], spec['max'])
        self.spin.setDecimals(spec['decimals'])
        self.spin.setSingleStep(spec['step'])
        self.spin.setSuffix(spec['suffix'])
        self.spin.setValue(mode_param_value(code, value))
        self.spin.blockSignals(False)
        self.label.setText(tr(spec['label']))
        self.label.setProperty('msgid', spec['label'])
        self.label.setToolTip(tr(spec['tip']))
        self.label.setProperty('tip', spec['tip'])
        self.spin.setToolTip(tr(spec['tip']))

    def value(self):
        if not self._code:
            return None
        return mode_param_value(self._code, self.spin.value())


def special_defaults():
    return copy.deepcopy(dict(SPECIAL_EXTRA_DEFAULTS))


def normalize_special_values(src):
    """从任务 / 设置 dict 里取出新特殊检测参数，缺的用默认值补齐。"""
    out = special_defaults()
    for k in out:
        if src and k in src and src[k] is not None:
            out[k] = copy.deepcopy(src[k])
    return out


def format_area_rule(rule):
    r = dict(rule or {})
    k = r.get('kind', 'le')
    if k == 'ge':
        return tr('面积 ≥ {0} ㎡').format(r.get('threshold', 0))
    if k == 'between':
        return tr('面积 ∈ [{0}, {1}] ㎡').format(r.get('t_min', 0), r.get('t_max', 0))
    return tr('面积 ≤ {0} ㎡').format(r.get('threshold', 0))


def build_special_param_form(sp_key, values, parent=None, on_changed=None):
    """为 2.1 新增的特殊检测生成参数表单。返回 (QWidget 或 None, getter)，getter() -> 参数 dict。"""
    vals = normalize_special_values(values)

    def _notify():
        if on_changed:
            on_changed(dict(vals))

    def _getter():
        return dict(vals)

    if sp_key == 'poly_area':
        w = QWidget(parent)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(QLabel(tr('面积规则')))
        lbl = QLabel(format_area_rule(vals['_poly_area_rule']))
        lbl.setWordWrap(True)
        lay.addWidget(lbl, 1)
        btn = QPushButton(tr('编辑…'))
        btn.setObjectName('filterBtn')
        lay.addWidget(btn)

        def _edit():
            dlg = CdetLineLengthRuleDialog(w, vals['_poly_area_rule'], measure='area')
            if run_dialog(dlg) == QDialog.Accepted and dlg.result_rule():
                vals['_poly_area_rule'] = dlg.result_rule()
                lbl.setText(format_area_rule(vals['_poly_area_rule']))
                _notify()

        btn.clicked.connect(_edit)
        return w, _getter

    if sp_key == 'vertex_quality':
        w = QWidget(parent)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(QLabel(tr('尖角阈值')))
        sp_a = _make_spin(0.0, 179.0, 1, 1.0, ' °')
        sp_a.setValue(float(vals['_spike_angle']))
        sp_a.setToolTip(tr('顶点前后两段夹角小于该值算尖角；小于 1° 标为回头线。设 0 不查尖角。'))
        lay.addWidget(sp_a)
        lay.addWidget(QLabel(tr('最小间距')))
        sp_d = _make_spin(0.0, 1e7, 3, 0.01, ' m')
        sp_d.setValue(float(vals['_dense_min_dist']))
        sp_d.setToolTip(tr('相邻顶点距离小于该值（米）算过密；距离为 0 的重复顶点总会报出。'))
        lay.addWidget(sp_d)
        lay.addStretch(1)

        def _upd(_v=None):
            vals['_spike_angle'] = float(sp_a.value())
            vals['_dense_min_dist'] = float(sp_d.value())
            _notify()

        sp_a.valueChanged.connect(_upd)
        sp_d.valueChanged.connect(_upd)
        return w, _getter

    if sp_key == 'point_near':
        w = QWidget(parent)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(QLabel(tr('过近距离')))
        sp = _make_spin(0.0, 1e9, 3, 0.5, ' m')
        sp.setValue(float(vals['_near_dist_m']))
        sp.setToolTip(tr('两个点的实际距离（米）不超过该值算过近。'))
        lay.addWidget(sp)
        chk = QCheckBox(tr('容差内也算'))
        chk.setChecked(bool(vals['_near_include_same']))
        chk.setToolTip(tr('不勾选：吸附容差内的点当作重复点，不算过近；勾选：一并算过近。'))
        lay.addWidget(chk)
        lay.addStretch(1)

        def _upd(_v=None):
            vals['_near_dist_m'] = float(sp.value())
            vals['_near_include_same'] = bool(chk.isChecked())
            _notify()

        sp.valueChanged.connect(_upd)
        chk.toggled.connect(_upd)
        return w, _getter

    if sp_key == 'geom_validity':
        w = QWidget(parent)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        chk = QCheckBox(tr('多部件要素也算问题'))
        chk.setChecked(bool(vals['_validity_multipart']))
        chk.setToolTip(tr('勾选后，含两个及以上部件的要素也会报出（CDET_问题 写「多部件」）。'))
        lay.addWidget(chk)

        def _upd(_v=None):
            vals['_validity_multipart'] = bool(chk.isChecked())
            _notify()

        chk.toggled.connect(_upd)
        return w, _getter

    return None, _getter
