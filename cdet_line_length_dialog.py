# -*- coding: utf-8 -*-
"""长度（米）/ 面积（平方米）筛选规则：≤ / ≥ / 区间内。"""
from qgis.PyQt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QRadioButton,
    QButtonGroup,
    QDoubleSpinBox,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
)
from .i18n import tr as _i18n_tr, localize_button_box


def tr(text):
    return _i18n_tr(text)


class CdetLineLengthRuleDialog(QDialog):
    def __init__(self, parent, rule, measure='length'):
        super().__init__(parent)
        area = measure == 'area'
        what = tr('面积') if area else tr('长度')
        unit = tr('平方米') if area else tr('米')
        self.setWindowTitle(tr('面积筛选规则（平方米）') if area else tr('线长度筛选规则（米）'))
        self.setModal(True)
        self._rule_in = dict(rule) if rule else {'kind': 'le', 'threshold': 0.0}
        self._result = None

        root = QVBoxLayout(self)
        self._grp = QButtonGroup(self)
        self._r_le = QRadioButton(tr('{0} ≤ 阈值（{1}）').format(what, unit))
        self._r_ge = QRadioButton(tr('{0} ≥ 阈值（{1}）').format(what, unit))
        self._r_bw = QRadioButton(tr('{0}在区间内 [最小, 最大]（{1}，含端点）').format(what, unit))
        self._grp.addButton(self._r_le, 0)
        self._grp.addButton(self._r_ge, 1)
        self._grp.addButton(self._r_bw, 2)
        root.addWidget(self._r_le)
        root.addWidget(self._r_ge)
        root.addWidget(self._r_bw)

        self._w_le = QGroupBox()
        fl = QFormLayout(self._w_le)
        self._sp_le = QDoubleSpinBox()
        self._sp_le.setRange(0.0, 1e12)
        self._sp_le.setDecimals(3)
        self._sp_le.setSingleStep(1.0)
        fl.addRow(tr('阈值（{0}）').format(unit), self._sp_le)
        root.addWidget(self._w_le)

        self._w_ge = QGroupBox()
        fg = QFormLayout(self._w_ge)
        self._sp_ge = QDoubleSpinBox()
        self._sp_ge.setRange(0.0, 1e12)
        self._sp_ge.setDecimals(3)
        self._sp_ge.setSingleStep(1.0)
        fg.addRow(tr('阈值（{0}）').format(unit), self._sp_ge)
        root.addWidget(self._w_ge)

        self._w_bw = QGroupBox()
        fb = QFormLayout(self._w_bw)
        self._sp_min = QDoubleSpinBox()
        self._sp_min.setRange(0.0, 1e12)
        self._sp_min.setDecimals(3)
        self._sp_max = QDoubleSpinBox()
        self._sp_max.setRange(0.0, 1e12)
        self._sp_max.setDecimals(3)
        fb.addRow(tr('最小（{0}）').format(unit), self._sp_min)
        fb.addRow(tr('最大（{0}）').format(unit), self._sp_max)
        root.addWidget(self._w_bw)

        root.addWidget(QLabel(
            tr('面积按图层椭球计算（平方米）。') if area
            else tr('长度按折线逐段在椭球/平面上累计（与工程设置一致）。')
        ))

        self._grp.buttonClicked.connect(self._sync)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        localize_button_box(bb)
        bb.accepted.connect(self._on_ok)
        bb.rejected.connect(self.reject)
        root.addWidget(bb)

        self._apply_in()
        self._sync()

    def _apply_in(self):
        k = self._rule_in.get('kind', 'le')
        if k == 'ge':
            self._r_ge.setChecked(True)
            self._sp_ge.setValue(float(self._rule_in.get('threshold', 0)))
        elif k == 'between':
            self._r_bw.setChecked(True)
            self._sp_min.setValue(float(self._rule_in.get('t_min', 0)))
            self._sp_max.setValue(float(self._rule_in.get('t_max', 0)))
        else:
            self._r_le.setChecked(True)
            self._sp_le.setValue(float(self._rule_in.get('threshold', 0)))

    def _sync(self):
        bid = self._grp.checkedId()
        self._w_le.setVisible(bid == 0)
        self._w_ge.setVisible(bid == 1)
        self._w_bw.setVisible(bid == 2)

    def _on_ok(self):
        bid = self._grp.checkedId()
        if bid == 1:
            self._result = {'kind': 'ge', 'threshold': float(self._sp_ge.value())}
        elif bid == 2:
            lo = float(self._sp_min.value())
            hi = float(self._sp_max.value())
            if lo > hi:
                lo, hi = hi, lo
            self._result = {'kind': 'between', 't_min': lo, 't_max': hi}
        else:
            self._result = {'kind': 'le', 'threshold': float(self._sp_le.value())}
        self.accept()

    def result_rule(self):
        return self._result
