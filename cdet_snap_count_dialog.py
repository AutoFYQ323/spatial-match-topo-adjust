# -*- coding: utf-8 -*-
"""吸附模式：按参考要素个数筛选（≤ / ≥ / 区间内），与线长规则结构一致。"""
from qgis.PyQt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QRadioButton,
    QButtonGroup,
    QSpinBox,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
)
from .i18n import tr as _i18n_tr, localize_button_box


def tr(text):
    return _i18n_tr(text)


class CdetSnapCountRuleDialog(QDialog):
    def __init__(self, parent, rule):
        super().__init__(parent)
        self.setWindowTitle(tr('个数筛选规则'))
        self.setModal(True)
        self._rule_in = dict(rule) if rule else {'kind': 'le', 'threshold': 0}
        self._result = None

        root = QVBoxLayout(self)
        self._grp = QButtonGroup(self)
        self._r_le = QRadioButton(tr('个数 ≤ 阈值'))
        self._r_ge = QRadioButton(tr('个数 ≥ 阈值'))
        self._r_eq = QRadioButton(tr('个数 = 阈值（恰好）'))
        self._r_bw = QRadioButton(tr('个数在区间内 [最小, 最大]（含端点）'))
        self._grp.addButton(self._r_le, 0)
        self._grp.addButton(self._r_ge, 1)
        self._grp.addButton(self._r_eq, 3)
        self._grp.addButton(self._r_bw, 2)
        root.addWidget(self._r_le)
        root.addWidget(self._r_ge)
        root.addWidget(self._r_eq)
        root.addWidget(self._r_bw)

        self._w_le = QGroupBox()
        fl = QFormLayout(self._w_le)
        self._sp_le = QSpinBox()
        self._sp_le.setRange(0, 999999999)
        fl.addRow(tr('阈值'), self._sp_le)
        root.addWidget(self._w_le)

        self._w_ge = QGroupBox()
        fg = QFormLayout(self._w_ge)
        self._sp_ge = QSpinBox()
        self._sp_ge.setRange(0, 999999999)
        fg.addRow(tr('阈值'), self._sp_ge)
        root.addWidget(self._w_ge)

        self._w_eq = QGroupBox()
        fe = QFormLayout(self._w_eq)
        self._sp_eq = QSpinBox()
        self._sp_eq.setRange(0, 999999999)
        fe.addRow(tr('阈值'), self._sp_eq)
        root.addWidget(self._w_eq)

        self._w_bw = QGroupBox()
        fb = QFormLayout(self._w_bw)
        self._sp_min = QSpinBox()
        self._sp_min.setRange(0, 999999999)
        self._sp_max = QSpinBox()
        self._sp_max.setRange(0, 999999999)
        fb.addRow(tr('最小'), self._sp_min)
        fb.addRow(tr('最大'), self._sp_max)
        root.addWidget(self._w_bw)

        root.addWidget(
            QLabel(
                tr(
                    '统计规则依各子类型而定（如：点关联线 / 线关联点按挂接位置去重计数；'
                    '面内点/线按与面相交计件）。',
                )
            )
        )

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
            self._sp_ge.setValue(int(float(self._rule_in.get('threshold', 0))))
        elif k == 'eq':
            self._r_eq.setChecked(True)
            self._sp_eq.setValue(int(float(self._rule_in.get('threshold', 0))))
        elif k == 'between':
            self._r_bw.setChecked(True)
            self._sp_min.setValue(int(float(self._rule_in.get('t_min', 0))))
            self._sp_max.setValue(int(float(self._rule_in.get('t_max', 0))))
        else:
            self._r_le.setChecked(True)
            self._sp_le.setValue(int(float(self._rule_in.get('threshold', 0))))

    def _sync(self):
        bid = self._grp.checkedId()
        self._w_le.setVisible(bid == 0)
        self._w_ge.setVisible(bid == 1)
        self._w_eq.setVisible(bid == 3)
        self._w_bw.setVisible(bid == 2)

    def _on_ok(self):
        bid = self._grp.checkedId()
        if bid == 1:
            self._result = {'kind': 'ge', 'threshold': float(self._sp_ge.value())}
        elif bid == 3:
            self._result = {'kind': 'eq', 'threshold': float(self._sp_eq.value())}
        elif bid == 2:
            lo = int(self._sp_min.value())
            hi = int(self._sp_max.value())
            if lo > hi:
                lo, hi = hi, lo
            self._result = {'kind': 'between', 't_min': float(lo), 't_max': float(hi)}
        else:
            self._result = {'kind': 'le', 'threshold': float(self._sp_le.value())}
        self.accept()

    def result_rule(self):
        return self._result


def format_snap_count_rule_summary(rule):
    r = dict(rule or {})
    k = r.get('kind', 'le')
    if k == 'ge':
        return tr('个数 ≥ {0}').format(int(float(r.get('threshold', 0))))
    if k == 'eq':
        return tr('个数 = {0}').format(int(float(r.get('threshold', 0))))
    if k == 'between':
        return tr('个数 ∈ [{0}, {1}]').format(
            int(float(r.get('t_min', 0))), int(float(r.get('t_max', 0)))
        )
    return tr('个数 ≤ {0}').format(int(float(r.get('threshold', 0))))
