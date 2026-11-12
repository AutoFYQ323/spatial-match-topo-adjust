# -*- coding: utf-8 -*-
"""Small call-name differences between QGIS 3 (Qt 5) and QGIS 4 (Qt 6)."""

from qgis.PyQt.QtWidgets import QHeaderView


def run_dialog(widget):
    try:
        guard_all_combos(widget)
    except Exception:
        pass
    runner = getattr(widget, "exec_", None)
    if not callable(runner):
        runner = widget.exec
    return runner()


def run_menu(menu, pos):
    runner = getattr(menu, "exec_", None)
    if not callable(runner):
        runner = menu.exec
    return runner(pos)


def pointer_pos(event):
    if hasattr(event, "position"):
        point = event.position()
        if hasattr(point, "toPoint"):
            return point.toPoint()
        return point
    return event.pos()


def header_mode(name):
    mode = getattr(QHeaderView, name, None)
    if mode is not None:
        return mode
    return getattr(QHeaderView.ResizeMode, name)


def qvariant_type(name):
    """Type token accepted by QgsField on Qt 5 (QVariant) and Qt 6 (QMetaType)."""
    try:
        from qgis.PyQt.QtCore import QVariant
        val = getattr(QVariant, name, None)
        if val is not None and not callable(val):
            return val
    except Exception:
        pass
    try:
        from qgis.PyQt.QtCore import QMetaType
        typ = getattr(QMetaType, "Type", None)
        if typ is not None:
            val = getattr(typ, name, None)
            if val is not None:
                return val
        val = getattr(QMetaType, name, None)
        if val is not None:
            return val
    except Exception:
        pass
    raise AttributeError("qvariant_type: %s" % name)


def qtype_is(value, name):
    """True if a QgsField.type() / QVariant value matches the named type."""
    targets = []
    try:
        from qgis.PyQt.QtCore import QVariant
        val = getattr(QVariant, name, None)
        if val is not None and not callable(val):
            targets.append(val)
    except Exception:
        pass
    try:
        from qgis.PyQt.QtCore import QMetaType
        typ = getattr(QMetaType, "Type", None)
        if typ is not None:
            val = getattr(typ, name, None)
            if val is not None:
                targets.append(val)
        val = getattr(QMetaType, name, None)
        if val is not None:
            targets.append(val)
    except Exception:
        pass
    return value in targets


def is_null_qvariant(value):
    try:
        from qgis.PyQt.QtCore import QVariant
        if isinstance(value, QVariant):
            return bool(value.isNull())
    except Exception:
        pass
    return False


def dialog_accepted():
    from qgis.PyQt.QtWidgets import QDialog
    accepted = getattr(QDialog, "Accepted", None)
    if accepted is None:
        accepted = QDialog.DialogCode.Accepted
    return accepted


from qgis.PyQt.QtCore import QPoint, QRect, QSize, Qt
from qgis.PyQt.QtWidgets import QLayout, QStyle


class FlowLayout(QLayout):
    """Left-to-right, wrapping layout so a narrow window does not clip a single row."""

    def __init__(self, parent=None, margin=-1, hspacing=-1, vspacing=-1):
        super().__init__(parent)
        if margin >= 0:
            self.setContentsMargins(margin, margin, margin, margin)
        self._hspacing = hspacing
        self._vspacing = vspacing
        self._items = []

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _smart_spacing(self, metric):
        parent = self.parent()
        if parent is None:
            return -1
        if parent.isWidgetType():
            return parent.style().pixelMetric(metric, None, parent)
        return parent.spacing()

    def _hspace(self):
        if self._hspacing >= 0:
            return self._hspacing
        return self._smart_spacing(QStyle.PM_LayoutHorizontalSpacing)

    def _vspace(self):
        if self._vspacing >= 0:
            return self._vspacing
        return self._smart_spacing(QStyle.PM_LayoutVerticalSpacing)

    def _do_layout(self, rect, test_only):
        m = self.contentsMargins()
        effective = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x = effective.x()
        y = effective.y()
        line_height = 0
        space_x = self._hspace()
        space_y = self._vspace()
        if space_x < 0:
            space_x = 8
        if space_y < 0:
            space_y = 6
        for item in self._items:
            wid = item.widget()
            if wid is not None and wid.isHidden():
                continue
            hint = item.sizeHint()
            next_x = x + hint.width() + space_x
            if next_x - space_x > effective.right() and line_height > 0:
                x = effective.x()
                y = y + line_height + space_y
                next_x = x + hint.width() + space_x
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x = next_x
            line_height = max(line_height, hint.height())
        return y + line_height - rect.y() + m.bottom()


def _combo_popup_open(combo):
    view = getattr(combo, "view", None)
    if not callable(view):
        return False
    try:
        widget = view()
    except Exception:
        return False
    return widget is not None and widget.isVisible()


class _ComboWheelGuard(object):
    """Block wheel on closed combo boxes so the value does not change. Open popups can still scroll."""

    def eventFilter(self, obj, event):
        try:
            from qgis.PyQt.QtCore import QEvent
            from qgis.PyQt.QtWidgets import QComboBox, QAbstractSpinBox
        except Exception:
            return False
        if event.type() != QEvent.Wheel:
            return False
        # Spin boxes stay wheelable, even if they sit inside a combo-like row.
        if isinstance(obj, QAbstractSpinBox):
            return False
        combo = obj if isinstance(obj, QComboBox) else None
        if combo is None:
            parent = obj.parent() if hasattr(obj, "parent") else None
            if isinstance(parent, QComboBox):
                combo = parent
        if combo is None:
            return False
        if _combo_popup_open(combo):
            return False
        event.ignore()
        return True


_COMBO_WHEEL_GUARD = None


def _wheel_guard():
    global _COMBO_WHEEL_GUARD
    if _COMBO_WHEEL_GUARD is None:
        from qgis.PyQt.QtCore import QObject

        class _Guard(QObject, _ComboWheelGuard):
            pass

        _COMBO_WHEEL_GUARD = _Guard()
    return _COMBO_WHEEL_GUARD


def guard_combo_wheel(combo):
    from qgis.PyQt.QtWidgets import QComboBox
    if not isinstance(combo, QComboBox):
        return combo
    guard = _wheel_guard()
    try:
        combo.installEventFilter(guard)
    except Exception:
        pass
    return combo


def _dialog_accepted(code):
    from qgis.PyQt.QtWidgets import QDialog
    ok = getattr(QDialog, "Accepted", None)
    if ok is None:
        ok = QDialog.DialogCode.Accepted
    return code == ok


def _standard_button(owner, name):
    direct = getattr(owner, name, None)
    if direct is not None:
        return direct
    for nest_name in ("StandardButton", "Icon"):
        nested = getattr(owner, nest_name, None)
        if nested is None:
            continue
        val = getattr(nested, name, None)
        if val is not None:
            return val
    return None


def localize_message_box(box):
    """Standard buttons follow the plugin language, not the QGIS locale."""
    if box is None:
        return box
    try:
        from .i18n import tr
    except ImportError:
        from i18n import tr
    from qgis.PyQt.QtWidgets import QMessageBox
    mapping = (
        ("Ok", "确定"),
        ("Cancel", "取消"),
        ("Yes", "是"),
        ("No", "否"),
        ("Close", "关闭"),
    )
    for name, msgid in mapping:
        flag = _standard_button(QMessageBox, name)
        if flag is None:
            continue
        try:
            button = box.button(flag)
        except Exception:
            button = None
        if button is not None:
            button.setText(tr(msgid))
    return box


from qgis.PyQt.QtWidgets import QMessageBox as _QtMessageBox


class AppMessageBox(_QtMessageBox):
    """QMessageBox whose OK / Cancel / Yes / No follow the plugin language."""

    def showEvent(self, event):
        localize_message_box(self)
        super(AppMessageBox, self).showEvent(event)

    @staticmethod
    def _show(parent, icon, title, text, buttons, default_button):
        box = AppMessageBox(parent)
        box.setIcon(icon)
        box.setWindowTitle("" if title is None else str(title))
        box.setText("" if text is None else str(text))
        if buttons is not None:
            box.setStandardButtons(buttons)
        if default_button not in (None, 0):
            try:
                box.setDefaultButton(default_button)
            except Exception:
                pass
        localize_message_box(box)
        return run_dialog(box)

    @staticmethod
    def information(parent, title, text, buttons=None, defaultButton=None):
        if buttons is None:
            buttons = _standard_button(_QtMessageBox, "Ok")
        icon = _standard_button(_QtMessageBox, "Information")
        return AppMessageBox._show(parent, icon, title, text, buttons, defaultButton)

    @staticmethod
    def warning(parent, title, text, buttons=None, defaultButton=None):
        if buttons is None:
            buttons = _standard_button(_QtMessageBox, "Ok")
        icon = _standard_button(_QtMessageBox, "Warning")
        return AppMessageBox._show(parent, icon, title, text, buttons, defaultButton)

    @staticmethod
    def critical(parent, title, text, buttons=None, defaultButton=None):
        if buttons is None:
            buttons = _standard_button(_QtMessageBox, "Ok")
        icon = _standard_button(_QtMessageBox, "Critical")
        return AppMessageBox._show(parent, icon, title, text, buttons, defaultButton)

    @staticmethod
    def question(parent, title, text, buttons=None, defaultButton=None):
        if buttons is None:
            yes = _standard_button(_QtMessageBox, "Yes")
            no = _standard_button(_QtMessageBox, "No")
            buttons = yes | no
        icon = _standard_button(_QtMessageBox, "Question")
        return AppMessageBox._show(parent, icon, title, text, buttons, defaultButton)


def _input_mode(name):
    from qgis.PyQt.QtWidgets import QInputDialog
    val = getattr(QInputDialog, name, None)
    if val is not None:
        return val
    return getattr(QInputDialog.InputMode, name)


def _localize_input(dlg):
    try:
        from .i18n import localize_button_box
    except ImportError:
        from i18n import localize_button_box
    from qgis.PyQt.QtWidgets import QDialogButtonBox
    box = dlg.findChild(QDialogButtonBox)
    if box is not None:
        localize_button_box(box)
    return dlg


def ask_text(parent, title, label, text=""):
    """One-line name prompt. OK and Cancel use the plugin language."""
    from qgis.PyQt.QtWidgets import QInputDialog
    dlg = QInputDialog(parent)
    dlg.setWindowTitle("" if title is None else str(title))
    dlg.setLabelText("" if label is None else str(label))
    dlg.setInputMode(_input_mode("TextInput"))
    dlg.setTextValue("" if text is None else str(text))
    _localize_input(dlg)
    ok = _dialog_accepted(run_dialog(dlg))
    return dlg.textValue(), ok


def ask_item(parent, title, label, items, current=0, editable=False):
    from qgis.PyQt.QtWidgets import QInputDialog
    values = [str(item) for item in (items or [])]
    dlg = QInputDialog(parent)
    dlg.setWindowTitle("" if title is None else str(title))
    dlg.setLabelText("" if label is None else str(label))
    try:
        dlg.setComboBoxItems(values)
        dlg.setComboBoxEditable(bool(editable))
    except Exception:
        pass
    if values:
        idx = int(current or 0)
        if idx < 0 or idx >= len(values):
            idx = 0
        dlg.setTextValue(values[idx])
    _localize_input(dlg)
    ok = _dialog_accepted(run_dialog(dlg))
    return dlg.textValue(), ok


def guard_all_combos(root):
    """Install the wheel guard on every QComboBox under root (dialogs included)."""
    from qgis.PyQt.QtWidgets import QComboBox
    if root is None:
        return
    if isinstance(root, QComboBox):
        guard_combo_wheel(root)
    for combo in root.findChildren(QComboBox):
        guard_combo_wheel(combo)
