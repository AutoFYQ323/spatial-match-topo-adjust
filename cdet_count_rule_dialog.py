# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QButtonGroup,
    QSpinBox,
    QLineEdit,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
)
from .i18n import tr as _i18n_tr, localize_button_box
from .qtutil import AppMessageBox as QMessageBox


def tr(text):
    return _i18n_tr(text)


class CdetCountRuleDialog(QDialog):
    """元素数量写入规则：原样 / ≤ / ≥ / ≤与≥+其他"""

    def __init__(self, parent, rule):
        super().__init__(parent)
        self.setWindowTitle(tr('元素数量写入规则'))
        self.setModal(True)
        self._rule_in = dict(rule) if rule else {'kind': 'direct'}
        self._result = None

        root = QVBoxLayout(self)
        self._grp = QButtonGroup(self)
        self._radio_direct = QRadioButton(tr('原样写入命中元素个数（整数）'))
        self._radio_le = QRadioButton(tr('小于等于：满足与不满足各写一个值'))
        self._radio_ge = QRadioButton(tr('大于等于：满足与不满足各写一个值'))
        self._radio_le_ge = QRadioButton(tr('小于等于且大于等于：分三段（≤阈值、≥阈值、其他）'))
        self._grp.addButton(self._radio_direct, 0)
        self._grp.addButton(self._radio_le, 1)
        self._grp.addButton(self._radio_ge, 2)
        self._grp.addButton(self._radio_le_ge, 3)
        root.addWidget(self._radio_direct)
        root.addWidget(self._radio_le)
        root.addWidget(self._radio_ge)
        root.addWidget(self._radio_le_ge)

        self._stack = QWidget()
        form_outer = QVBoxLayout(self._stack)
        form_outer.setContentsMargins(0, 8, 0, 0)

        self._w_le = QGroupBox()
        fl = QFormLayout(self._w_le)
        self._spin_le = QSpinBox()
        self._spin_le.setRange(0, 99999999)
        self._edit_le_yes = QLineEdit()
        self._edit_le_no = QLineEdit()
        fl.addRow(tr('阈值（个数≤该值视为满足）'), self._spin_le)
        fl.addRow(tr('满足时写入'), self._edit_le_yes)
        fl.addRow(tr('不满足时写入'), self._edit_le_no)
        form_outer.addWidget(self._w_le)

        self._w_ge = QGroupBox()
        fg = QFormLayout(self._w_ge)
        self._spin_ge = QSpinBox()
        self._spin_ge.setRange(0, 99999999)
        self._edit_ge_yes = QLineEdit()
        self._edit_ge_no = QLineEdit()
        fg.addRow(tr('阈值（个数≥该值视为满足）'), self._spin_ge)
        fg.addRow(tr('满足时写入'), self._edit_ge_yes)
        fg.addRow(tr('不满足时写入'), self._edit_ge_no)
        form_outer.addWidget(self._w_ge)

        self._w_both = QGroupBox()
        fb = QFormLayout(self._w_both)
        self._spin_both_le = QSpinBox()
        self._spin_both_le.setRange(0, 99999999)
        self._spin_both_ge = QSpinBox()
        self._spin_both_ge.setRange(0, 99999999)
        self._edit_both_v_le = QLineEdit()
        self._edit_both_v_ge = QLineEdit()
        self._edit_both_v_other = QLineEdit()
        fb.addRow(tr('小于等于阈值（个数≤该值用第一列写入值）'), self._spin_both_le)
        fb.addRow(tr('大于等于阈值（个数≥该值用第二列写入值）'), self._spin_both_ge)
        fb.addRow(tr('≤阈值时写入'), self._edit_both_v_le)
        fb.addRow(tr('≥阈值时写入'), self._edit_both_v_ge)
        fb.addRow(tr('介于两者之间时写入（其他）'), self._edit_both_v_other)
        form_outer.addWidget(self._w_both)

        root.addWidget(self._stack)

        self._grp.buttonClicked.connect(self._sync_stack)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        localize_button_box(bb)
        bb.accepted.connect(self._on_ok)
        bb.rejected.connect(self.reject)
        root.addWidget(bb)

        self._apply_rule_to_ui(self._rule_in)
        self._sync_stack()

    def _sync_stack(self):
        bid = self._grp.checkedId()
        self._w_le.setVisible(bid == 1)
        self._w_ge.setVisible(bid == 2)
        self._w_both.setVisible(bid == 3)

    def _apply_rule_to_ui(self, r):
        k = r.get('kind', 'direct')
        if k == 'direct':
            self._radio_direct.setChecked(True)
        elif k == 'le':
            self._radio_le.setChecked(True)
            self._spin_le.setValue(int(r.get('threshold', 0)))
            self._edit_le_yes.setText(str(r.get('if_yes', '')))
            self._edit_le_no.setText(str(r.get('if_no', '')))
        elif k == 'ge':
            self._radio_ge.setChecked(True)
            self._spin_ge.setValue(int(r.get('threshold', 0)))
            self._edit_ge_yes.setText(str(r.get('if_yes', '')))
            self._edit_ge_no.setText(str(r.get('if_no', '')))
        elif k == 'le_ge':
            self._radio_le_ge.setChecked(True)
            self._spin_both_le.setValue(int(r.get('t_le', 0)))
            self._spin_both_ge.setValue(int(r.get('t_ge', 1)))
            self._edit_both_v_le.setText(str(r.get('v_le', '')))
            self._edit_both_v_ge.setText(str(r.get('v_ge', '')))
            self._edit_both_v_other.setText(str(r.get('v_other', '')))
        else:
            self._radio_direct.setChecked(True)

    def _on_ok(self):
        bid = self._grp.checkedId()
        if bid == 0:
            self._result = {'kind': 'direct'}
            self.accept()
            return
        if bid == 1:
            y = self._edit_le_yes.text().strip()
            n = self._edit_le_no.text().strip()
            if not y or not n:
                QMessageBox.warning(self, tr('提示'), tr('请填写「满足」与「不满足」时的写入值。'))
                return
            self._result = {
                'kind': 'le',
                'threshold': self._spin_le.value(),
                'if_yes': y,
                'if_no': n,
            }
            self.accept()
            return
        if bid == 2:
            y = self._edit_ge_yes.text().strip()
            n = self._edit_ge_no.text().strip()
            if not y or not n:
                QMessageBox.warning(self, tr('提示'), tr('请填写「满足」与「不满足」时的写入值。'))
                return
            self._result = {
                'kind': 'ge',
                'threshold': self._spin_ge.value(),
                'if_yes': y,
                'if_no': n,
            }
            self.accept()
            return
        if bid == 3:
            t1 = self._spin_both_le.value()
            t2 = self._spin_both_ge.value()
            if t1 >= t2:
                QMessageBox.warning(
                    self,
                    tr('提示'),
                    tr('「小于等于」阈值须小于「大于等于」阈值，否则「其他」区间为空。'),
                )
                return
            a = self._edit_both_v_le.text().strip()
            b = self._edit_both_v_ge.text().strip()
            c = self._edit_both_v_other.text().strip()
            if not a or not b or not c:
                QMessageBox.warning(self, tr('提示'), tr('请填写三段对应的写入值。'))
                return
            self._result = {
                'kind': 'le_ge',
                't_le': t1,
                't_ge': t2,
                'v_le': a,
                'v_ge': b,
                'v_other': c,
            }
            self.accept()

    def result_rule(self):
        return self._result
