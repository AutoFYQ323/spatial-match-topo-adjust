# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsSettings
from qgis.PyQt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QGridLayout,
    QLabel,
    QPushButton,
    QDoubleSpinBox,
    QComboBox,
    QDialogButtonBox,
    QColorDialog,
)

try:
    from .cdet_memory_style import (
        load_point_style,
        save_point_style,
        load_line_style,
        save_line_style,
        default_point_style,
        default_line_style,
    )
except ImportError:
    from cdet_memory_style import (
        load_point_style,
        save_point_style,
        load_line_style,
        save_line_style,
        default_point_style,
        default_line_style,
    )
from .i18n import tr as _i18n_tr, localize_button_box


def _qcolor_from_csv(s):
    parts = [x.strip() for x in (s or '').split(',') if x.strip() != '']
    try:
        n = [int(float(x)) for x in parts]
    except (TypeError, ValueError):
        return QColor(0, 0, 0, 0)
    if len(n) == 3:
        return QColor(n[0], n[1], n[2], 255)
    if len(n) >= 4:
        return QColor(n[0], n[1], n[2], n[3])
    return QColor(0, 0, 0, 0)


def _csv_from_qcolor(c):
    return f'{c.red()},{c.green()},{c.blue()},{c.alpha()}'


def _style_btn_color(btn, c):
    btn.setStyleSheet(
        f'background-color: rgba({c.red()},{c.green()},{c.blue()},{c.alpha()}); '
        f'border: 1px solid #888; min-height: 22px; min-width: 80px;'
    )


LINE_STYLE_CHOICES = [
    ('solid', '实线'),
    ('dash', '虚线'),
    ('dot', '点线'),
    ('dash dot', '点划线'),
    ('dash dot dot', '双点划线'),
    ('long dash', '长虚线'),
    ('long dash dot', '长点划线'),
]


class CdetMemoryStyleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr('临时图层默认样式'))
        self.setMinimumWidth(420)
        self._pt_fill = QColor(0, 0, 0, 0)
        self._pt_outline = QColor(0, 0, 0, 255)
        self._ln_color = QColor(0, 0, 0, 255)
        root = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.addTab(self._build_point_tab(), self.tr('临时点图层'))
        tabs.addTab(self._build_line_tab(), self.tr('临时线图层'))
        root.addWidget(tabs)
        row_bt = QHBoxLayout()
        self.btn_restore_defaults = QPushButton(self.tr('恢复默认'))
        self.btn_restore_defaults.clicked.connect(self._on_restore_defaults)
        row_bt.addWidget(self.btn_restore_defaults)
        row_bt.addStretch()
        bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        localize_button_box(bbox)
        row_bt.addWidget(bbox)
        root.addLayout(row_bt)
        bbox.accepted.connect(self._on_ok)
        bbox.rejected.connect(self.reject)
        self._load_from_settings()

    def tr(self, text):
        if getattr(self, '_i18n_raw', False):
            return text
        return _i18n_tr(text)

    def _build_point_tab(self):
        w = QWidget()
        g = QGridLayout(w)
        r = 0
        g.addWidget(QLabel(self.tr('符号大小 (mm)')), r, 0)
        self.sp_pt_size = QDoubleSpinBox()
        self.sp_pt_size.setDecimals(2)
        self.sp_pt_size.setRange(0.1, 80.0)
        self.sp_pt_size.setSingleStep(0.5)
        g.addWidget(self.sp_pt_size, r, 1)
        r += 1
        g.addWidget(QLabel(self.tr('填充颜色')), r, 0)
        row_f = QHBoxLayout()
        self.btn_pt_fill = QPushButton(self.tr('选择…'))
        self.btn_pt_fill.clicked.connect(self._pick_pt_fill)
        row_f.addWidget(self.btn_pt_fill)
        row_f.addStretch()
        g.addLayout(row_f, r, 1)
        r += 1
        g.addWidget(QLabel(self.tr('描边颜色')), r, 0)
        row_o = QHBoxLayout()
        self.cb_pt_outline_mode = QComboBox()
        # 固定中文，不参与 Qt 翻译上下文（按需求不本地化）
        self.cb_pt_outline_mode.addItem(self.tr('指定颜色'), 'fixed')
        self.cb_pt_outline_mode.addItem(self.tr('随机颜色'), 'random')
        self.cb_pt_outline_mode.currentIndexChanged.connect(self._on_pt_outline_mode_changed)
        row_o.addWidget(self.cb_pt_outline_mode)
        self.btn_pt_outline = QPushButton(self.tr('选择…'))
        self.btn_pt_outline.clicked.connect(self._pick_pt_outline)
        row_o.addWidget(self.btn_pt_outline)
        row_o.addStretch()
        g.addLayout(row_o, r, 1)
        r += 1
        g.addWidget(QLabel(self.tr('描边宽度')), r, 0)
        self.sp_pt_outline_w = QDoubleSpinBox()
        self.sp_pt_outline_w.setDecimals(2)
        self.sp_pt_outline_w.setRange(0.0, 20.0)
        self.sp_pt_outline_w.setSingleStep(0.1)
        g.addWidget(self.sp_pt_outline_w, r, 1)
        hint = QLabel(
            self.tr(
                '提示：填充可选带透明度的颜色；描边宽度为毫米。'
                '「随机颜色」：使用内置约 10 种描边色，按每次生成临时点图层的先后顺序循环分配（非真随机）；'
                '仍沿用下方保存的透明度（若曾选带透明描边）。'
            )
        )
        hint.setWordWrap(True)
        hint.setStyleSheet('color: palette(mid);')
        g.addWidget(hint, r + 1, 0, 1, 2)
        return w

    def _build_line_tab(self):
        w = QWidget()
        g = QGridLayout(w)
        r = 0
        g.addWidget(QLabel(self.tr('线颜色')), r, 0)
        row_c = QHBoxLayout()
        self.btn_ln_color = QPushButton(self.tr('选择…'))
        self.btn_ln_color.clicked.connect(self._pick_ln_color)
        row_c.addWidget(self.btn_ln_color)
        row_c.addStretch()
        g.addLayout(row_c, r, 1)
        r += 1
        g.addWidget(QLabel(self.tr('线宽 (mm)')), r, 0)
        self.sp_ln_width = QDoubleSpinBox()
        self.sp_ln_width.setDecimals(2)
        self.sp_ln_width.setRange(0.01, 50.0)
        self.sp_ln_width.setSingleStep(0.5)
        g.addWidget(self.sp_ln_width, r, 1)
        r += 1
        g.addWidget(QLabel(self.tr('线型')), r, 0)
        self.cb_ln_style = QComboBox()
        for key, label in LINE_STYLE_CHOICES:
            self.cb_ln_style.addItem(self.tr(label), key)
        g.addWidget(self.cb_ln_style, r, 1)
        return w

    def _load_from_settings(self):
        pd = load_point_style()
        ld = load_line_style()
        self.sp_pt_size.setValue(float(pd.get('size', 6.0)))
        self._pt_fill = _qcolor_from_csv(pd.get('fill', '0,0,0,0'))
        self._pt_outline = _qcolor_from_csv(pd.get('outline', '0,0,0'))
        self.sp_pt_outline_w.setValue(float(pd.get('outline_width', 1.0)))
        _style_btn_color(self.btn_pt_fill, self._pt_fill)
        _style_btn_color(self.btn_pt_outline, self._pt_outline)
        om = 'random' if pd.get('outline_random') else 'fixed'
        idx = self.cb_pt_outline_mode.findData(om)
        if idx < 0:
            idx = self.cb_pt_outline_mode.findData('random')
        self.cb_pt_outline_mode.blockSignals(True)
        self.cb_pt_outline_mode.setCurrentIndex(idx if idx >= 0 else 1)
        self.cb_pt_outline_mode.blockSignals(False)
        self._on_pt_outline_mode_changed()
        self._ln_color = _qcolor_from_csv(ld.get('color', '0,0,0'))
        self.sp_ln_width.setValue(float(ld.get('width', 5.0)))
        _style_btn_color(self.btn_ln_color, self._ln_color)
        idx = self.cb_ln_style.findData(ld.get('line_style', 'dash'))
        if idx < 0:
            idx = self.cb_ln_style.findData('dash')
        self.cb_ln_style.setCurrentIndex(max(0, idx))

    def _pick_pt_fill(self):
        c = QColorDialog.getColor(
            self._pt_fill,
            self,
            self.tr('填充颜色'),
            QColorDialog.ShowAlphaChannel,
        )
        if c.isValid():
            self._pt_fill = c
            _style_btn_color(self.btn_pt_fill, self._pt_fill)

    def _on_pt_outline_mode_changed(self, _i=None):
        fixed = self.cb_pt_outline_mode.currentData() == 'fixed'
        self.btn_pt_outline.setEnabled(fixed)
        if not fixed:
            self.btn_pt_outline.setToolTip(self.tr('内置多色按生成顺序循环；不需要在此选色'))
        else:
            self.btn_pt_outline.setToolTip('')

    def _pick_pt_outline(self):
        c = QColorDialog.getColor(
            self._pt_outline,
            self,
            self.tr('描边颜色'),
            QColorDialog.ShowAlphaChannel,
        )
        if c.isValid():
            self._pt_outline = c
            _style_btn_color(self.btn_pt_outline, self._pt_outline)

    def _pick_ln_color(self):
        c = QColorDialog.getColor(
            self._ln_color,
            self,
            self.tr('线颜色'),
            QColorDialog.ShowAlphaChannel,
        )
        if c.isValid():
            self._ln_color = c
            _style_btn_color(self.btn_ln_color, self._ln_color)

    def _on_ok(self):
        pd = {
            'size': float(self.sp_pt_size.value()),
            'fill': _csv_from_qcolor(self._pt_fill),
            'outline': _csv_from_qcolor(self._pt_outline),
            'outline_width': float(self.sp_pt_outline_w.value()),
            'outline_random': self.cb_pt_outline_mode.currentData() == 'random',
        }
        _ls = self.cb_ln_style.currentData()
        if not _ls:
            _ls = 'solid'
        ld = {
            'color': _csv_from_qcolor(self._ln_color),
            'width': float(self.sp_ln_width.value()),
            'line_style': str(_ls),
        }
        save_point_style(pd)
        save_line_style(ld)
        QgsSettings().sync()
        self.accept()

    def _on_restore_defaults(self):
        pd = default_point_style()
        ld = default_line_style()
        self.sp_pt_size.setValue(pd['size'])
        self._pt_fill = _qcolor_from_csv(pd['fill'])
        self._pt_outline = _qcolor_from_csv(pd['outline'])
        self.sp_pt_outline_w.setValue(pd['outline_width'])
        _style_btn_color(self.btn_pt_fill, self._pt_fill)
        _style_btn_color(self.btn_pt_outline, self._pt_outline)
        om = 'random' if pd.get('outline_random') else 'fixed'
        idx = self.cb_pt_outline_mode.findData(om)
        if idx < 0:
            idx = self.cb_pt_outline_mode.findData('random')
        self.cb_pt_outline_mode.blockSignals(True)
        self.cb_pt_outline_mode.setCurrentIndex(idx if idx >= 0 else 1)
        self.cb_pt_outline_mode.blockSignals(False)
        self._on_pt_outline_mode_changed()
        self._ln_color = _qcolor_from_csv(ld['color'])
        self.sp_ln_width.setValue(ld['width'])
        _style_btn_color(self.btn_ln_color, self._ln_color)
        idx = self.cb_ln_style.findData(ld['line_style'])
        if idx >= 0:
            self.cb_ln_style.setCurrentIndex(idx)
