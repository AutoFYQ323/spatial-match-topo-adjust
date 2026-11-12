# -*- coding: utf-8 -*-
import copy
import html
import json
import time
from qgis.PyQt.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout,
                                 QGroupBox, QCheckBox, QRadioButton, QButtonGroup, QListWidget, QPushButton,
                                 QToolButton, QAbstractSpinBox, QLabel, QSizePolicy, QDoubleSpinBox, QSpinBox, QLineEdit,
                                 QStackedWidget, QComboBox, QGridLayout,
                                 QMenu,
                                 QListWidgetItem, QDialogButtonBox, QAbstractItemView,
                                 QFileDialog, QProgressDialog,
                                 QTreeWidget, QTreeWidgetItem, QScrollArea, QAbstractScrollArea, QFrame,
                                 QStyledItemDelegate, QStyle, QStyleOptionViewItem, QApplication)
from qgis.PyQt.QtCore import Qt, QEvent, QSize, QPoint, QRect
from qgis.PyQt.QtGui import QBrush, QColor, QFont, QFontMetrics
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsSettings,
    QgsWkbTypes,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
)

try:
    from .cdet_field_naming import (
        run_field_naming,
        spatial_mode_choices,
        multi_match_choices,
        multi_match_tip,
        MULTI_MATCH_COMMON_TIP,
        spatial_mode_label,
        format_mode_param,
        mode_param_spec,
        mode_param_value,
        mode_category,
        LAYER_NAME_VALUE,
        LAYER_NAME_SETTINGS_KEY,
        REF_ELEMENT_COUNT,
        REF_ELEMENT_COUNT_STORE,
        default_element_count_rule,
        format_element_count_rule_summary,
        _field_intersection,
        _layer_geom_class,
        field_display_label,
        field_display_label_from_layer,
        resolve_field_name,
        normalize_count_attach,
        LP_END_FIELDS,
    )
    from .cdet_category import (
        ROLE_LAYER_ID,
        ROLE_LAYER_NAME,
        safe_feature_count,
        count_features_by_expr,
        layers_feature_count,
        ROLE_HAS_CATS,
        ROLE_CATS,
        ROLE_FEATURE_COUNT,
        CAT_MARK,
        layer_filter_categories,
        layer_item_display,
        format_layer_caption,
        align_saved_categories,
        normalize_category_map,
        filters_by_layer_id,
    )
    from .cdet_count_rule_dialog import CdetCountRuleDialog
    from .cdet_line_length_dialog import CdetLineLengthRuleDialog
    from .cdet_snap_count_dialog import CdetSnapCountRuleDialog, format_snap_count_rule_summary
    from .cdet_dialog_params import (
        ModeParamRow,
        add_mode_items,
        build_special_param_form,
        normalize_special_values,
        special_defaults,
    )
    from .cdet_snap_special import (
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
        expand_polygon_output_codes_for_tasks,
        SPECIAL_KEYS,
        SPECIAL_KEYS_NO_REF,
        normalize_overlap_scope,
        special_mode_label,
        special_mode_label_source,
        special_mode_tip,
        special_modes_for_geom,
        SPECIAL_TARGET_GEOMS,
        SPECIAL_REF_GEOM,
        SPECIAL_EXTRA_DEFAULTS,
        SPECIAL_KEYS_NO_SNAP_FILTER,
        QUALITY_KEYS,
    )
    from .cdet_move import (
        run_move,
        remove_move_preview_layers,
        move_mode_choices,
        move_mode_label,
        move_mode_known,
        is_withdrawn_line_line_mode,
        layers_are_line_line,
        withdrawn_line_line_message,
    )
except ImportError:
    from cdet_field_naming import (
        run_field_naming,
        spatial_mode_choices,
        multi_match_choices,
        multi_match_tip,
        MULTI_MATCH_COMMON_TIP,
        spatial_mode_label,
        format_mode_param,
        mode_param_spec,
        mode_param_value,
        mode_category,
        LAYER_NAME_VALUE,
        LAYER_NAME_SETTINGS_KEY,
        REF_ELEMENT_COUNT,
        REF_ELEMENT_COUNT_STORE,
        default_element_count_rule,
        format_element_count_rule_summary,
        _field_intersection,
        _layer_geom_class,
        field_display_label,
        field_display_label_from_layer,
        resolve_field_name,
        normalize_count_attach,
        LP_END_FIELDS,
    )
    from cdet_category import (
        ROLE_LAYER_ID,
        ROLE_LAYER_NAME,
        safe_feature_count,
        count_features_by_expr,
        layers_feature_count,
        ROLE_HAS_CATS,
        ROLE_CATS,
        ROLE_FEATURE_COUNT,
        CAT_MARK,
        layer_filter_categories,
        layer_item_display,
        format_layer_caption,
        align_saved_categories,
        normalize_category_map,
        filters_by_layer_id,
    )
    from cdet_count_rule_dialog import CdetCountRuleDialog
    from cdet_line_length_dialog import CdetLineLengthRuleDialog
    from cdet_snap_count_dialog import CdetSnapCountRuleDialog, format_snap_count_rule_summary
    from cdet_dialog_params import (
        ModeParamRow,
        add_mode_items,
        build_special_param_form,
        normalize_special_values,
        special_defaults,
    )
    from cdet_snap_special import (
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
        expand_polygon_output_codes_for_tasks,
        SPECIAL_KEYS,
        SPECIAL_KEYS_NO_REF,
        normalize_overlap_scope,
        special_mode_label,
        special_mode_label_source,
        special_mode_tip,
        special_modes_for_geom,
        SPECIAL_TARGET_GEOMS,
        SPECIAL_REF_GEOM,
        SPECIAL_EXTRA_DEFAULTS,
        SPECIAL_KEYS_NO_SNAP_FILTER,
        QUALITY_KEYS,
    )
    from cdet_move import (
        run_move,
        remove_move_preview_layers,
        move_mode_choices,
        move_mode_label,
        move_mode_known,
        is_withdrawn_line_line_mode,
        layers_are_line_line,
        withdrawn_line_line_message,
    )

from .i18n import tr as _i18n_tr, language_changed, current_language, set_language, localize_button_box
from .errors import EMPTY_FEATURES
from .i18n.stamp import stamp_tree, retranslate_tree
from .qtutil import (
    run_dialog, run_menu, pointer_pos, FlowLayout, guard_all_combos,
    AppMessageBox as QMessageBox, ask_text, ask_item,
)
from .ui_chrome import (
    language_icon, help_icon, import_icon, export_icon, mode_icon,
    style_icon_button, style_filter_button, style_param_label,
    configure_fit_combo, param_block, ACTION_BTN_H, BOTTOM_BTN_H, FILTER_BTN_H,
)
from .settings_compat import (
    settings_value,
    settings_set,
    is_layer_title_token,
    is_element_count_token,
    is_field_scheme_kind,
    is_move_scheme_kind,
    LAYER_TITLE_NEW,
    ELEMENT_COUNT_NEW,
    FIELD_SCHEME_KIND as FIELD_SCHEME_KIND_NEW,
    MOVE_SCHEME_KIND as MOVE_SCHEME_KIND_NEW,
    SNAP_SCHEME_KIND,
    is_snap_scheme_kind,
)


try:
    from .scheme_bundle import (
        BUNDLE_KIND,
        is_scheme_bundle,
        make_bundle,
        bundle_libraries,
        LIB_SNAP,
        LIB_FIELD,
        LIB_MOVE,
        PLUGIN_VERSION,
    )
except ImportError:
    from scheme_bundle import (
        BUNDLE_KIND,
        is_scheme_bundle,
        make_bundle,
        bundle_libraries,
        LIB_SNAP,
        LIB_FIELD,
        LIB_MOVE,
        PLUGIN_VERSION,
    )

DISPLAY_NAME = 'Spatial Match & Topo Adjust'
# Categorized row title: clear rose, not a warning / error red.
_CAT_TITLE_COLOR = QColor('#c2185b')
_CAT_TITLE_COLOR_SELECTED = QColor('#ffffff')


class _CategoryMarkDelegate(QStyledItemDelegate):
    """有分类的图层：行前 ◆◆ 与标题加粗，色为 #c2185b；选中行可反白。"""

    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        has = bool(index.data(ROLE_HAS_CATS))
        text = opt.text or ''
        opt.text = ''
        widget = opt.widget
        style = widget.style() if widget is not None else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, widget)
        painter.save()
        rect = opt.rect.adjusted(6, 0, -4, 0)
        fm = opt.fontMetrics
        selected = bool(opt.state & QStyle.StateFlag.State_Selected)
        if has:
            font = QFont(opt.font)
            font.setBold(True)
            painter.setFont(font)
            fm = painter.fontMetrics()
            painter.setPen(_CAT_TITLE_COLOR_SELECTED if selected else _CAT_TITLE_COLOR)
            painter.drawText(rect, int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft), CAT_MARK)
            rect = rect.adjusted(fm.horizontalAdvance(CAT_MARK + ' '), 0, 0, 0)
            painter.setPen(_CAT_TITLE_COLOR_SELECTED if selected else _CAT_TITLE_COLOR)
        else:
            painter.setPen(QColor('#ffffff') if selected else QColor('#212529'))
        shown = fm.elidedText(text, Qt.TextElideMode.ElideRight, max(rect.width(), 0))
        painter.drawText(rect, int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft), shown)
        painter.restore()

    def sizeHint(self, option, index):
        hint = super().sizeHint(option, index)
        if index.data(ROLE_HAS_CATS):
            hint.setWidth(hint.width() + option.fontMetrics.horizontalAdvance(CAT_MARK + ' '))
        return hint


class CDETDialog(QDialog):
    METERS_PER_DEGREE = 111320.0
    SNAP_SCHEME_CUSTOM = '__custom__'
    FIELD_SCHEME_CUSTOM = '__field_custom__'
    FIELD_SCHEME_KIND = FIELD_SCHEME_KIND_NEW
    MOVE_SCHEME_CUSTOM = '__move_custom__'
    MOVE_SCHEME_KIND = MOVE_SCHEME_KIND_NEW
    UNGROUPED_KEY = '__ungrouped__'
    _SNAP_REF_FILT_CACHE_UNSET = object()

    def __init__(self, iface, core, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.core = core
        self.project = QgsProject.instance()
        self.settings = QgsSettings()
        self.is_geographic = True
        self._ui_mode = 'snap'
        self._cat_move = {'target': {}, 'ref': {}}
        self._move_tol = None
        self._shared_sf_tol = None
        self._move_preview_layer_ids = []
        self._restore_field_named = None
        self._restore_field_ref = None
        self._restore_field_spatial = None
        self._restore_field_multi = None
        self._restore_snap_spatial = None
        self._restore_snap_ref_mode = None
        self._line_length_rule = {'kind': 'le', 'threshold': 0.0}
        self._mode_params = {}
        self._special_values = special_defaults()
        self._special_form_key = None
        self._snap_count_rule = {'kind': 'le', 'threshold': 0.0}
        self._count_attach = 'endpoint'
        self._count_output_mates = False
        self._field_group_path_target = ''
        self._field_group_path_ref = ''
        self._field_target_geom = None
        self._field_ref_geom = None
        self._count_rule = default_element_count_rule()
        self._last_non_count_ref_index = 0
        self._ref_combo_populating = False
        self._snap_schemes = {}
        self._snap_group_orders = {}
        self._active_snap_scheme = self.SNAP_SCHEME_CUSTOM
        self._field_schemes = {}
        self._active_field_scheme = self.FIELD_SCHEME_CUSTOM
        self._field_scheme_loading = False
        self._move_schemes = {}
        self._active_move_scheme = self.MOVE_SCHEME_CUSTOM
        self._move_scheme_loading = False
        self._move_batch_continue = True
        self._restore_move_mode = None
        self._invalid_move_mode = None
        self._last_move_import_skips = []
        self._cat_snap = {'target': {}, 'ref': {}}
        self._cat_field = {'target': {}, 'ref': {}}
        self._restore_end_head_ref = None
        self._restore_end_head_named = None
        self._restore_end_tail_ref = None
        self._restore_end_tail_named = None
        self._i18n_raw = True
        self.init_ui()
        self.bind_signals()
        self.load_all_layers()
        self.load_settings()
        self._i18n_raw = False
        stamp_tree(self)
        # The composed window title is not one catalog key. Set it after stamping.
        self.setProperty("titleMsgid", None)
        # init_ui runs before the language is applied, so controls that already
        # stored a msgid kept the Chinese source. Manual switching repaints them;
        # do that same repaint once before the window is shown.
        retranslate_tree(self)
        self._sync_mode_toggle_text()
        language_changed().connect(self._on_language_changed)

    def tr(self, text):
        if getattr(self, '_i18n_raw', False):
            return text
        return _i18n_tr(text)

    def _make_section_title(self, icon_name, msgid):
        try:
            from .icons import load_icon
        except ImportError:
            from icons import load_icon
        host = QWidget()
        lay = QHBoxLayout(host)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        ic = QLabel()
        pix = load_icon(icon_name).pixmap(18, 18)
        if not pix.isNull():
            ic.setPixmap(pix)
        ic.setFixedSize(18, 18)
        lab = QLabel(self.tr(msgid))
        lab.setObjectName('title')
        lab.setProperty('msgid', msgid)
        lab.setWordWrap(True)
        lab.setMinimumWidth(0)
        lab.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        lab.setToolTip(self.tr(msgid))
        lay.addWidget(ic, 0)
        lay.addWidget(lab, 1)
        host.setFixedHeight(44)
        host.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return host, lab

    def _set_title_text(self, label, msgid):
        if label is None:
            return
        label.setText(self.tr(msgid))
        label.setProperty('msgid', msgid)
        label.setWordWrap(True)
        label.setMinimumWidth(0)
        label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        label.setToolTip(self.tr(msgid))

    def _show_help(self):
        try:
            from .help_dialog import HelpDialog
        except ImportError:
            from help_dialog import HelpDialog
        run_dialog(HelpDialog(self))

    def init_ui(self):
        self.setWindowTitle(DISPLAY_NAME)
        self.setMinimumSize(640, 560)
        self.resize(700, 650)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        try:
            self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
        except Exception:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)

        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
            QGroupBox {
                font-size: 12px;
                font-weight: bold;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 14px;
                background-color: rgba(255,255,255,0.7);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #212529;
            }
            QCheckBox, QRadioButton {
                font-size: 11px;
                color: #495057;
                spacing: 6px;
            }
            QCheckBox:hover, QRadioButton:hover {
                color: #228be6;
            }
            QLabel {
                font-size: 11px;
                color: #495057;
            }
            QLabel#title {
                font-size: 13px;
                font-weight: bold;
                color: #212529;
            }
            QLabel#meterHint {
                font-size: 10px;
                color: #868e96;
                font-style: italic;
            }
            QListWidget {
                font-size: 11px;
                color: #212529;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 4px;
                background-color: #ffffff;
                selection-background-color: #339af0;
                selection-color: #ffffff;
                outline: none;
            }
            QListWidget::item {
                padding: 3px 6px;
                border-radius: 3px;
            }
            QListWidget::item:hover {
                background-color: #e7f5ff;
            }
            QListWidget::item:selected {
                background-color: #339af0;
            }
            QListWidget#layerColumnList {
                font-size: 11px;
                color: #212529;
                border: none;
                border-radius: 0px;
                padding: 4px;
                background-color: #ffffff;
                selection-background-color: #339af0;
                selection-color: #ffffff;
                outline: none;
            }
            QListWidget#layerColumnList::item {
                padding: 3px 6px;
                border-radius: 3px;
            }
            QListWidget#layerColumnList::item:hover {
                background-color: #e7f5ff;
            }
            QListWidget#layerColumnList::item:selected {
                background-color: #339af0;
            }
            QPushButton {
                font-size: 13px;
                font-weight: 500;
                color: #ffffff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #339af0, stop:1 #228be6);
                border: none;
                border-radius: 5px;
                padding: 3px 6px;
                min-width: 0px;
            }
            QPushButton#schemeAddBtn, QPushButton#schemeViewBtn, QPushButton#schemeQuickBtn,
            QPushButton#schemeManageMainBtn, QPushButton#fieldAddBtn, QPushButton#fieldViewBtn,
            QPushButton#moveAddBtn, QPushButton#moveViewBtn {
                padding: 0px 8px;
                min-height: 0px;
                max-height: 28px;
            }
            QPushButton#iconToolBtn {
                background: transparent;
                border: 1px solid transparent;
                min-width: 28px;
                max-width: 16777215px;
                min-height: 28px;
                max-height: 32px;
                padding: 2px;
                border-radius: 4px;
            }
            QPushButton#iconToolBtn:hover {
                background: rgba(33, 37, 41, 0.10);
                border: 1px solid rgba(33, 37, 41, 0.18);
            }
            QPushButton#iconToolBtn:pressed {
                background: rgba(21, 101, 192, 0.22);
                border: 1px solid rgba(21, 101, 192, 0.45);
            }
            QPushButton#iconToolBtn:checked {
                background: rgba(21, 101, 192, 0.20);
                border: 1px solid rgba(21, 101, 192, 0.55);
            }
            QPushButton#iconToolBtn:disabled {
                background: rgba(33, 37, 41, 0.04);
                border: 1px solid transparent;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #228be6, stop:1 #1c7ed6);
            }
            QPushButton:pressed {
                background: #1971c2;
            }
            QPushButton:disabled {
                background: #adb5bd;
            }
            QPushButton#filterBtn {
                background: transparent;
                border: 1px solid transparent;
                font-size: 13px;
                padding: 2px;
                min-width: 32px;
                min-height: 32px;
                max-height: 32px;
                border-radius: 4px;
            }
            QPushButton#filterBtn:hover {
                background: rgba(33, 37, 41, 0.10);
                border: 1px solid rgba(33, 37, 41, 0.18);
            }
            QPushButton#filterBtn:pressed {
                background: rgba(21, 101, 192, 0.22);
                border: 1px solid rgba(21, 101, 192, 0.45);
            }
            QPushButton#filterBtn:checked {
                background: rgba(21, 101, 192, 0.20);
                border: 1px solid rgba(21, 101, 192, 0.55);
            }
            QPushButton#filterBtn:disabled {
                background: rgba(33, 37, 41, 0.05);
                border: 1px dashed rgba(33, 37, 41, 0.28);
            }
            QToolButton#layerFilterBtn {
                background: transparent;
                border: 1px solid transparent;
                padding: 2px 1px 1px 1px;
                min-width: 36px;
                min-height: 48px;
                max-height: 48px;
                border-radius: 4px;
            }
            QToolButton#layerFilterBtn:hover {
                background: rgba(33, 37, 41, 0.10);
                border: 1px solid rgba(33, 37, 41, 0.18);
            }
            QToolButton#layerFilterBtn:pressed {
                background: rgba(21, 101, 192, 0.22);
                border: 1px solid rgba(21, 101, 192, 0.45);
            }
            QToolButton#layerFilterBtn:checked {
                background: rgba(21, 101, 192, 0.20);
                border: 1px solid rgba(21, 101, 192, 0.55);
            }
            QToolButton#layerFilterBtn:disabled {
                background: rgba(33, 37, 41, 0.05);
                border: 1px dashed rgba(33, 37, 41, 0.28);
            }
            QFrame#layerColumnFrame {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background-color: rgba(255,255,255,0.7);
            }
            QPushButton#schemeQuickBtn {
                font-size: 12px;
                font-weight: 600;
                padding: 3px 4px;
                min-width: 0px;
                min-height: 28px;
                max-height: 28px;
                border-radius: 6px;
                color: #ffffff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8b9cff, stop:0.5 #748ffc, stop:1 #5c7cfa);
                border: 1px solid #4c6ef5;
            }
            QPushButton#schemeQuickBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #aeb8ff, stop:1 #748ffc);
                border: 1px solid #5c7cfa;
            }
            QPushButton#schemeQuickBtn:pressed {
                background: #4263eb;
                border: 1px solid #364fc7;
            }
            QPushButton#schemeQuickBtn:disabled {
                background: #adb5bd;
                border: 1px solid #868e96;
                color: #f1f3f5;
            }
            QPushButton#schemeAddBtn {
                font-size: 12px;
                font-weight: 600;
                padding: 3px 4px;
                min-width: 0px;
                min-height: 28px;
                max-height: 28px;
                border-radius: 6px;
                color: #ffffff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #12b886, stop:0.5 #0ca678, stop:1 #099268);
                border: 1px solid #087f5b;
            }
            QPushButton#schemeAddBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #38d9a9, stop:1 #20c997);
                border: 1px solid #0ca678;
            }
            QPushButton#schemeAddBtn:pressed {
                background: #087f5b;
                border: 1px solid #06614a;
            }
            QPushButton#schemeAddBtn:disabled {
                background: #adb5bd;
                border: 1px solid #868e96;
                color: #f1f3f5;
            }
            QPushButton#schemeViewBtn {
                font-size: 12px;
                font-weight: 600;
                padding: 3px 4px;
                min-width: 0px;
                min-height: 28px;
                max-height: 28px;
                border-radius: 6px;
                color: #ffffff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4dabf7, stop:0.5 #339af0, stop:1 #228be6);
                border: 1px solid #1c7ed6;
            }
            QPushButton#schemeViewBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #74c0fc, stop:1 #339af0);
                border: 1px solid #228be6;
            }
            QPushButton#schemeViewBtn:pressed {
                background: #1971c2;
                border: 1px solid #1864ab;
            }
            QPushButton#schemeViewBtn:disabled {
                background: #adb5bd;
                border: 1px solid #868e96;
                color: #f1f3f5;
            }
            QPushButton#moveAddBtn {
                font-size: 12px;
                font-weight: 600;
                padding: 3px 4px;
                min-width: 0px;
                min-height: 28px;
                max-height: 28px;
                border-radius: 6px;
                color: #ffffff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #12b886, stop:0.5 #0ca678, stop:1 #099268);
                border: 1px solid #087f5b;
            }
            QPushButton#moveAddBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #38d9a9, stop:1 #20c997);
                border: 1px solid #0ca678;
            }
            QPushButton#moveAddBtn:pressed {
                background: #087f5b;
                border: 1px solid #06614a;
            }
            QPushButton#moveAddBtn:disabled {
                background: #adb5bd;
                border: 1px solid #868e96;
                color: #f1f3f5;
            }
            QPushButton#moveViewBtn {
                font-size: 12px;
                font-weight: 600;
                padding: 3px 4px;
                min-width: 0px;
                min-height: 28px;
                max-height: 28px;
                border-radius: 6px;
                color: #ffffff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4dabf7, stop:0.5 #339af0, stop:1 #228be6);
                border: 1px solid #1c7ed6;
            }
            QPushButton#moveViewBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #74c0fc, stop:1 #339af0);
                border: 1px solid #228be6;
            }
            QPushButton#moveViewBtn:pressed {
                background: #1971c2;
                border: 1px solid #1864ab;
            }
            QPushButton#moveViewBtn:disabled {
                background: #ced4da;
                border: 1px solid #adb5bd;
                color: #f8f9fa;
            }
            QPushButton#schemeManageMainBtn {
                font-size: 12px;
                font-weight: 600;
                padding: 3px 4px;
                min-width: 0px;
                min-height: 28px;
                max-height: 28px;
                border-radius: 6px;
                color: #ffffff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7c6bcf, stop:0.5 #6741d9, stop:1 #5f3dc4);
                border: 1px solid #4c2fc4;
            }
            QPushButton#schemeManageMainBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #9775fa, stop:1 #7950f2);
                border: 1px solid #6741d9;
            }
            QPushButton#schemeManageMainBtn:pressed {
                background: #4c2fc4;
                border: 1px solid #3d248f;
            }
            QPushButton#schemeManageMainBtn:disabled {
                background: #adb5bd;
                border: 1px solid #868e96;
                color: #f1f3f5;
            }
            QPushButton#schemeImportBtn {
                font-size: 13px;
                font-weight: 600;
                padding: 3px 10px;
                min-height: 27px;
                max-height: 27px;
                border-radius: 6px;
                color: #ffffff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2bb3a8, stop:0.5 #1fa89e, stop:1 #0d9488);
                border: 1px solid #0f766e;
            }
            QPushButton#schemeImportBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5eead4, stop:1 #14b8a6);
                border: 1px solid #0d9488;
            }
            QPushButton#schemeImportBtn:pressed {
                background: #0f766e;
                border: 1px solid #115e59;
            }
            QPushButton#schemeImportBtn:disabled {
                background: #adb5bd;
                border: 1px solid #868e96;
                color: #f1f3f5;
            }
            QPushButton#schemeExportBtn {
                font-size: 13px;
                font-weight: 600;
                padding: 3px 10px;
                min-height: 27px;
                max-height: 27px;
                border-radius: 6px;
                color: #ffffff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffa94d, stop:0.5 #fd7e14, stop:1 #f76707);
                border: 1px solid #e8590c;
            }
            QPushButton#schemeExportBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffc078, stop:1 #fd7e14);
                border: 1px solid #f76707;
            }
            QPushButton#schemeExportBtn:pressed {
                background: #e8590c;
                border: 1px solid #d9480f;
            }
            QPushButton#schemeExportBtn:disabled {
                background: #adb5bd;
                border: 1px solid #868e96;
                color: #f1f3f5;
            }
            QPushButton#fieldAddBtn, QPushButton#fieldViewBtn {
                font-size: 12px;
                font-weight: 600;
                padding: 3px 8px;
                min-width: 0px;
                min-height: 28px;
                max-height: 28px;
                border-radius: 6px;
                color: #ffffff;
            }
            QPushButton#fieldAddBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #12b886, stop:1 #099268);
                border: 1px solid #087f5b;
            }
            QPushButton#fieldAddBtn:hover { background: #20c997; }
            QPushButton#fieldAddBtn:pressed { background: #087f5b; }
            QPushButton#fieldViewBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4dabf7, stop:1 #228be6);
                border: 1px solid #1c7ed6;
            }
            QPushButton#fieldViewBtn:hover { background: #339af0; }
            QPushButton#fieldViewBtn:pressed { background: #1971c2; }
            QPushButton#fieldAddBtn:disabled, QPushButton#fieldViewBtn:disabled {
                background: #adb5bd;
                border: 1px solid #868e96;
                color: #f1f3f5;
            }
            QPushButton#schemeManageBtn {
                font-size: 13px;
                font-weight: 600;
                padding: 3px 10px;
                min-width: 72px;
                min-height: 27px;
                max-height: 27px;
                border-radius: 6px;
                color: #f8f9fa;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5c8899, stop:0.5 #4a6f82, stop:1 #3d5a6b);
                border: 1px solid #2f4858;
            }
            QPushButton#schemeManageBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6d9fb3, stop:1 #526f80);
                border: 1px solid #3d5a6b;
            }
            QPushButton#schemeManageBtn:pressed {
                background: #2f4858;
                border: 1px solid #263238;
            }
            QPushButton#schemeManageBtn:disabled {
                background: #adb5bd;
                border: 1px solid #868e96;
                color: #e9ecef;
            }
            QPushButton#schemeDeleteBtn {
                font-size: 10px;
                font-weight: 600;
                padding: 4px 10px;
                min-width: 72px;
                min-height: 30px;
                border-radius: 6px;
                color: #ffffff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e57474, stop:0.5 #d94848, stop:1 #c92a2a);
                border: 1px solid #a61e1e;
            }
            QPushButton#schemeDeleteBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f09090, stop:1 #e03131);
                border: 1px solid #c92a2a;
            }
            QPushButton#schemeDeleteBtn:pressed {
                background: #a61e1e;
                border: 1px solid #862e2e;
            }
            QPushButton#schemeDeleteBtn:disabled {
                background: #adb5bd;
                border: 1px solid #868e96;
                color: #f1f3f5;
            }
            QPushButton#executeBtn,
            QPushButton#refreshBtn,
            QPushButton#modeToggleBtn {
                font-size: 13px;
                font-weight: bold;
                min-height: 50px;
                max-height: 50px;
                padding: 0px 6px;
                border-radius: 6px;
            }
            QPushButton#bottomClearBtn,
            QPushButton#bottomCloseBtn {
                font-size: 13px;
                font-weight: bold;
                min-height: 28px;
                max-height: 28px;
                padding: 2px 6px;
                border-radius: 6px;
            }
            QPushButton#executeBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #51cf66, stop:1 #2f9e44);
                color: #ffffff;
            }
            QPushButton#executeBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #40c057, stop:1 #37b24d);
            }
            QPushButton#refreshBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffd43b, stop:1 #fab005);
                color: #212529;
            }
            QPushButton#refreshBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fcc419, stop:1 #f59f00);
            }
            QPushButton#bottomClearBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff8787, stop:1 #fa5252);
                color: #ffffff;
            }
            QPushButton#bottomClearBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fa5252, stop:1 #e03131);
            }
            QPushButton#bottomCloseBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #adb5bd, stop:1 #868e96);
                color: #ffffff;
            }
            QPushButton#bottomCloseBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #868e96, stop:1 #495057);
            }
            QPushButton#modeToggleBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #9775fa, stop:1 #7048e8);
                color: #ffffff;
            }
            QPushButton#modeToggleBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #845ef7, stop:1 #5f3dc4);
            }
            QDoubleSpinBox {
                font-size: 11px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 1px 6px;
                background-color: #ffffff;
                min-width: 64px;
            }
            QDoubleSpinBox:focus {
                border-color: #339af0;
            }
        """)

        outer_vertical = QVBoxLayout(self)
        outer_vertical.setContentsMargins(0, 0, 0, 0)
        outer_vertical.setSpacing(0)
        columns_panel = QWidget()
        columns_panel.setMinimumWidth(480)
        columns_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        columns_layout = QHBoxLayout(columns_panel)
        self._columns_layout = columns_layout
        columns_layout.setContentsMargins(0, 0, 0, 0)
        columns_layout.setSpacing(0)
        outer_vertical.addWidget(columns_panel, 1)

        layer_group = QWidget()
        layer_main = QVBoxLayout(layer_group)
        layer_main.setContentsMargins(6, 6, 6, 6)
        layer_main.setSpacing(6)

        lists_layout = QGridLayout()
        self._lists_layout = lists_layout
        lists_layout.setHorizontalSpacing(8)
        lists_layout.setVerticalSpacing(6)
        lists_layout.setColumnStretch(0, 1)
        lists_layout.setColumnStretch(1, 1)

        self.w_target_title, self.lbl_target_title = self._make_section_title(
            'title_target', '判断图层（输出来源）'
        )
        self.target_layer_list = QListWidget()
        self.target_layer_list.setObjectName('layerColumnList')
        self.target_layer_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.target_layer_list.setMinimumHeight(200)
        self.target_layer_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.target_filter_stack = QStackedWidget()
        snap_target_btns = QWidget()
        left_btns = QHBoxLayout(snap_target_btns)
        left_btns.setContentsMargins(0, 0, 0, 0)
        left_btns.setSpacing(4)
        self.target_btn_point = QToolButton()
        self.target_btn_line = QToolButton()
        self.target_btn_polygon = QToolButton()
        self.target_btn_all = QToolButton()
        for btn, kind, name in (
            (self.target_btn_point, 'point', '点'),
            (self.target_btn_line, 'line', '线'),
            (self.target_btn_polygon, 'polygon', '面'),
            (self.target_btn_all, 'all', '全部'),
        ):
            style_filter_button(btn, kind, name)
            left_btns.addWidget(btn, 1)
        field_target_btns = QWidget()
        fl_t = QHBoxLayout(field_target_btns)
        fl_t.setContentsMargins(0, 0, 0, 0)
        fl_t.setSpacing(4)
        self.field_tgt_btn_point = QToolButton()
        self.field_tgt_btn_line = QToolButton()
        self.field_tgt_btn_polygon = QToolButton()
        self.field_tgt_btn_group = QToolButton()
        for btn, kind, name in (
            (self.field_tgt_btn_point, 'point', '点'),
            (self.field_tgt_btn_line, 'line', '线'),
            (self.field_tgt_btn_polygon, 'polygon', '面'),
            (self.field_tgt_btn_group, 'group', '图层组'),
        ):
            style_filter_button(btn, kind, name)
            fl_t.addWidget(btn, 1)
        self.target_filter_stack.addWidget(snap_target_btns)
        self.target_filter_stack.addWidget(field_target_btns)

        self.ref_layer_list = QListWidget()
        self.ref_layer_list.setObjectName('layerColumnList')
        self.ref_layer_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.ref_layer_list.setMinimumHeight(200)
        self.ref_layer_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._cat_delegate = _CategoryMarkDelegate(self)
        self.target_layer_list.setItemDelegate(self._cat_delegate)
        self.ref_layer_list.setItemDelegate(self._cat_delegate)

        self.ref_filter_stack = QStackedWidget()
        snap_ref_btns = QWidget()
        right_btns = QHBoxLayout(snap_ref_btns)
        right_btns.setContentsMargins(0, 0, 0, 0)
        right_btns.setSpacing(4)
        self.ref_btn_point = QToolButton()
        self.ref_btn_line = QToolButton()
        self.ref_btn_polygon = QToolButton()
        self.ref_btn_all = QToolButton()
        for btn, kind, name in (
            (self.ref_btn_point, 'point', '点'),
            (self.ref_btn_line, 'line', '线'),
            (self.ref_btn_polygon, 'polygon', '面'),
            (self.ref_btn_all, 'all', '全部'),
        ):
            style_filter_button(btn, kind, name)
            right_btns.addWidget(btn, 1)
        field_ref_btns = QWidget()
        fl_r = QHBoxLayout(field_ref_btns)
        fl_r.setContentsMargins(0, 0, 0, 0)
        fl_r.setSpacing(4)
        self.field_ref_btn_point = QToolButton()
        self.field_ref_btn_line = QToolButton()
        self.field_ref_btn_polygon = QToolButton()
        self.field_ref_btn_group = QToolButton()
        for btn, kind, name in (
            (self.field_ref_btn_point, 'point', '点'),
            (self.field_ref_btn_line, 'line', '线'),
            (self.field_ref_btn_polygon, 'polygon', '面'),
            (self.field_ref_btn_group, 'group', '图层组'),
        ):
            style_filter_button(btn, kind, name)
            fl_r.addWidget(btn, 1)
        self.ref_filter_stack.addWidget(snap_ref_btns)
        self.ref_filter_stack.addWidget(field_ref_btns)

        self.snap_right_stack = QStackedWidget()
        self.page_snap_ref_layers = QWidget()
        _psr = QVBoxLayout(self.page_snap_ref_layers)
        _psr.setContentsMargins(0, 0, 0, 0)
        _psr.setSpacing(0)
        self.page_polygon_outputs = QWidget()
        _ppo = QVBoxLayout(self.page_polygon_outputs)
        _ppo.setContentsMargins(0, 0, 0, 0)
        _ppo.setSpacing(4)
        self.lbl_polygon_stack_title = QLabel()
        self.lbl_polygon_stack_title.setObjectName('title')
        self.lbl_polygon_stack_title.setVisible(False)
        _ppo.addWidget(self.lbl_polygon_stack_title)
        self.list_polygon_outputs = QListWidget()
        self.list_polygon_outputs.setObjectName('layerColumnList')
        self.list_polygon_outputs.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        _ppo.addWidget(self.list_polygon_outputs, 1)
        _row_po = QHBoxLayout()
        self.btn_polygon_out_all = QPushButton(self.tr('全选输出'))
        self.btn_polygon_out_none = QPushButton(self.tr('全不选'))
        for _b in (self.btn_polygon_out_all, self.btn_polygon_out_none):
            _b.setObjectName('filterBtn')
        _row_po.addWidget(self.btn_polygon_out_all)
        _row_po.addWidget(self.btn_polygon_out_none)
        _row_po.addStretch(1)
        _ppo.addLayout(_row_po)
        _psr.addWidget(self.ref_layer_list, 1)
        self.snap_right_stack.addWidget(self.page_snap_ref_layers)
        self.snap_right_stack.addWidget(self.page_polygon_outputs)

        self.w_snap_mode_preset, self.lbl_snap_ref_title = self._make_section_title(
            'title_ref', '参考图层'
        )
        self.lbl_snap_ref_title.setWordWrap(False)
        self.lbl_snap_ref_title.setMinimumWidth(0)
        self.lbl_snap_ref_title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        row_snap_ref_way = self.w_snap_mode_preset.layout()
        self.combo_snap_ref_mode = QComboBox()
        self.combo_snap_ref_mode.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo_snap_ref_mode.setMinimumWidth(48)
        self.combo_snap_ref_mode.setMaximumWidth(16777215)
        row_snap_ref_way.addWidget(self.combo_snap_ref_mode, 1)
        self.w_snap_special_extra = QWidget()
        _spl = QVBoxLayout(self.w_snap_special_extra)
        _spl.setContentsMargins(0, 0, 0, 0)
        _spl.setSpacing(4)
        self.w_poly_extra = QWidget()
        _poly_l = QHBoxLayout(self.w_poly_extra)
        _poly_l.setContentsMargins(0, 0, 0, 0)
        _poly_l.setSpacing(6)
        _poly_l.addWidget(QLabel(self.tr('面检测')), 0)
        _poly_hint = QLabel(self.tr('重叠/孔洞/空隙面积阈值(㎡，默认1）'))
        _poly_hint.setWordWrap(True)
        _poly_l.addWidget(_poly_hint)
        self.spin_overlap_area_tol = QDoubleSpinBox()
        self.spin_overlap_area_tol.setRange(0.000001, 1e15)
        self.spin_overlap_area_tol.setDecimals(6)
        self.spin_overlap_area_tol.setSingleStep(0.01)
        self.spin_overlap_area_tol.setValue(1.0)
        _poly_l.addWidget(self.spin_overlap_area_tol)
        self.w_poly_extra.setVisible(False)
        _spl.addWidget(self.w_poly_extra)

        self.w_line_extra = QWidget()
        _le = QHBoxLayout(self.w_line_extra)
        _le.setContentsMargins(0, 0, 0, 0)
        self.lbl_line_extra_title = QLabel(self.tr('线长规则'))
        _le.addWidget(self.lbl_line_extra_title)
        self.lbl_line_rule_summary = QLabel()
        self.lbl_line_rule_summary.setWordWrap(True)
        _le.addWidget(self.lbl_line_rule_summary, 1)
        self.btn_line_length_rule = QPushButton(self.tr('编辑…'))
        self.btn_line_length_rule.setObjectName('filterBtn')
        _le.addWidget(self.btn_line_length_rule)
        self.w_line_extra.setVisible(False)
        _spl.addWidget(self.w_line_extra)

        self.w_count_attach_extra = QWidget()
        _ca = QVBoxLayout(self.w_count_attach_extra)
        _ca.setContentsMargins(0, 0, 0, 0)
        _ca.setSpacing(4)
        _ca_row = QHBoxLayout()
        _ca_row.addWidget(QLabel(self.tr('挂接位置')))
        self.combo_count_attach = QComboBox()
        self.combo_count_attach.addItem(self.tr('端点（默认）'), 'endpoint')
        self.combo_count_attach.addItem(self.tr('任意折点'), 'vertex')
        self.combo_count_attach.addItem(self.tr('沿线身'), 'along')
        self.combo_count_attach.setToolTip(
            self.tr(
                '点与线怎样才算「连上」（距离都按吸附容差）：\n'
                '端点＝点贴着线头或线尾；\n'
                '任意折点＝点贴着线上任一顶点（端点或中间拐点）；\n'
                '沿线身＝点贴着线上任意位置，不必在顶点上。\n'
                '1.0 版方案没有这一项时按「端点」处理。'
            )
        )
        _ca_row.addWidget(self.combo_count_attach, 1)
        _ca.addLayout(_ca_row)
        self.chk_count_output_mates = QCheckBox(self.tr('同时输出对端要素'))
        self.chk_count_output_mates.setToolTip(
            self.tr(
                '除了输出筛选出的要素，再把跟它连上的对方要素也输出成一个图层：\n'
                '「点上接了几条线」额外输出这些线；「线上挂了几个点」额外输出这些点。'
            )
        )
        _ca.addWidget(self.chk_count_output_mates)
        self.w_count_attach_extra.setVisible(False)
        _spl.addWidget(self.w_count_attach_extra)

        self.w_overlap_hint = QWidget()
        _oh = QVBoxLayout(self.w_overlap_hint)
        _oh.setContentsMargins(0, 0, 0, 0)
        _oh.setSpacing(4)
        _row_os = QHBoxLayout()
        self.combo_overlap_scope = QComboBox()
        self.combo_overlap_scope.setToolTip(
            self.tr(
                '四种组合（2×2）：\n'
                '「单独判断」= 各图层内部分别算重叠；「集合判断」= 同几何类型的多图层合并后统一配对'
                '（线仅与线、面仅与面；选「自动」时按点、线、面各跑一轮）。线/面重叠以「顶点在吸附容差下是否一致」判定。\n'
                '「单独输出」= 命中按图层拆成多个临时图层；「集合输出」= 所有命中写入一个临时图层。'))
        self.combo_overlap_scope.addItem(self.tr('单独判断 + 单独输出'), 'per_layer')
        self.combo_overlap_scope.addItem(self.tr('单独判断 + 集合输出'), 'merged_concat')
        self.combo_overlap_scope.addItem(self.tr('集合判断 + 单独输出'), 'group_per_layer')
        self.combo_overlap_scope.addItem(self.tr('集合判断 + 集合输出'), 'merged_group')
        _row_os.addWidget(self.combo_overlap_scope, 1)
        _oh.addLayout(_row_os)
        self.w_overlap_hint.setVisible(False)
        _spl.addWidget(self.w_overlap_hint)

        self.w_chain_extra = QWidget()
        _ch = QHBoxLayout(self.w_chain_extra)
        _ch.setContentsMargins(0, 0, 0, 0)
        _ch.addWidget(QLabel(self.tr('点线链：最小段数（≥）')))
        self.spin_chain_min_seg = QSpinBox()
        self.spin_chain_min_seg.setRange(1, 100000)
        self.spin_chain_min_seg.setValue(3)
        self.spin_chain_min_seg.setToolTip(
            self.tr('沿端点相接的线链行走，累计段数；仅支持「≥」规则；配合下方「提取已吸附」筛选命中/未命中。'),
        )
        _ch.addWidget(self.spin_chain_min_seg)
        _ch.addStretch(1)
        self.w_chain_extra.setVisible(False)
        _spl.addWidget(self.w_chain_extra)

        self.w_line_overlap_extra = QWidget()
        _lo = QHBoxLayout(self.w_line_overlap_extra)
        _lo.setContentsMargins(0, 0, 0, 0)
        _lo.addWidget(QLabel(self.tr('最短重叠（米）')))
        self.spin_line_overlap_min = QDoubleSpinBox()
        self.spin_line_overlap_min.setRange(0.0, 1e7)
        self.spin_line_overlap_min.setDecimals(2)
        self.spin_line_overlap_min.setSingleStep(1.0)
        self.spin_line_overlap_min.setValue(1.0)
        self.spin_line_overlap_min.setToolTip(
            self.tr(
                '两线贴在一起的长度达到该值才输出中心点。'
                '从一个点往各方向分开不算。'
                '图里那种只在节点分叉的，把这个值调大可以再压掉误报。'
            ),
        )
        _lo.addWidget(self.spin_line_overlap_min)
        _lo.addStretch(1)
        self.w_line_overlap_extra.setVisible(False)
        _spl.addWidget(self.w_line_overlap_extra)

        self.w_quality_extra = QWidget()
        self._quality_extra_lay = QVBoxLayout(self.w_quality_extra)
        self._quality_extra_lay.setContentsMargins(0, 0, 0, 0)
        self.w_quality_extra.setVisible(False)
        _spl.addWidget(self.w_quality_extra)

        self.right_header_stack = QStackedWidget()
        self.w_field_ref_header, self.lbl_ref_title = self._make_section_title(
            'title_ref', '参考图层'
        )
        self.right_header_stack.addWidget(self.w_snap_mode_preset)
        self.right_header_stack.addWidget(self.w_field_ref_header)
        self.w_move_ref_header, self.lbl_move_ref_title = self._make_section_title(
            'title_ref', '参考图层'
        )
        self.right_header_stack.addWidget(self.w_move_ref_header)

        self.w_snap_layer_right_wrap = QWidget()
        _rw = QVBoxLayout(self.w_snap_layer_right_wrap)
        _rw.setContentsMargins(0, 0, 0, 0)
        _rw.setSpacing(6)
        _rw.addWidget(self.w_snap_special_extra)
        _rw.addWidget(self.snap_right_stack, 1)

        self.frame_left_col = QFrame()
        self.frame_left_col.setObjectName('layerColumnFrame')
        self.frame_left_col.setFrameShape(QFrame.Shape.NoFrame)
        _fl = QVBoxLayout(self.frame_left_col)
        _fl.setContentsMargins(8, 8, 8, 8)
        _fl.setSpacing(6)
        _fl.addWidget(self.w_target_title)
        _fl.addWidget(self.target_layer_list, 1)
        _fl.addWidget(self.target_filter_stack)

        self.frame_right_col = QFrame()
        self.frame_right_col.setObjectName('layerColumnFrame')
        self.frame_right_col.setFrameShape(QFrame.Shape.NoFrame)
        _fr = QVBoxLayout(self.frame_right_col)
        _fr.setContentsMargins(8, 8, 8, 8)
        _fr.setSpacing(6)
        _fr.addWidget(self.right_header_stack)
        _fr.addWidget(self.w_snap_layer_right_wrap, 1)
        _fr.addWidget(self.ref_filter_stack)

        lists_layout.addWidget(self.frame_left_col, 0, 0)
        lists_layout.addWidget(self.frame_right_col, 0, 1)
        lists_layout.setRowStretch(0, 1)
        layer_main.addLayout(lists_layout, 1)

        columns_layout.addWidget(layer_group, 5)

        self.options_group = QGroupBox(self.tr('吸附选项'))
        options_outer = QVBoxLayout(self.options_group)
        options_outer.setContentsMargins(8, 4, 8, 4)
        options_outer.setSpacing(0)
        self.mid_scroll = QScrollArea()
        self.mid_scroll.setWidgetResizable(True)
        self.mid_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.mid_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.mid_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mid_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        try:
            self.mid_scroll.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored)
        except Exception:  # nosec B110
            pass
        self.mid_inner = QWidget()
        options_layout = QVBoxLayout(self.mid_inner)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(4)

        self.lbl_tol = QLabel(self.tr('容差'))
        style_param_label(self.lbl_tol, '容差', '容差')
        self.lbl_batch_scheme = QLabel()
        style_param_label(self.lbl_batch_scheme, '批量方案', '批量方案')
        self.spin_tolerance = QDoubleSpinBox()
        self.spin_tolerance.setDecimals(6)
        self.spin_tolerance.setMinimum(0.000001)
        self.spin_tolerance.setMaximum(10000.0)
        self.spin_tolerance.setValue(0.00001)
        self.spin_tolerance.setSingleStep(0.000001)
        self.spin_tolerance.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_tolerance.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.lbl_unit = QLabel(self.tr('度'))
        self.lbl_meter_hint = QLabel(self.tr('(≈1.11m)'))
        self.lbl_meter_hint.setObjectName('meterHint')
        self.lbl_meter_hint.setWordWrap(True)
        self.lbl_meter_hint.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.chk_snap = QCheckBox(self.tr('提取已吸附'))
        self.chk_snap.setProperty('msgid', '提取已吸附')
        self._snap_chk_tip_standard = self.tr(
            '标准模式：勾选＝输出命中参考的要素；不勾选＝输出未命中参考的要素。',
        )
        self.chk_snap.setToolTip(self._snap_chk_tip_standard)
        self.btn_scheme_add = QPushButton()
        self.btn_scheme_add.setObjectName('schemeAddBtn')
        self.lbl_field_output = QLabel()
        style_param_label(self.lbl_field_output, '输出', '输出')
        self.combo_field_output = QComboBox()
        self.combo_field_output.addItem(self.tr('直接修改图层'), 'direct')
        self.combo_field_output.addItem(self.tr('生成临时图层'), 'memory')
        self.combo_field_output.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo_field_output.setMinimumWidth(0)

        self.lbl_snap_sp = QLabel()
        style_param_label(self.lbl_snap_sp, '空间模式', '空间命名模式')
        self.combo_snap_spatial_mode = QComboBox()
        self.combo_snap_spatial_mode.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo_snap_spatial_mode.setMinimumWidth(0)
        self.combo_snap_spatial_mode.setToolTip(
            self.tr('与字段命名相同：按所选关系判断「是否命中参考」，用于筛选已/未命中要素。'))
        self.combo_snap_scheme = QComboBox()
        self.combo_snap_scheme.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo_snap_scheme.setMinimumWidth(0)
        self.chk_batch_continue = QCheckBox(self.tr('失败继续'))
        self.chk_batch_continue.setProperty('msgid', '失败继续')
        self.chk_batch_continue.setToolTip(self.tr('批量执行时，子任务失败后是否继续后续任务。'))
        self.chk_batch_continue.setProperty('tip', '批量执行时，子任务失败后是否继续后续任务。')
        self.chk_batch_continue.setChecked(True)

        self.btn_memory_style = QPushButton()
        self.btn_memory_style.setObjectName('schemeQuickBtn')
        self.btn_scheme_view = QPushButton()
        self.btn_scheme_view.setObjectName('schemeViewBtn')

        self.w_snap_options_block = QWidget()
        lay_snap_block_main = QHBoxLayout(self.w_snap_options_block)
        lay_snap_block_main.setContentsMargins(0, 0, 0, 0)
        lay_snap_block_main.setSpacing(10)

        self.w_tol_cluster = QWidget()
        lay_tol_cluster = QVBoxLayout(self.w_tol_cluster)
        self.lay_tol_cluster = lay_tol_cluster
        lay_tol_cluster.setContentsMargins(0, 0, 0, 0)
        lay_tol_cluster.setSpacing(1)
        lay_tol_cluster.addWidget(self.lbl_tol)
        _tol_ctrl = QHBoxLayout()
        _tol_ctrl.setContentsMargins(0, 0, 0, 0)
        _tol_ctrl.setSpacing(6)
        _tol_ctrl.addWidget(self.spin_tolerance, 0)
        _tol_ctrl.addWidget(self.lbl_unit, 0)
        _tol_ctrl.addWidget(self.lbl_meter_hint, 1)
        lay_tol_cluster.addLayout(_tol_ctrl)
        self.w_out_cluster = QWidget()
        lay_out_cluster = QVBoxLayout(self.w_out_cluster)
        lay_out_cluster.setContentsMargins(0, 0, 0, 0)
        lay_out_cluster.setSpacing(1)
        lay_out_cluster.addWidget(self.lbl_field_output)
        lay_out_cluster.addWidget(self.combo_field_output)
        self.lbl_field_output.setVisible(False)
        self.combo_field_output.setVisible(False)
        self.w_out_cluster.setVisible(False)

        self.w_tol_row = QWidget()
        self.w_tol_row.setVisible(False)
        self.lay_tol_row = QVBoxLayout(self.w_tol_row)
        self.lay_tol_row.setContentsMargins(0, 0, 0, 0)
        self.lay_tol_row.setSpacing(6)
        # w_tol_row is a compatibility host only. Do not nest 容差 / 输出
        # inside it — each mid parameter must be a sibling group.

        self.w_snap_left_inner = QWidget()
        self.lay_snap_left = QVBoxLayout(self.w_snap_left_inner)
        self.lay_snap_left.setContentsMargins(0, 0, 0, 0)
        self.lay_snap_left.setSpacing(6)
        self.w_snap_mid_top_pad = self._make_edge_pad('snap_mid_top_pad')
        self.lay_snap_left.addWidget(self.w_snap_mid_top_pad)
        self.lay_snap_left.addWidget(self.w_tol_cluster)
        self.row_snap_mode_param = ModeParamRow(on_changed=self._on_mode_param_changed)
        self.w_snap_spatial_block = param_block(self.lbl_snap_sp, self.combo_snap_spatial_mode)
        self.lay_snap_left.addWidget(self.chk_snap)
        self.lay_snap_left.addWidget(self.chk_batch_continue)
        self.lay_snap_left.addWidget(self.w_snap_spatial_block)
        self.lay_snap_left.addWidget(self.row_snap_mode_param)
        self.w_snap_batch_block = param_block(self.lbl_batch_scheme, self.combo_snap_scheme)
        self.lay_snap_left.addWidget(self.w_snap_batch_block)
        self.w_snap_mid_bottom_pad = self._make_edge_pad('snap_mid_bottom_pad')
        self.lay_snap_left.addWidget(self.w_snap_mid_bottom_pad)

        self.w_snap_ad_right = QWidget()
        self.w_snap_ad_right.setVisible(False)

        lay_snap_block_main.addWidget(self.w_snap_left_inner, 1)
        self.w_snap_left_inner.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._options_group_layout = options_layout
        options_layout.addWidget(self.w_snap_options_block)

        self.snap_options_extra = QWidget()
        snap_extra_layout = QVBoxLayout(self.snap_options_extra)
        snap_extra_layout.setContentsMargins(0, 0, 0, 0)
        snap_extra_layout.setSpacing(8)
        self.btn_scheme_manage = QPushButton(self.tr('📋 方案管理'))
        self.btn_scheme_manage.setObjectName('schemeManageMainBtn')
        self.btn_scheme_import = QPushButton(self.tr('📥 导入'))
        self.btn_scheme_import.setObjectName('schemeImportBtn')
        self.btn_scheme_export = QPushButton(self.tr('📤 导出'))
        self.btn_scheme_export.setObjectName('schemeExportBtn')
        self.btn_memory_style.setObjectName('schemeQuickBtn')
        self.w_snap_mid_actions = QWidget()
        self._style_action_btn(self.btn_scheme_add, '添加', '将当前图层与参数快照加入所选批量方案')
        self._style_action_btn(self.btn_scheme_view, '查看', '查看、编辑、删除、调整当前方案里的子任务')
        self._style_action_btn(self.btn_scheme_manage, '方案', '方案管理')
        self._style_action_btn(self.btn_memory_style, '样式', '配置临时点图层与线图层的默认符号（本地保存）')
        self._fill_mid_action_column(
            self.w_snap_mid_actions,
            (self.btn_scheme_add, self.btn_scheme_view,
             self.btn_scheme_manage, self.btn_memory_style),
        )
        snap_extra_layout.addWidget(self.w_snap_mid_actions)
        options_layout.insertWidget(0, self.snap_options_extra)

        self.field_options_extra = QWidget()
        field_outer = QVBoxLayout(self.field_options_extra)
        field_outer.setContentsMargins(0, 0, 0, 0)
        field_outer.setSpacing(2)
        self.field_grid = QGridLayout()
        self.field_grid.setContentsMargins(0, 0, 0, 0)
        self.field_grid.setHorizontalSpacing(10)
        self.field_grid.setVerticalSpacing(8)
        self.combo_named_field = QComboBox()
        self.combo_ref_field = QComboBox()
        self.combo_spatial_mode = QComboBox()
        self.combo_multi_match = QComboBox()
        for _cb in (self.combo_named_field, self.combo_ref_field,
                    self.combo_spatial_mode, self.combo_multi_match):
            _cb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.lbl_named_field = QLabel()
        style_param_label(self.lbl_named_field, '命名字段', '被命名字段')
        self.lbl_ref_field = QLabel()
        style_param_label(self.lbl_ref_field, '参考字段', '参考取值字段')
        self.lbl_multi_match = QLabel()
        style_param_label(self.lbl_multi_match, '多匹配', '多匹配处理')
        self.lbl_spatial_mode = QLabel()
        style_param_label(self.lbl_spatial_mode, '空间模式', '空间命名模式')
        self.row_field_mode_param = ModeParamRow(on_changed=self._on_mode_param_changed)
        self.w_named_field_block = param_block(self.lbl_named_field, self.combo_named_field, spacing=1)
        self.w_ref_field_block = param_block(self.lbl_ref_field, self.combo_ref_field, spacing=1)
        self.w_multi_match_block = param_block(self.lbl_multi_match, self.combo_multi_match, spacing=1)
        self.w_spatial_mode_block = param_block(self.lbl_spatial_mode, self.combo_spatial_mode, spacing=1)
        field_outer.addWidget(self.w_named_field_block)
        field_outer.addWidget(self.w_ref_field_block)
        field_outer.addWidget(self.w_multi_match_block)
        field_outer.addWidget(self.w_spatial_mode_block)
        field_outer.addWidget(self.row_field_mode_param)
        # Keep field_grid as an empty layout so older placement helpers stay safe.
        self.field_grid = QGridLayout()
        self.field_grid.setContentsMargins(0, 0, 0, 0)
        self.w_end_fields = QWidget()
        end_outer = QVBoxLayout(self.w_end_fields)
        end_outer.setContentsMargins(0, 0, 0, 0)
        end_outer.setSpacing(6)
        self.combo_head_ref = QComboBox()
        self.combo_head_named = QComboBox()
        self.combo_tail_ref = QComboBox()
        self.combo_tail_named = QComboBox()
        for _cb in (self.combo_head_ref, self.combo_head_named, self.combo_tail_ref, self.combo_tail_named):
            _cb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.lbl_head_ref = QLabel()
        style_param_label(self.lbl_head_ref, '头点字段', '头点字段')
        self.lbl_head_named = QLabel()
        style_param_label(self.lbl_head_named, '写入线字段', '写入线字段')
        self.lbl_tail_ref = QLabel()
        style_param_label(self.lbl_tail_ref, '尾点字段', '尾点字段')
        self.lbl_tail_named = QLabel()
        style_param_label(self.lbl_tail_named, '写入线字段', '写入线字段')
        end_outer.addWidget(param_block(self.lbl_head_ref, self.combo_head_ref))
        end_outer.addWidget(param_block(self.lbl_head_named, self.combo_head_named))
        end_outer.addWidget(param_block(self.lbl_tail_ref, self.combo_tail_ref))
        end_outer.addWidget(param_block(self.lbl_tail_named, self.combo_tail_named))
        self.w_end_fields.setVisible(False)
        field_outer.addWidget(self.w_end_fields)
        self.combo_field_scheme = QComboBox()
        self.combo_field_scheme.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo_field_scheme.setMinimumWidth(0)
        self.lbl_field_scheme = QLabel()
        style_param_label(self.lbl_field_scheme, '批量方案', '批量方案')
        self.w_field_batch_block = param_block(self.lbl_field_scheme, self.combo_field_scheme, spacing=1)
        field_outer.addWidget(self.w_field_batch_block)
        self.w_field_mid_bottom_pad = self._make_edge_pad('field_mid_bottom_pad')
        field_outer.addWidget(self.w_field_mid_bottom_pad)
        self.btn_field_scheme_add = QPushButton()
        self.btn_field_scheme_view = QPushButton()
        self.btn_field_scheme_manage = QPushButton()
        self.btn_field_scheme_import = QPushButton(self.tr('导入'))
        self.btn_field_scheme_export = QPushButton(self.tr('导出'))
        self.btn_field_scheme_add.setObjectName('fieldAddBtn')
        self.btn_field_scheme_view.setObjectName('fieldViewBtn')
        self.btn_field_scheme_manage.setObjectName('schemeManageMainBtn')
        self.btn_field_scheme_import.setObjectName('schemeImportBtn')
        self.btn_field_scheme_export.setObjectName('schemeExportBtn')
        self._style_action_btn(self.btn_field_scheme_add, '添加', '把当前字段命名参数作为一条子任务，加入所选方案')
        self._style_action_btn(self.btn_field_scheme_view, '查看', '查看、编辑、删除、调整当前方案里的子任务')
        self._style_action_btn(self.btn_field_scheme_manage, '方案', '新建、重命名、复制、删除方案')
        self.w_field_mid_actions = QWidget()
        self._fill_mid_action_grid(
            self.w_field_mid_actions,
            (self.btn_field_scheme_add, self.btn_field_scheme_manage),
            (self.btn_field_scheme_view,),
            span_row2=True,
        )
        field_outer.insertWidget(0, self.w_field_mid_actions)
        self.w_field_mid_top_pad = self._make_edge_pad('field_mid_top_pad')
        field_outer.insertWidget(1, self.w_field_mid_top_pad)
        self.field_options_extra.setVisible(False)
        options_layout.addWidget(self.field_options_extra)

        self.move_options_extra = QWidget()
        _move_outer = QVBoxLayout(self.move_options_extra)
        _move_outer.setContentsMargins(0, 0, 0, 0)
        _move_outer.setSpacing(8)
        # 移动：容差在上方共用行。全部组合都在「移动模式」里，按两侧图层的点／线／面切换。
        # 不要「提取已吸附」「临时样式」；不在参考图层侧再加一套特殊检测。

        self.lbl_move_mode = QLabel(self.tr('移动模式'))
        self.combo_move_mode = QComboBox()
        self.combo_move_mode.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo_move_mode.setMinimumWidth(0)
        self.combo_move_mode.setMaxVisibleItems(22)
        self.lbl_move_pair = QLabel(self.tr(
            '左右两侧都选好图层后，列表会按点 / 线 / 面切换。'
        ))
        self.lbl_move_pair.setWordWrap(True)
        self.lbl_move_pair.setStyleSheet('color:#495057;font-size:11px;')
        self.lbl_move_pair.setVisible(False)
        self.lbl_move_pair.hide()

        self.lbl_move_batch_scheme = QLabel(self.tr('批量方案'))
        self.combo_move_scheme = QComboBox()
        self.combo_move_scheme.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo_move_scheme.setMinimumWidth(0)
        self.chk_move_batch_continue = QCheckBox(self.tr('失败继续'))
        self.chk_move_batch_continue.setChecked(True)
        self.chk_move_batch_continue.setToolTip(
            self.tr('批量执行时，某一子任务失败后是否继续后面的子任务')
        )

        self.btn_move_scheme_add = QPushButton(self.tr('➕ 添加'))
        self.btn_move_scheme_add.setObjectName('moveAddBtn')
        self.btn_move_scheme_add.setToolTip(
            self.tr('将当前被移／参考图层与容差加入所选移动方案')
        )
        self.btn_move_scheme_view = QPushButton()
        self.btn_move_scheme_view.setObjectName('moveViewBtn')
        self.btn_move_scheme_view.setToolTip(
            self.tr('查看、编辑、删除、调整当前移动方案里的子任务')
        )
        self.w_move_left_inner = QWidget()
        _lay_move_left = QVBoxLayout(self.w_move_left_inner)
        _lay_move_left.setContentsMargins(0, 0, 0, 0)
        _lay_move_left.setSpacing(6)
        self.lay_move_rows = _lay_move_left
        style_param_label(self.lbl_move_batch_scheme, '批量方案', '批量方案')
        style_param_label(self.lbl_move_mode, '移动模式', '移动模式')
        self.w_move_mid_top_pad = self._make_edge_pad('move_mid_top_pad')
        _lay_move_left.addWidget(self.w_move_mid_top_pad)
        _lay_move_left.addWidget(self.chk_move_batch_continue)
        self.w_move_mode_block = param_block(self.lbl_move_mode, self.combo_move_mode)
        _lay_move_left.addWidget(self.w_move_mode_block)
        self.w_move_batch_block = param_block(self.lbl_move_batch_scheme, self.combo_move_scheme)
        _lay_move_left.addWidget(self.w_move_batch_block)
        self.w_move_mid_bottom_pad = self._make_edge_pad('move_mid_bottom_pad')
        _lay_move_left.addWidget(self.w_move_mid_bottom_pad)

        self.w_move_options_block = QWidget()
        _lay_move_block = QVBoxLayout(self.w_move_options_block)
        _lay_move_block.setContentsMargins(0, 0, 0, 0)
        _lay_move_block.setSpacing(6)
        _lay_move_block.addWidget(self.w_move_left_inner)
        self.w_move_left_inner.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        _move_outer.addWidget(self.w_move_options_block)

        self.btn_move_scheme_manage = QPushButton()
        self.btn_move_scheme_manage.setObjectName('schemeManageMainBtn')
        self.btn_move_scheme_import = QPushButton(self.tr('📥 导入'))
        self.btn_move_scheme_import.setObjectName('schemeImportBtn')
        self.btn_move_scheme_import.setToolTip(
            self.tr('导入移动方案 JSON（独立入口，不串吸附库）')
        )
        self.btn_move_scheme_export = QPushButton(self.tr('📤 导出'))
        self.btn_move_scheme_export.setObjectName('schemeExportBtn')
        self.btn_move_scheme_export.setToolTip(
            self.tr('导出移动方案 JSON（独立入口，不串吸附库）')
        )
        self._style_action_btn(self.btn_move_scheme_add, '添加', '将当前被移／参考图层与容差加入所选移动方案')
        self._style_action_btn(self.btn_move_scheme_view, '查看', '查看、编辑、删除、调整当前移动方案里的子任务')
        self._style_action_btn(self.btn_move_scheme_manage, '方案', '新建、重命名、复制、删除移动方案（与吸附方案库分开）')
        self.w_move_mid_actions = QWidget()
        self._fill_mid_action_column(
            self.w_move_mid_actions,
            (self.btn_move_scheme_add, self.btn_move_scheme_manage, self.btn_move_scheme_view),
        )
        _move_outer.insertWidget(0, self.w_move_mid_actions)
        self.move_options_extra.setVisible(False)
        options_layout.addWidget(self.move_options_extra)

        self.mid_scroll.setWidget(self.mid_inner)

        self.btn_confirm = QPushButton()
        self.btn_confirm.setObjectName('executeBtn')
        self._style_action_btn(self.btn_confirm, '执行', '使用当前界面上的吸附选项参数执行')

        self.btn_refresh = QPushButton()
        self.btn_refresh.setObjectName('refreshBtn')
        self._style_action_btn(self.btn_refresh, '刷新', '重新加载图层列表')

        self.btn_mode_toggle = QPushButton()
        self.btn_mode_toggle.setObjectName('modeToggleBtn')
        self._style_action_btn(self.btn_mode_toggle, '吸附', '当前：吸附检测 — 点击展开三选（吸附检测／字段命名／移动）')
        self._sync_mode_toggle_text()

        self.btn_language = QPushButton()
        self.btn_language.clicked.connect(self._show_language_menu)
        style_icon_button(self.btn_language, language_icon(), '语言')

        self.btn_help = QPushButton()
        # Placeholder only: no document, no popup.
        style_icon_button(self.btn_help, help_icon(), '帮助')

        style_icon_button(self.btn_scheme_import, import_icon(), '导入')
        style_icon_button(self.btn_scheme_export, export_icon(), '导出')
        style_icon_button(self.btn_field_scheme_import, import_icon(), '导入')
        style_icon_button(self.btn_field_scheme_export, export_icon(), '导出')
        style_icon_button(self.btn_move_scheme_import, import_icon(), '导入')
        style_icon_button(self.btn_move_scheme_export, export_icon(), '导出')

        def _boxed_frame():
            fr = QFrame()
            fr.setFrameShape(QFrame.Shape.StyledPanel)
            fr.setFrameShadow(QFrame.Shadow.Plain)
            fr.setLineWidth(1)
            fr.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            return fr

        self.right_col = QWidget()
        self.right_col.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.right_col.setMinimumWidth(0)
        right_lay = QVBoxLayout(self.right_col)
        right_lay.setContentsMargins(8, 4, 8, 8)
        right_lay.setSpacing(8)

        self.right_top_frame = _boxed_frame()
        top_lay = QHBoxLayout(self.right_top_frame)
        top_lay.setContentsMargins(4, 4, 4, 4)
        top_lay.setSpacing(4)
        for _b in (
            self.btn_language,
            self.btn_help,
            self.btn_scheme_import,
            self.btn_scheme_export,
            self.btn_field_scheme_import,
            self.btn_field_scheme_export,
            self.btn_move_scheme_import,
            self.btn_move_scheme_export,
        ):
            top_lay.addWidget(_b, 1)
        self.btn_field_scheme_import.setVisible(False)
        self.btn_field_scheme_export.setVisible(False)
        self.btn_move_scheme_import.setVisible(False)
        self.btn_move_scheme_export.setVisible(False)

        self.options_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        options_outer.addWidget(self.mid_scroll)

        self.right_bottom_frame = _boxed_frame()
        bottom_outer = QVBoxLayout(self.right_bottom_frame)
        bottom_outer.setContentsMargins(4, 4, 4, 4)
        bottom_outer.setSpacing(4)
        bottom_outer.addWidget(self.btn_mode_toggle)
        bottom_row2 = QHBoxLayout()
        bottom_row2.setContentsMargins(0, 0, 0, 0)
        bottom_row2.setSpacing(6)
        bottom_row2.addWidget(self.btn_refresh, 1)
        bottom_row2.addWidget(self.btn_confirm, 1)
        bottom_outer.addLayout(bottom_row2)

        self.right_top_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.right_bottom_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.mid_scroll.setMinimumHeight(64)
        right_lay.addWidget(self.right_top_frame, 0)
        right_lay.addWidget(self.options_group, 1)
        right_lay.addWidget(self.right_bottom_frame, 0)
        self._setup_filter_button_groups()
        self._distribute_mid_param_stretch()
        columns_layout.addWidget(self.right_col, 2)
        self._configure_right_combos()
        self._stamp_static_combo_sources()
        self._init_multi_combo()
        self._init_polygon_output_checklist()
        self._update_line_rule_label()
        try:
            guard_all_combos(self)
        except Exception:  # nosec B110
            pass

    def _action_btn_height(self, btn):
        if btn.objectName() in ('executeBtn', 'refreshBtn', 'modeToggleBtn'):
            return BOTTOM_BTN_H
        return ACTION_BTN_H

    def _style_action_btn(self, btn, short_src, tip_src):
        btn.setText(self.tr(short_src))
        btn.setToolTip(self.tr(tip_src))
        btn.setProperty('msgid', short_src)
        btn.setProperty('tip', tip_src)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setMinimumWidth(0)
        btn.setFixedHeight(self._action_btn_height(btn))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

    def _fill_mid_action_grid(self, host, row1, row2, span_row2=False):
        lay = QGridLayout(host)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setHorizontalSpacing(6)
        lay.setVerticalSpacing(6)
        lay.setColumnStretch(0, 1)
        lay.setColumnStretch(1, 1)
        for col, btn in enumerate(row1):
            lay.addWidget(btn, 0, col)
        if span_row2 and len(row2) == 1:
            lay.addWidget(row2[0], 1, 0, 1, 2)
        else:
            for col, btn in enumerate(row2):
                lay.addWidget(btn, 1, col)
        host.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _fill_mid_action_column(self, host, buttons):
        lay = QVBoxLayout(host)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        for btn in buttons:
            if btn is not None:
                lay.addWidget(btn)
        host.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _iter_filter_buttons(self):
        names = (
            'target_btn_point', 'target_btn_line', 'target_btn_polygon', 'target_btn_all',
            'ref_btn_point', 'ref_btn_line', 'ref_btn_polygon', 'ref_btn_all',
            'field_tgt_btn_point', 'field_tgt_btn_line', 'field_tgt_btn_polygon', 'field_tgt_btn_group',
            'field_ref_btn_point', 'field_ref_btn_line', 'field_ref_btn_polygon', 'field_ref_btn_group',
        )
        for name in names:
            btn = getattr(self, name, None)
            if btn is not None:
                yield btn

    def _filter_button_name_tip(self, btn):
        src = btn.property('tip') or ''
        return self.tr(src) if src else ''

    def _apply_filter_button_tip(self, btn, extra=None):
        """Restore the tr() name tooltip and the title under the icon."""
        if btn is None:
            return
        name = self._filter_button_name_tip(btn)
        try:
            btn.setText(name)
        except Exception:  # nosec B110
            pass
        if extra:
            btn.setToolTip(name + ('\n' + extra if name else extra))
        else:
            btn.setToolTip(name)

    def _restore_filter_button_tips(self, buttons=None, extra=None):
        if buttons is None:
            buttons = list(self._iter_filter_buttons())
        for btn in buttons:
            self._apply_filter_button_tip(btn, extra=extra)

    def _setup_filter_button_groups(self):
        def _group(btns, exclusive=True):
            grp = QButtonGroup(self)
            grp.setExclusive(exclusive)
            for i, b in enumerate(btns):
                if b is None:
                    continue
                b.setCheckable(True)
                grp.addButton(b, i)
            return grp
        self._filter_grp_target = _group([
            getattr(self, 'target_btn_point', None),
            getattr(self, 'target_btn_line', None),
            getattr(self, 'target_btn_polygon', None),
            getattr(self, 'target_btn_all', None),
        ])
        self._filter_grp_ref = _group([
            getattr(self, 'ref_btn_point', None),
            getattr(self, 'ref_btn_line', None),
            getattr(self, 'ref_btn_polygon', None),
            getattr(self, 'ref_btn_all', None),
        ])
        # Field point/line/polygon can all be off; group is independent.
        for btn in self._iter_filter_buttons():
            btn.setCheckable(True)
        if hasattr(self, 'target_btn_all'):
            self.target_btn_all.setChecked(True)
        if hasattr(self, 'ref_btn_all'):
            self.ref_btn_all.setChecked(True)
        self._sync_field_filter_checked()

    def _geom_filter_key(self, geom):
        if geom == QgsWkbTypes.GeometryType.PointGeometry:
            return 'point'
        if geom == QgsWkbTypes.GeometryType.LineGeometry:
            return 'line'
        if geom == QgsWkbTypes.GeometryType.PolygonGeometry:
            return 'polygon'
        return 'all'

    def _sync_snap_filter_checked(self, side, geom):
        key = self._geom_filter_key(geom)
        mapping = {
            'target': {
                'point': getattr(self, 'target_btn_point', None),
                'line': getattr(self, 'target_btn_line', None),
                'polygon': getattr(self, 'target_btn_polygon', None),
                'all': getattr(self, 'target_btn_all', None),
            },
            'ref': {
                'point': getattr(self, 'ref_btn_point', None),
                'line': getattr(self, 'ref_btn_line', None),
                'polygon': getattr(self, 'ref_btn_polygon', None),
                'all': getattr(self, 'ref_btn_all', None),
            },
        }.get(side, {})
        for k, btn in mapping.items():
            if btn is None:
                continue
            btn.blockSignals(True)
            btn.setChecked(k == key)
            btn.blockSignals(False)

    def _sync_field_filter_checked(self, side=None):
        sides = ('target', 'ref') if side is None else (side,)
        for s in sides:
            if s == 'target':
                geom = getattr(self, '_field_target_geom', None)
                path = getattr(self, '_field_group_path_target', None)
                mapping = {
                    'point': getattr(self, 'field_tgt_btn_point', None),
                    'line': getattr(self, 'field_tgt_btn_line', None),
                    'polygon': getattr(self, 'field_tgt_btn_polygon', None),
                }
                grp = getattr(self, 'field_tgt_btn_group', None)
            else:
                geom = getattr(self, '_field_ref_geom', None)
                path = getattr(self, '_field_group_path_ref', None)
                mapping = {
                    'point': getattr(self, 'field_ref_btn_point', None),
                    'line': getattr(self, 'field_ref_btn_line', None),
                    'polygon': getattr(self, 'field_ref_btn_polygon', None),
                }
                grp = getattr(self, 'field_ref_btn_group', None)
            want = self._geom_filter_key(geom) if geom is not None else None
            for k, btn in mapping.items():
                if btn is None:
                    continue
                btn.blockSignals(True)
                btn.setChecked(k == want)
                btn.blockSignals(False)
            if grp is not None:
                grp.blockSignals(True)
                grp.setChecked(bool(path))
                grp.blockSignals(False)
                name_tip = self._filter_button_name_tip(grp)
                if path:
                    node = self._resolve_group_from_path(path)
                    layers = self._layers_in_tree_group(node) if node is not None else []
                    total = layers_feature_count(layers)
                    extra = self.tr('组内矢量要素共 {0} 个').format(total)
                    grp.setToolTip(name_tip + ('\n' + extra if name_tip else extra))
                else:
                    grp.setToolTip(name_tip)

    def _make_edge_pad(self, name, height=8):
        pad = QWidget()
        pad.setObjectName(name)
        pad.setFixedHeight(int(height))
        pad.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        pad.setProperty('mid_edge_pad', True)
        return pad

    def _is_mid_gap_widget(self, widget):
        return widget is not None and bool(widget.property('mid_gap'))

    def _is_edge_pad_widget(self, widget):
        return widget is not None and bool(widget.property('mid_edge_pad'))

    def _make_mid_even_gap(self, height):
        gap = QWidget()
        gap.setProperty('mid_gap', True)
        gap.setFixedHeight(max(0, int(height)))
        gap.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        return gap

    def _strip_mid_gaps(self, layout):
        if layout is None:
            return
        widgets = []
        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget = item.widget() if item is not None else None
            if widget is None or self._is_mid_gap_widget(widget):
                if widget is not None and self._is_mid_gap_widget(widget):
                    widget.setParent(None)
                    widget.deleteLater()
                continue
            widgets.append(widget)
        while layout.count():
            layout.takeAt(0)
        for widget in widgets:
            layout.addWidget(widget)
            layout.setStretch(layout.count() - 1, 0)

    def _edge_pad_insert_index(self, layout, name):
        if layout is None:
            return 0
        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget = item.widget() if item is not None else None
            if widget is not None and widget.objectName() == name:
                return i + 1
        return 0

    def _visible_mid_widgets(self, layout, skip=()):
        skip = set(w for w in (skip or ()) if w is not None)
        out = []
        if layout is None:
            return out
        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget = item.widget() if item is not None else None
            if widget is None or widget in skip:
                continue
            if self._is_mid_gap_widget(widget) or self._is_edge_pad_widget(widget):
                continue
            parent = widget.parentWidget() or widget
            if widget.isVisibleTo(parent):
                out.append(widget)
        return out

    def _apply_snap_mid_control_heights(self, extra):
        # 补死: leftover must not be eaten by raising the tolerance box
        # or any mid control. Keep this hook as a reset-only no-op.
        self._reset_snap_mid_control_heights()

    def _reset_snap_mid_control_heights(self):
        for w in (
            getattr(self, 'spin_tolerance', None),
            getattr(self, 'combo_snap_scheme', None),
            getattr(self, 'combo_snap_spatial_mode', None),
        ):
            if w is None:
                continue
            stored = w.property('snap_base_h')
            if stored:
                w.setMinimumHeight(int(stored))
            else:
                w.setMinimumHeight(0)
            w.setMaximumHeight(16777215)

    def _insert_even_gaps_between(self, layout, widgets, gap_h, remainder=0):
        if layout is None or len(widgets) < 2:
            return
        gap_h = max(0, int(gap_h))
        remainder = max(0, int(remainder))
        if gap_h <= 0 and remainder <= 0:
            return
        positions = []
        for w in widgets:
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item is not None and item.widget() is w:
                    positions.append(i)
                    break
        if len(positions) != len(widgets):
            return
        n_gaps = len(positions) - 1
        for k, idx in enumerate(positions[1:][::-1]):
            front = n_gaps - 1 - k
            extra = 1 if front < remainder else 0
            layout.insertWidget(idx, self._make_mid_even_gap(gap_h + extra))

    def _redistribute_group_gaps(self, layout, skip_widgets=()):
        # Compatibility no-op: 2.2.9 expanding springs are abolished.
        self._strip_mid_gaps(layout)

    def _current_mid_actions(self):
        mode = getattr(self, '_ui_mode', 'snap')
        if mode == 'field':
            return getattr(self, 'w_field_mid_actions', None)
        if mode == 'move':
            return getattr(self, 'w_move_mid_actions', None)
        return getattr(self, 'w_snap_mid_actions', None)

    def _current_param_layout(self):
        mode = getattr(self, '_ui_mode', 'snap')
        if mode == 'field':
            host = getattr(self, 'field_options_extra', None)
            return host.layout() if host is not None else None
        if mode == 'move':
            return getattr(self, 'lay_move_rows', None)
        return getattr(self, 'lay_snap_left', None)

    def _current_edge_pads(self):
        mode = getattr(self, '_ui_mode', 'snap')
        if mode == 'field':
            return (
                getattr(self, 'w_field_mid_top_pad', None),
                getattr(self, 'w_field_mid_bottom_pad', None),
            )
        if mode == 'move':
            return (
                getattr(self, 'w_move_mid_top_pad', None),
                getattr(self, 'w_move_mid_bottom_pad', None),
            )
        return (
            getattr(self, 'w_snap_mid_top_pad', None),
            getattr(self, 'w_snap_mid_bottom_pad', None),
        )

    def _widget_pref_h(self, widget):
        if widget is None:
            return 0
        return max(widget.sizeHint().height(), widget.minimumSizeHint().height(), 0)

    def _visible_param_groups(self, layout, skip=()):
        skip = set(w for w in (skip or ()) if w is not None)
        actions = self._current_mid_actions()
        if actions is not None:
            skip.add(actions)
        out = []
        if layout is None:
            return out
        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget = item.widget() if item is not None else None
            if widget is None or widget in skip:
                continue
            if self._is_mid_gap_widget(widget) or self._is_edge_pad_widget(widget):
                continue
            parent = widget.parentWidget() or widget
            if widget.isVisibleTo(parent):
                out.append(widget)
        return out

    def _mid_param_region_height(self):
        """Height of the mid param region using height/sizeHint only.

        Do not call mapTo here. init_ui runs this before the dialog is shown, and
        mapping an unmapped mid_scroll viewport crashes in Qt C++ (0xC0000005)
        where a Python try cannot catch it.
        """
        mid = getattr(self, 'mid_scroll', None)
        actions = self._current_mid_actions()
        if mid is None:
            return 1
        vp = mid.viewport() if mid.viewport() is not None else mid
        # Prefer the viewport only. mid.height() includes the frame and would
        # overstate leftover, causing mid content to clip with the bar hidden.
        h = 0
        if vp is not None:
            h = int(vp.height() or 0)
        if h <= 0:
            h = int(mid.height() or 0)
        if h <= 0:
            if vp is not None:
                h = max(h, int(vp.sizeHint().height() or 0), int(vp.minimumSizeHint().height() or 0))
            h = max(h, int(mid.sizeHint().height() or 0), int(mid.minimumSizeHint().height() or 0), 1)
        # Subtract only the mid action strip and the spacing under it.
        # Never subtract the param host itself (move_options_extra also
        # contains the move parameter groups).
        if actions is not None and actions.isVisible():
            ah = int(actions.height() or 0)
            if ah <= 0:
                ah = self._widget_pref_h(actions)
            h -= max(ah, 0)
            parent = actions.parentWidget()
            parent_lay = parent.layout() if parent is not None else None
            used_parent_spacing = False
            if parent_lay is not None:
                for i in range(parent_lay.count()):
                    item = parent_lay.itemAt(i)
                    sibling = item.widget() if item is not None else None
                    if sibling is not None and sibling is not actions and sibling.isVisible():
                        h -= max(parent_lay.spacing(), 0)
                        used_parent_spacing = True
                        break
            if not used_parent_spacing:
                ol = getattr(self, '_options_group_layout', None)
                if ol is not None:
                    h -= max(ol.spacing(), 0)
        return max(int(h), 1)

    def _iter_mid_host_layouts(self):
        host = getattr(self, 'field_options_extra', None)
        for lay in (
            getattr(self, 'lay_snap_left', None),
            getattr(self, 'lay_move_rows', None),
            host.layout() if host is not None else None,
            getattr(self, 'lay_tol_row', None),
        ):
            if lay is not None:
                yield lay

    def _mid_owned_param_widgets(self):
        names = (
            'w_tol_row', 'w_tol_cluster', 'w_out_cluster',
            'chk_snap', 'chk_batch_continue', 'w_snap_spatial_block',
            'row_snap_mode_param', 'w_snap_batch_block',
            'w_snap_mid_top_pad', 'w_snap_mid_bottom_pad',
            'w_named_field_block', 'w_ref_field_block', 'w_multi_match_block',
            'w_spatial_mode_block', 'row_field_mode_param', 'w_end_fields',
            'w_field_batch_block', 'w_field_mid_top_pad', 'w_field_mid_bottom_pad',
            'chk_move_batch_continue', 'w_move_mode_block', 'w_move_batch_block',
            'w_move_mid_top_pad', 'w_move_mid_bottom_pad',
        )
        out = []
        for name in names:
            widget = getattr(self, name, None)
            if widget is not None:
                out.append(widget)
        return out

    def _detach_mid_param_widgets(self):
        for widget in self._mid_owned_param_widgets():
            for lay in self._iter_mid_host_layouts():
                CDETDialog._layout_take_widget(lay, widget)

    def _mid_param_order(self, mode):
        if mode == 'field':
            items = [
                getattr(self, 'w_field_mid_top_pad', None),
                getattr(self, 'w_tol_cluster', None),
                getattr(self, 'w_out_cluster', None),
                getattr(self, 'w_named_field_block', None),
                getattr(self, 'w_ref_field_block', None),
                getattr(self, 'w_multi_match_block', None),
                getattr(self, 'w_spatial_mode_block', None),
                getattr(self, 'row_field_mode_param', None),
                getattr(self, 'w_end_fields', None),
                getattr(self, 'w_field_batch_block', None),
                getattr(self, 'w_field_mid_bottom_pad', None),
            ]
        elif mode == 'move':
            items = [
                getattr(self, 'w_move_mid_top_pad', None),
                getattr(self, 'w_tol_cluster', None),
                getattr(self, 'w_out_cluster', None),
                getattr(self, 'chk_move_batch_continue', None),
                getattr(self, 'w_move_mode_block', None),
                getattr(self, 'w_move_batch_block', None),
                getattr(self, 'w_move_mid_bottom_pad', None),
            ]
        else:
            items = [
                getattr(self, 'w_snap_mid_top_pad', None),
                getattr(self, 'w_tol_cluster', None),
                getattr(self, 'chk_snap', None),
                getattr(self, 'chk_batch_continue', None),
                getattr(self, 'w_snap_spatial_block', None),
                getattr(self, 'row_snap_mode_param', None),
                getattr(self, 'w_snap_batch_block', None),
                getattr(self, 'w_snap_mid_bottom_pad', None),
            ]
        return [widget for widget in items if widget is not None]

    def _lock_mid_group_policy(self, widget):
        """Keep each group at its natural height. Do not store sizeHint as a minimum: that ratchets the window taller."""
        if widget is None:
            return
        if self._is_edge_pad_widget(widget) or self._is_mid_gap_widget(widget):
            return
        policy = widget.sizePolicy()
        policy.setHorizontalPolicy(QSizePolicy.Policy.Expanding)
        policy.setVerticalPolicy(QSizePolicy.Policy.Minimum)
        widget.setSizePolicy(policy)
        widget.setMinimumHeight(0)
        widget.setMaximumHeight(16777215)

    def _rebuild_mid_param_layout(self):
        """Restore mid parameter groups as direct siblings in the active layout."""
        layout = self._current_param_layout()
        if layout is None:
            return
        self._strip_mid_gaps(layout)
        self._detach_mid_param_widgets()
        mode = getattr(self, '_ui_mode', 'snap')
        order = self._mid_param_order(mode)
        if mode == 'field':
            actions = getattr(self, 'w_field_mid_actions', None)
            if actions is not None and not CDETDialog._layout_contains_widget(layout, actions):
                layout.insertWidget(0, actions)
        for widget in order:
            layout.addWidget(widget)
            self._lock_mid_group_policy(widget)
        top, bottom = self._current_edge_pads()
        pad_h = 0 if getattr(self, '_ui_mode', None) == 'field' else 8
        for pad in (top, bottom):
            if pad is not None:
                pad.setFixedHeight(pad_h)
                pad.setVisible(True)
        row_host = getattr(self, 'w_tol_row', None)
        if row_host is not None:
            row_host.setVisible(False)
        if layout is not None:
            layout.activate()

    def _mid_structure_ok(self, layout):
        if layout is None:
            return False
        expected = self._mid_param_order(getattr(self, '_ui_mode', 'snap'))
        present = []
        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget = item.widget() if item is not None else None
            if widget is None:
                continue
            if self._is_mid_gap_widget(widget):
                continue
            present.append(widget)
            if widget is getattr(self, 'w_tol_row', None):
                return False
        for widget in expected:
            if widget not in present:
                return False
        return True

    def _layout_mid_groups(self):
        """Even stretch between parameter groups. Does not create gap widgets or resize the window.

        Snap and move keep the batch-scheme group last, so the extra space sits
        above it and the titles cannot be painted on top of each other.
        """
        layout = self._current_param_layout()
        if layout is None:
            return
        if not self._mid_structure_ok(layout):
            self._rebuild_mid_param_layout()
            layout = self._current_param_layout()
            if layout is None:
                return
        top, bottom = self._current_edge_pads()
        groups = self._visible_param_groups(layout, skip=(top, bottom))
        widgets = []
        sig = []
        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget = item.widget() if item is not None else None
            if widget is None:
                sig.append(('s',))
                continue
            if self._is_mid_gap_widget(widget):
                sig.append(('g',))
                continue
            widgets.append(widget)
            sig.append(('w', id(widget)))
        want = []
        seen = 0
        for widget in widgets:
            if widget in groups and seen:
                want.append(('s',))
            if widget in groups:
                seen += 1
            want.append(('w', id(widget)))
        # Field naming keeps a single trailing stretch, so leftover height sits
        # under 批量方案 instead of opening gaps between the fields above it.
        if getattr(self, '_ui_mode', None) == 'field':
            self._strip_mid_gaps(layout)
            layout.addStretch(1)
        elif sig != want:
            self._strip_mid_gaps(layout)
            positions = []
            for i in range(layout.count()):
                item = layout.itemAt(i)
                widget = item.widget() if item is not None else None
                if widget in groups:
                    positions.append(i)
            for idx in positions[1:][::-1]:
                layout.insertStretch(idx, 1)
        pad_h = 0 if getattr(self, '_ui_mode', None) == 'field' else 8
        for pad in (top, bottom):
            if pad is not None:
                pad.setFixedHeight(pad_h)
                pad.setVisible(True)
        for widget in groups:
            self._lock_mid_group_policy(widget)
        if getattr(self, '_ui_mode', None) == 'field':
            for widget in groups:
                policy = widget.sizePolicy()
                policy.setVerticalPolicy(QSizePolicy.Policy.Maximum)
                widget.setSizePolicy(policy)
                widget.setMinimumHeight(0)
                widget.setMaximumHeight(16777215)

    def _mode_param_groups(self, mode):
        """Widgets that form mid parameter groups for a mode (for min-height)."""
        if mode == 'snap':
            items = [
                getattr(self, 'w_tol_cluster', None),
                getattr(self, 'chk_snap', None),
                getattr(self, 'chk_batch_continue', None),
                getattr(self, 'w_snap_spatial_block', None),
                getattr(self, 'row_snap_mode_param', None),
                getattr(self, 'w_snap_batch_block', None),
            ]
        elif mode == 'move':
            items = [
                getattr(self, 'w_tol_cluster', None),
                getattr(self, 'w_out_cluster', None),
                getattr(self, 'chk_move_batch_continue', None),
                getattr(self, 'w_move_mode_block', None),
                getattr(self, 'w_move_batch_block', None),
            ]
        else:
            items = [
                getattr(self, 'w_tol_cluster', None),
                getattr(self, 'w_out_cluster', None),
                getattr(self, 'w_named_field_block', None),
                getattr(self, 'w_ref_field_block', None),
                getattr(self, 'w_multi_match_block', None),
                getattr(self, 'w_spatial_mode_block', None),
                getattr(self, 'row_field_mode_param', None),
                getattr(self, 'w_end_fields', None),
                getattr(self, 'w_field_batch_block', None),
            ]
        out = []
        for widget in items:
            if widget is None:
                continue
            # Hidden optional rows (mode params, end-fields) should not force extra window height.
            try:
                if not widget.isVisible() and widget in (
                    getattr(self, 'row_snap_mode_param', None),
                    getattr(self, 'row_field_mode_param', None),
                    getattr(self, 'w_end_fields', None),
                ):
                    continue
            except Exception:  # nosec B110
                pass
            out.append(widget)
        return out

    def _mode_fit_height(self, mode):
        top_h = 0
        bot_h = 0
        if getattr(self, 'right_top_frame', None) is not None:
            top_h = max(self.right_top_frame.sizeHint().height(), self.right_top_frame.minimumSizeHint().height(), 28)
            if top_h > 160:
                top_h = 28
        if getattr(self, 'right_bottom_frame', None) is not None:
            bot_h = max(self.right_bottom_frame.sizeHint().height(), self.right_bottom_frame.minimumSizeHint().height(), 60)
            if bot_h > 200:
                bot_h = 60
        actions = {
            'snap': getattr(self, 'w_snap_mid_actions', None),
            'field': getattr(self, 'w_field_mid_actions', None),
            'move': getattr(self, 'w_move_mid_actions', None),
        }.get(mode)
        groups = self._mode_param_groups(mode)
        spacing = 6
        layout = None
        if mode == 'snap':
            layout = getattr(self, 'lay_snap_left', None)
        elif mode == 'move':
            layout = getattr(self, 'lay_move_rows', None)
        else:
            host = getattr(self, 'field_options_extra', None)
            layout = host.layout() if host is not None else None
        if layout is not None:
            spacing = max(layout.spacing(), 0)
        mid = self._widget_pref_h(actions) + 8 + 8
        for widget in groups:
            mid += self._widget_pref_h(widget)
        n_sib = len(groups) + 2
        mid += spacing * max(n_sib - 1, 0)
        if mode == 'field':
            mid += spacing
        else:
            ol = getattr(self, '_options_group_layout', None)
            mid += max(ol.spacing() if ol is not None else 4, 0)
        # Right column chrome: margins/spacing, options group title, mid-scroll frame.
        chrome = 36 + 8 + 8 + 8
        return top_h + mid + bot_h + chrome

    def _distribute_mid_param_stretch(self):
        self._clear_mid_param_stretch()
        self._reset_snap_mid_control_heights()
        ol = getattr(self, '_options_group_layout', None)
        mode = getattr(self, '_ui_mode', 'snap')
        grow = {
            'snap': getattr(self, 'w_snap_options_block', None),
            'field': getattr(self, 'field_options_extra', None),
            'move': getattr(self, 'move_options_extra', None),
        }.get(mode)
        if ol is not None:
            for i in range(ol.count()):
                item = ol.itemAt(i)
                widget = item.widget() if item is not None else None
                if widget is None:
                    continue
                is_grow = widget is grow
                ol.setStretch(i, 1 if is_grow else 0)
                if is_grow:
                    widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        if mode == 'move':
            move_extra = getattr(self, 'move_options_extra', None)
            if move_extra is not None and move_extra.layout() is not None:
                lay = move_extra.layout()
                for i in range(lay.count()):
                    item = lay.itemAt(i)
                    widget = item.widget() if item is not None else None
                    lay.setStretch(i, 1 if widget is getattr(self, 'w_move_options_block', None) else 0)
        self._layout_mid_groups()

    def _mid_available_height(self):
        return self._mid_param_region_height()

    def _clear_mid_param_stretch(self):
        def _zero(layout):
            if layout is None:
                return
            for idx in range(layout.count()):
                item = layout.itemAt(idx)
                if item is None:
                    continue
                layout.setStretch(idx, 0)
                w = item.widget()
                if w is not None and w.layout() is not None:
                    if w in (
                        getattr(self, 'w_snap_options_block', None),
                        getattr(self, 'w_snap_left_inner', None),
                        getattr(self, 'field_options_extra', None),
                        getattr(self, 'move_options_extra', None),
                        getattr(self, 'w_move_options_block', None),
                        getattr(self, 'w_move_left_inner', None),
                        getattr(self, 'w_end_fields', None),
                        getattr(self, 'w_tol_row', None),
                    ):
                        _zero(w.layout())
        _zero(getattr(self, '_options_group_layout', None))
        self._strip_mid_gaps(getattr(self, 'lay_snap_left', None))
        self._strip_mid_gaps(getattr(self, 'lay_move_rows', None))
        host = getattr(self, 'field_options_extra', None)
        self._strip_mid_gaps(host.layout() if host is not None else None)

    def _sync_header_row_heights(self):
        """Both column headers stay one fixed row so a longer translation cannot cover the list or the combo."""
        headers = [
            getattr(self, 'w_target_title', None),
            getattr(self, 'w_snap_mode_preset', None),
            getattr(self, 'w_field_ref_header', None),
            getattr(self, 'w_move_ref_header', None),
        ]
        for widget in headers:
            if widget is None:
                continue
            widget.setFixedHeight(44)
            widget.setMinimumWidth(0)
        stack = getattr(self, 'right_header_stack', None)
        if stack is not None:
            stack.setFixedHeight(44)
            stack.setMinimumWidth(0)
        title = getattr(self, 'lbl_snap_ref_title', None)
        if title is not None:
            title.setWordWrap(False)
            title.setMinimumWidth(0)
            title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

    def _settle_main_layout(self):
        """Settle 5:2 / 1:1 column stretches against the real width after the widget is shown.

        Does not hard-code 250/200, so a narrower window can still wrap. Not a timer or fake click.
        """
        if getattr(self, 'target_layer_list', None) is None:
            return
        for w in (
            self.target_layer_list,
            getattr(self, 'w_snap_layer_right_wrap', None),
            getattr(self, 'ref_layer_list', None),
            getattr(self, 'target_filter_stack', None),
            getattr(self, 'ref_filter_stack', None),
            getattr(self, 'frame_left_col', None),
            getattr(self, 'frame_right_col', None),
            getattr(self, 'right_col', None),
        ):
            if w is not None:
                w.setMinimumWidth(0)
        gl = getattr(self, '_lists_layout', None)
        if gl is not None:
            gl.setColumnStretch(0, 1)
            gl.setColumnStretch(1, 1)
            try:
                gl.setColumnMinimumWidth(0, 0)
                gl.setColumnMinimumWidth(1, 0)
            except Exception:  # nosec B110
                pass
            gl.invalidate()
        cl = getattr(self, '_columns_layout', None)
        if cl is not None and cl.count() >= 2:
            cl.setStretch(0, 5)
            cl.setStretch(1, 2)
            cl.invalidate()
        if self.layout() is not None:
            self.layout().activate()
        self.updateGeometry()
        self._distribute_mid_param_stretch()
        self._sync_header_row_heights()
        if self.layout() is not None:
            self.layout().activate()
        self.updateGeometry()

    def _apply_min_size_from_layout(self):
        """Floor only. The window size is 700×650 until the user resizes it, and that resize stays in memory."""
        self.setMinimumSize(640, 560)
        self._last_layout_min_height = 650

    def _refresh_output_combo(self):
        combo = getattr(self, 'combo_field_output', None)
        if combo is None:
            return
        prev = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(self.tr('直接修改图层'), 'direct')
        combo.addItem(self.tr('生成临时图层'), 'memory')
        idx = combo.findData(prev)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        combo.blockSignals(False)
        combo.setProperty('itemMsgids', ['直接修改图层', '生成临时图层'])

    def _stamp_static_combo_sources(self):
        mapping = {
            'combo_field_output': ['直接修改图层', '生成临时图层'],
            'combo_count_attach': ['端点（默认）', '任意折点', '沿线身'],
            'combo_overlap_scope': [
                '单独判断 + 单独输出',
                '单独判断 + 集合输出',
                '集合判断 + 单独输出',
                '集合判断 + 集合输出',
            ],
        }
        for name, sources in mapping.items():
            combo = getattr(self, name, None)
            if combo is not None and combo.count() == len(sources):
                combo.setProperty('itemMsgids', sources)

    def _configure_right_combos(self):
        for name in (
            'combo_snap_scheme', 'combo_snap_spatial_mode', 'combo_snap_ref_mode',
            'combo_field_output',
            'combo_named_field', 'combo_ref_field', 'combo_spatial_mode',
            'combo_multi_match', 'combo_field_scheme', 'combo_move_scheme',
            'combo_move_mode', 'combo_head_ref', 'combo_head_named',
            'combo_tail_ref', 'combo_tail_named',
        ):
            combo = getattr(self, name, None)
            if combo is not None:
                configure_fit_combo(combo)

    def _mode_short_src(self, mode=None):
        mode = mode or getattr(self, '_ui_mode', 'snap')
        return {'snap': '吸附', 'field': '命名', 'move': '移动'}.get(mode, '吸附')

    def _refill_translated_combos(self):
        try:
            self._refresh_snap_spatial_combo()
        except Exception:  # nosec B110
            pass
        try:
            self._refresh_field_combos()
        except Exception:  # nosec B110
            pass
        try:
            self._init_multi_combo()
        except Exception:  # nosec B110
            pass
        try:
            self._refresh_move_mode_combo()
        except Exception:  # nosec B110
            pass
        try:
            self._retranslate_snap_ref_mode_combo()
        except Exception:  # nosec B110
            pass
        try:
            self._refresh_output_combo()
        except Exception:  # nosec B110
            pass
        for _fn in ('_refresh_snap_scheme_combo', '_refresh_field_scheme_combo', '_refresh_move_scheme_combo'):
            try:
                getattr(self, _fn)()
            except Exception:  # nosec B110
                pass
        self._stamp_static_combo_sources()
        try:
            if hasattr(self, 'row_snap_mode_param') and hasattr(self, 'combo_snap_spatial_mode'):
                self.row_snap_mode_param.set_mode(self.combo_snap_spatial_mode.currentData())
            if hasattr(self, 'row_field_mode_param') and hasattr(self, 'combo_spatial_mode'):
                self.row_field_mode_param.set_mode(self.combo_spatial_mode.currentData())
        except Exception:  # nosec B110
            pass

    def closeEvent(self, event):
        try:
            self._persist_settings()
        except Exception:  # nosec B110
            pass
        try:
            remove_move_preview_layers(self.project)
        except Exception:  # nosec B110
            pass
        super().closeEvent(event)

    def _cat_store(self):
        mode = getattr(self, '_ui_mode', None)
        if mode == 'field':
            return self._cat_field
        if mode == 'move':
            return self._cat_move
        return self._cat_snap

    def _item_layer_name(self, item):
        if item is None:
            return ''
        name = item.data(ROLE_LAYER_NAME)
        if isinstance(name, str) and name:
            return name
        # Never parse the visible caption (it may include categories and a count).
        return ''

    def _harvest_list_categories(self, lw, side):
        if getattr(self, '_skip_cat_harvest', False) or lw is None:
            return
        store = self._cat_store().setdefault(side, {})
        for i in range(lw.count()):
            it = lw.item(i)
            if it.data(ROLE_LAYER_NAME) is None:
                continue
            name = self._item_layer_name(it)
            cats = it.data(ROLE_CATS)
            if not isinstance(cats, list) or not name:
                continue
            if cats:
                store[name] = [
                    {'label': c.get('label'), 'filter_expr': c.get('filter_expr')}
                    for c in cats if isinstance(c, dict) and c.get('filter_expr')
                ]

    def _set_layer_item_caption(self, item, has_categories=None, labels=None, feature_count=None):
        """Visible text only. Real name stays in ROLE_LAYER_NAME."""
        if item is None:
            return
        name = item.data(ROLE_LAYER_NAME) or ''
        if labels is None:
            cats = item.data(ROLE_CATS) or []
            labels = [c.get('label') for c in cats if isinstance(c, dict)]
        if has_categories is None:
            has_categories = bool(item.data(ROLE_HAS_CATS))
        if feature_count is None:
            feature_count = item.data(ROLE_FEATURE_COUNT)
        if feature_count is not None:
            item.setData(ROLE_FEATURE_COUNT, int(feature_count) if int(feature_count) >= 0 else 0)
        item.setText(layer_item_display(name, has_categories, labels, feature_count=feature_count))

    def _add_project_layer_item(self, lw, layer, side):
        saved = (self._cat_store().get(side) or {}).get(layer.name())
        live, picked = align_saved_categories(layer, saved if isinstance(saved, list) else [])
        item = QListWidgetItem()
        item.setData(ROLE_LAYER_ID, layer.id())
        item.setData(ROLE_LAYER_NAME, layer.name())
        item.setData(ROLE_HAS_CATS, bool(live))
        item.setData(ROLE_CATS, picked)
        item.setData(ROLE_FEATURE_COUNT, safe_feature_count(layer))
        self._set_layer_item_caption(
            item,
            has_categories=bool(live),
            labels=[c.get('label') for c in picked],
            feature_count=safe_feature_count(layer),
        )
        if live:
            item.setToolTip(self.tr('点击图层名前的 ◆◆ 选择分类（点行内其它位置只选中图层，不弹分类）。'))
        lw.addItem(item)
        return item

    def _categories_map_from_list(self, lw):
        out = {}
        for it in lw.selectedItems():
            name = self._item_layer_name(it)
            cats = it.data(ROLE_CATS) or []
            if not name or not cats:
                continue
            out[name] = [
                {'label': c.get('label'), 'filter_expr': c.get('filter_expr')}
                for c in cats if isinstance(c, dict) and c.get('filter_expr')
            ]
        return normalize_category_map(out)

    def _filters_for_list(self, lw, layers):
        return filters_by_layer_id(layers, self._categories_map_from_list(lw))

    def _names_with_categories(self, names, cat_map):
        cat_map = cat_map if isinstance(cat_map, dict) else {}
        parts = []
        for name in names or []:
            items = cat_map.get(name) or []
            labels = [it.get('label') for it in items if isinstance(it, dict)]
            parts.append(format_layer_caption(name, labels))
        return ','.join(parts)

    def _trim_category_map(self, raw, names):
        mapping = normalize_category_map(raw)
        keep = set(names or [])
        return {name: mapping[name] for name in mapping if name in keep}

    def _load_cat_json(self, key):
        raw = settings_value(self.settings, key, '{}', typ=str)
        try:
            data = json.loads(raw) if raw else {}
        except Exception:
            data = {}
        return normalize_category_map(data)

    def _category_mark_hit(self, lw, item, pos):
        if lw is None or item is None or pos is None:
            return False
        rect = lw.visualItemRect(item)
        font = QFont(lw.font())
        font.setBold(True)
        fm = QFontMetrics(font)
        mark_w = fm.horizontalAdvance(CAT_MARK + ' ')
        left = rect.x() + 6
        x = pos.x()
        y = pos.y()
        return (left <= x <= left + mark_w) and (rect.y() <= y <= rect.y() + rect.height())

    def _layer_list_of(self, watched):
        for lw in (self.target_layer_list, self.ref_layer_list):
            if watched is lw.viewport():
                return lw
        return None

    def eventFilter(self, watched, event):
        # ExtendedSelection, same as the local plugin: no modifier selects only
        # that row and does not clear it on a second click; Ctrl toggles one
        # row; Shift selects a range; a drag selects the rows crossed.
        # Empty space is swallowed so it does not clear. The category mark
        # opens the picker and leaves the current selection as it is.
        lw = self._layer_list_of(watched)
        if lw is None:
            return super().eventFilter(watched, event)
        et = event.type()
        if et not in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease, QEvent.Type.MouseButtonDblClick):
            return super().eventFilter(watched, event)
        left = getattr(Qt, 'LeftButton', None)
        if event.button() != left:
            return super().eventFilter(watched, event)
        pos = pointer_pos(event)
        item = lw.itemAt(pos)
        blank = getattr(self, '_layer_blank_press', None)
        if item is None:
            # A drag that starts on a row and ends on empty space must still
            # reach the list, so only a press that itself began on empty space
            # is swallowed. That is what would otherwise clear the selection.
            if et == QEvent.Type.MouseButtonPress:
                self._layer_blank_press = lw
                return True
            if et == QEvent.Type.MouseButtonDblClick:
                return True
            if et == QEvent.Type.MouseButtonRelease and blank is lw:
                self._layer_blank_press = None
                return True
            return super().eventFilter(watched, event)
        if et == QEvent.Type.MouseButtonPress:
            self._layer_blank_press = None
            if item.data(ROLE_HAS_CATS) and self._category_mark_hit(lw, item, pos):
                self._pick_item_categories(lw, item)
                return True
        return super().eventFilter(watched, event)

    def _optional_layer_total(self, layer):
        if layer is None:
            return None
        try:
            n = layer.featureCount()
        except Exception:
            return None
        try:
            n = int(n)
        except (TypeError, ValueError):
            return None
        if n < 0:
            return None
        return n

    def _caption_with_optional_count(self, name, count):
        if count is None:
            return name or ''
        return layer_item_display(name or '', False, [], feature_count=count)

    def _sync_open_category_dialog(self):
        sess = getattr(self, '_open_cat_session', None)
        if not sess:
            return
        dlg = sess.get('dlg')
        layer = sess.get('layer')
        boxes = sess.get('boxes') or []
        title = sess.get('title')
        if dlg is None or not dlg.isVisible():
            self._open_cat_session = None
            return
        dlg.setWindowTitle(self.tr('选择分类'))
        if title is not None:
            total = self._optional_layer_total(layer)
            title.setText(self._caption_with_optional_count(sess.get('name') or '', total))
        for cb in boxes:
            cat = cb.property('cat') or {}
            label = cat.get('label') or ''
            n = count_features_by_expr(layer, cat.get('filter_expr'))
            cb.setText(self._caption_with_optional_count(label, n))

    def _pick_item_categories(self, lw, item):
        name = self._item_layer_name(item)
        found = self.project.mapLayersByName(name)
        if not found:
            return
        layer = found[0]
        live = layer_filter_categories(layer)
        if not live:
            item.setData(ROLE_HAS_CATS, False)
            item.setData(ROLE_CATS, [])
            self._set_layer_item_caption(item, has_categories=False, labels=[])
            QMessageBox.information(self, self.tr('提示'), self.tr('当前没有可筛选的分类'))
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr('选择分类'))
        dlg.resize(360, 420)
        lay = QVBoxLayout(dlg)
        title = QLabel()
        title.setText(self._caption_with_optional_count(name, self._optional_layer_total(layer)))
        title.setWordWrap(True)
        lay.addWidget(title)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        host = QWidget()
        box_lay = QVBoxLayout(host)
        saved = [c for c in (item.data(ROLE_CATS) or []) if isinstance(c, dict)]
        # Empty ROLE_CATS (including never subset-checked) means the whole layer: check all.
        selected = {c.get('filter_expr') for c in saved if c.get('filter_expr')}
        default_all = not selected
        boxes = []
        for cat in live:
            label = cat.get('label') or ''
            n = count_features_by_expr(layer, cat.get('filter_expr'))
            cb = QCheckBox(self._caption_with_optional_count(label, n))
            cb.setChecked(True if default_all else (cat.get('filter_expr') in selected))
            cb.setProperty('cat', cat)
            boxes.append(cb)
            box_lay.addWidget(cb)
        box_lay.addStretch(1)
        scroll.setWidget(host)
        lay.addWidget(scroll, 1)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        localize_button_box(bb)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        lay.addWidget(bb)
        self._open_cat_session = {
            'dlg': dlg, 'layer': layer, 'boxes': boxes, 'title': title, 'name': name,
        }
        try:
            result = run_dialog(dlg)
        finally:
            self._open_cat_session = None
        if result != QDialog.DialogCode.Accepted:
            return
        picked = []
        for cb in boxes:
            if cb.isChecked():
                cat = cb.property('cat')
                if isinstance(cat, dict):
                    picked.append({'label': cat.get('label'), 'filter_expr': cat.get('filter_expr')})
        # Confirming with none checked still means whole-layer / all selected.
        if not picked:
            item.setData(ROLE_CATS, [])
            self._set_layer_item_caption(item, has_categories=True, labels=[])
            side = 'target' if lw is self.target_layer_list else 'ref'
            self._cat_store().setdefault(side, {}).pop(name, None)
            return
        item.setData(ROLE_CATS, picked)
        self._set_layer_item_caption(item, has_categories=True, labels=[c.get('label') for c in picked])
        side = 'target' if lw is self.target_layer_list else 'ref'
        store = self._cat_store().setdefault(side, {})
        store[name] = picked

    def _select_layer_names(self, lw, names):
        want = set(names or [])
        lw.blockSignals(True)
        lw.clearSelection()
        for i in range(lw.count()):
            it = lw.item(i)
            if self._item_layer_name(it) in want:
                it.setSelected(True)
        lw.blockSignals(False)

    def _fill_end_field_combos(self, named_layers, ref_layers):
        prev = {
            'head_ref': self._restore_end_head_ref or self.combo_head_ref.currentData(),
            'head_named': self._restore_end_head_named or self.combo_head_named.currentData(),
            'tail_ref': self._restore_end_tail_ref or self.combo_tail_ref.currentData(),
            'tail_named': self._restore_end_tail_named or self.combo_tail_named.currentData(),
        }
        self._restore_end_head_ref = None
        self._restore_end_head_named = None
        self._restore_end_tail_ref = None
        self._restore_end_tail_named = None
        combos = (self.combo_head_ref, self.combo_head_named, self.combo_tail_ref, self.combo_tail_named)
        for combo in combos:
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(self.tr('（不写）'), '')
        if named_layers:
            names = _field_intersection(named_layers)
            if not names:
                names = [named_layers[0].fields().at(i).name() for i in range(named_layers[0].fields().count())]
            for field_name in names:
                label = field_display_label_from_layer(named_layers[0], field_name)
                self.combo_head_named.addItem(label, field_name)
                self.combo_tail_named.addItem(label, field_name)
        if ref_layers:
            layer0 = ref_layers[0]
            for i in range(layer0.fields().count()):
                field = layer0.fields().at(i)
                label = field_display_label(field)
                self.combo_head_ref.addItem(label, field.name())
                self.combo_tail_ref.addItem(label, field.name())
        for combo, key in (
            (self.combo_head_ref, 'head_ref'),
            (self.combo_head_named, 'head_named'),
            (self.combo_tail_ref, 'tail_ref'),
            (self.combo_tail_named, 'tail_named'),
        ):
            wanted = prev.get(key) or ''
            idx = combo.findData(wanted) if wanted else 0
            if idx < 0 and wanted and (named_layers or ref_layers):
                layer_for = named_layers[0] if key.endswith('named') and named_layers else (ref_layers[0] if ref_layers else None)
                if layer_for is not None:
                    resolved = resolve_field_name(layer_for, wanted)
                    if resolved:
                        idx = combo.findData(resolved)
            combo.setCurrentIndex(idx if idx >= 0 else 0)
            combo.blockSignals(False)

    def _sync_end_field_rows(self, *_args):
        if not hasattr(self, 'w_end_fields'):
            return
        end = self.combo_spatial_mode.currentData() == LP_END_FIELDS
        self.w_end_fields.setVisible(end)
        if end:
            self.combo_multi_match.setEnabled(True)
            self.combo_multi_match.setToolTip(self._end_fields_multi_tip_text())
        else:
            self._update_multi_match_for_ref_source()
        self._place_tol_clusters()
        if getattr(self, 'lay_snap_left', None) is not None:
            self._distribute_mid_param_stretch()

    def _place_tol_clusters(self):
        """Toggle mid-group visibility only; never reparent or stretch groups."""
        if not hasattr(self, 'w_tol_cluster'):
            return
        end = (
            getattr(self, '_ui_mode', None) == 'field'
            and hasattr(self, 'combo_spatial_mode')
            and self.combo_spatial_mode.currentData() == LP_END_FIELDS
        )
        for block in (getattr(self, 'w_named_field_block', None), getattr(self, 'w_ref_field_block', None)):
            if block is not None:
                block.setVisible(not end)
        if hasattr(self, 'lbl_named_field'):
            self.lbl_named_field.setVisible(not end)
            self.combo_named_field.setVisible(not end)
            self.lbl_ref_field.setVisible(not end)
            self.combo_ref_field.setVisible(not end)
        self.w_tol_cluster.setVisible(True)
        snap = getattr(self, '_ui_mode', None) == 'snap'
        show_out = not snap
        self.w_out_cluster.setVisible(show_out)
        self.lbl_field_output.setVisible(show_out)
        self.combo_field_output.setVisible(show_out)
        row_host = getattr(self, 'w_tol_row', None)
        if row_host is not None:
            row_host.setVisible(False)

    def _refresh_field_scheme_combo(self):
        if not hasattr(self, 'combo_field_scheme'):
            return
        self._field_scheme_loading = True
        self.combo_field_scheme.blockSignals(True)
        self.combo_field_scheme.clear()
        self.combo_field_scheme.addItem(self.tr('自定义（当前）'), self.FIELD_SCHEME_CUSTOM)
        for name in sorted(self._field_schemes.keys()):
            if isinstance(self._field_schemes.get(name), list):
                self.combo_field_scheme.addItem(name, name)
        idx = self.combo_field_scheme.findData(self._active_field_scheme)
        if idx < 0:
            self._active_field_scheme = self.FIELD_SCHEME_CUSTOM
            idx = 0
        self.combo_field_scheme.setCurrentIndex(idx)
        self.combo_field_scheme.blockSignals(False)
        self._field_scheme_loading = False
        has_scheme = any(isinstance(v, list) for v in self._field_schemes.values())
        self.btn_field_scheme_export.setEnabled(has_scheme)
        if hasattr(self, 'btn_field_scheme_view'):
            self.btn_field_scheme_view.setEnabled(self._active_field_scheme in self._field_schemes)

    def _on_field_scheme_changed(self, _index):
        if self._field_scheme_loading:
            return
        name = self.combo_field_scheme.currentData()
        self._active_field_scheme = name or self.FIELD_SCHEME_CUSTOM
        if hasattr(self, 'btn_field_scheme_view'):
            self.btn_field_scheme_view.setEnabled(self._active_field_scheme in self._field_schemes)

    def _current_field_scheme_payload(self):
        self._harvest_list_categories(self.target_layer_list, 'target')
        self._harvest_list_categories(self.ref_layer_list, 'ref')
        ref_src = self.combo_ref_field.currentData()
        if ref_src == LAYER_NAME_VALUE:
            ref_store = LAYER_NAME_SETTINGS_KEY
        else:
            ref_store = ref_src or ''
        return {
            'target_names': [self._item_layer_name(i) for i in self.target_layer_list.selectedItems()],
            'ref_names': [self._item_layer_name(i) for i in self.ref_layer_list.selectedItems()],
            'target_categories': self._categories_map_from_list(self.target_layer_list),
            'ref_categories': self._categories_map_from_list(self.ref_layer_list),
            'named_field': self.combo_named_field.currentData() or '',
            'ref_value_source': ref_store,
            'spatial_mode': self.combo_spatial_mode.currentData() or '',
            'multi_strategy': self.combo_multi_match.currentData() or '',
            'tolerance': float(self.spin_tolerance.value()),
            'field_output_mode': self.combo_field_output.currentData() or 'direct',
            'element_count_rule': dict(self._count_rule),
            'end_head_ref': self.combo_head_ref.currentData() or '',
            'end_head_named': self.combo_head_named.currentData() or '',
            'end_tail_ref': self.combo_tail_ref.currentData() or '',
            'end_tail_named': self.combo_tail_named.currentData() or '',
            'mode_param': self._current_mode_param(self.combo_spatial_mode.currentData()),
            'field_geom_target': self._geom_storage_key(self._field_target_geom),
            'field_geom_ref': self._geom_storage_key(self._field_ref_geom),
            'field_grp_target': self._field_group_path_target or '',
            'field_grp_ref': self._field_group_path_ref or '',
        }

    def _apply_field_scheme_payload(self, data):
        if not isinstance(data, dict):
            return
        self._field_scheme_loading = True
        try:
            self._field_group_path_target = data.get('field_grp_target') or ''
            self._field_group_path_ref = data.get('field_grp_ref') or ''
            self._field_target_geom = self._geom_from_storage_key(data.get('field_geom_target') or 'all')
            self._field_ref_geom = self._geom_from_storage_key(data.get('field_geom_ref') or 'all')
            self._cat_field['target'] = normalize_category_map(data.get('target_categories'))
            self._cat_field['ref'] = normalize_category_map(data.get('ref_categories'))
            try:
                self.spin_tolerance.setValue(float(data.get('tolerance', self.spin_tolerance.value())))
            except Exception:  # nosec B110
                pass
            fo = data.get('field_output_mode') or 'direct'
            fidx = self.combo_field_output.findData(fo)
            if fidx >= 0:
                self.combo_field_output.setCurrentIndex(fidx)
            rule = data.get('element_count_rule')
            if isinstance(rule, dict):
                self._count_rule = rule
            named = data.get('named_field') or ''
            self._restore_field_named = named or None
            ref = data.get('ref_value_source') or ''
            if is_layer_title_token(ref):
                ref = LAYER_NAME_VALUE
            elif is_element_count_token(ref):
                ref = REF_ELEMENT_COUNT
            self._restore_field_ref = ref or None
            self._restore_field_spatial = data.get('spatial_mode') or None
            self._restore_field_multi = data.get('multi_strategy') or None
            self._restore_end_head_ref = data.get('end_head_ref') or None
            self._restore_end_head_named = data.get('end_head_named') or None
            self._restore_end_tail_ref = data.get('end_tail_ref') or None
            self._restore_end_tail_named = data.get('end_tail_named') or None
            sm_load = data.get('spatial_mode')
            if sm_load and data.get('mode_param') is not None:
                self._mode_params[sm_load] = data.get('mode_param')
            self._skip_cat_harvest = True
            try:
                self._reload_field_side_list('target', refresh=False)
                self._reload_field_side_list('ref', refresh=False)
            finally:
                self._skip_cat_harvest = False
            self._select_layer_names(self.target_layer_list, data.get('target_names') or [])
            self._select_layer_names(self.ref_layer_list, data.get('ref_names') or [])
            self._refresh_field_combos()
        finally:
            self._field_scheme_loading = False

    def _clean_field_task(self, task):
        src = task if isinstance(task, dict) else {}
        clean = dict(src)
        clean['method_name'] = str(src.get('method_name') or src.get('run_name') or '')
        clean['run_name'] = str(src.get('run_name') or clean['method_name'] or '')
        clean['target_names'] = [str(n) for n in (src.get('target_names') or []) if n]
        clean['ref_names'] = [str(n) for n in (src.get('ref_names') or []) if n]
        clean['target_categories'] = normalize_category_map(src.get('target_categories'))
        clean['ref_categories'] = normalize_category_map(src.get('ref_categories'))
        return clean

    def _normalize_field_schemes(self, raw):
        """只保留子任务列表。上一版「一个方案一套参数」直接丢掉。"""
        out = {}
        if not isinstance(raw, dict):
            return out
        for name, body in raw.items():
            if not isinstance(name, str) or not name or name == self.FIELD_SCHEME_CUSTOM:
                continue
            if not isinstance(body, list):
                continue
            out[name] = [self._clean_field_task(t) for t in body if isinstance(t, dict)]
        return out

    def _field_task_display_text(self, idx, task):
        tnames = self._names_with_categories(task.get('target_names') or [], task.get('target_categories'))
        rnames = self._names_with_categories(task.get('ref_names') or [], task.get('ref_categories'))
        mode = task.get('spatial_mode') or ''
        mode_show = spatial_mode_label(mode) or '-'
        mp_txt = format_mode_param(mode, task.get('mode_param'))
        if mp_txt:
            mode_show = '{0}（{1}）'.format(mode_show, mp_txt)
        out = self.tr('临时图层') if task.get('field_output_mode') == 'memory' else self.tr('直接修改')
        return self.tr('{0}. {1} | 目标:{2} | 参考:{3} | {4} | 容差:{5} | {6}').format(
            idx,
            task.get('method_name') or task.get('run_name') or self.tr('子任务'),
            tnames or '-',
            rnames or '-',
            mode_show,
            task.get('tolerance', 0.0),
            out,
        )

    def _choose_field_scheme_names_dialog(self):
        names = sorted(k for k, v in self._field_schemes.items() if isinstance(v, list))
        if not names:
            QMessageBox.information(self, self.tr('提示'), self.tr('暂无可加入的方案，请先在方案管理里新建方案。'))
            return []
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr('加入到命名方案'))
        lay = QVBoxLayout(dlg)
        lw = QListWidget()
        lw.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for name in names:
            lw.addItem(name)
        lay.addWidget(lw)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        localize_button_box(bb)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        lay.addWidget(bb)
        if run_dialog(dlg) != QDialog.DialogCode.Accepted:
            return []
        return [i.text() for i in lw.selectedItems()]

    def _field_task_ready(self, payload):
        if not payload.get('target_names') or not payload.get('ref_names'):
            return self.tr('请先选择被命名图层和参考图层。')
        if payload.get('spatial_mode') == LP_END_FIELDS:
            used = 0
            for title, a, b in (
                (self.tr('线头'), payload.get('end_head_ref'), payload.get('end_head_named')),
                (self.tr('线尾'), payload.get('end_tail_ref'), payload.get('end_tail_named')),
            ):
                a = (a or '').strip()
                b = (b or '').strip()
                if a or b:
                    if not a or not b:
                        return self.tr('{0}需要同时选择点字段和线字段，或都留空。').format(title)
                    used += 1
            if not used:
                return self.tr('请至少填写线头或线尾的一组字段。')
            return ''
        if not payload.get('named_field') or not payload.get('ref_value_source') or not payload.get('spatial_mode'):
            return self.tr('请完整选择字段与模式。')
        return ''

    def _add_field_task(self):
        payload = self._current_field_scheme_payload()
        err = self._field_task_ready(payload)
        if err:
            QMessageBox.warning(self, self.tr('提示'), err)
            return
        mname, ok = ask_text(self, self.tr('方法名称'), self.tr('请输入本次添加的方法名称：'))
        if not ok:
            return
        mname = (mname or '').strip() or time.strftime('%Y%m%d_%H%M%S')
        payload['method_name'] = mname
        payload['run_name'] = mname
        chosen = self._choose_field_scheme_names_dialog()
        if not chosen:
            return
        for name in chosen:
            tasks = self._field_schemes.setdefault(name, [])
            if not isinstance(tasks, list):
                tasks = []
                self._field_schemes[name] = tasks
            tasks.append(self._clean_field_task(payload))
        self._persist_settings()
        QMessageBox.information(self, self.tr('提示'), self.tr('已加入 {0} 个方案。').format(len(chosen)))

    def _view_field_scheme(self):
        name = self._active_field_scheme
        if name == self.FIELD_SCHEME_CUSTOM or name not in self._field_schemes:
            QMessageBox.information(self, self.tr('提示'), self.tr('请选择一个命名方案。'))
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr('方案任务 - {0}').format(name))
        dlg.resize(760, 460)
        lay = QVBoxLayout(dlg)
        lw = QListWidget()
        lw.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        lay.addWidget(lw, 1)

        def _fill(focus=None):
            lw.clear()
            arr = self._field_schemes.get(name) or []
            for i, task in enumerate(arr):
                it = QListWidgetItem(self._field_task_display_text(i + 1, task))
                it.setData(Qt.ItemDataRole.UserRole, i)
                missing = []
                for layer_name in (task.get('target_names') or []) + (task.get('ref_names') or []):
                    if layer_name and not self.project.mapLayersByName(layer_name):
                        missing.append(layer_name)
                if missing:
                    it.setForeground(QBrush(QColor('#C62828')))
                    it.setToolTip(self.tr('工程中找不到：{0}').format('、'.join(missing)))
                lw.addItem(it)
                if focus is not None and i == focus:
                    it.setSelected(True)
                    lw.setCurrentItem(it)

        def _selected_indexes():
            idxs = []
            for it in lw.selectedItems():
                val = it.data(Qt.ItemDataRole.UserRole)
                if isinstance(val, int):
                    idxs.append(val)
            return sorted(set(idxs))

        def _move(delta):
            arr = self._field_schemes.get(name) or []
            idxs = _selected_indexes()
            if not idxs or not arr:
                return
            order = idxs if delta < 0 else list(reversed(idxs))
            moved = None
            for i in order:
                j = i + delta
                if j < 0 or j >= len(arr):
                    continue
                if delta < 0 and j in idxs:
                    continue
                if delta > 0 and j in idxs:
                    continue
                arr[i], arr[j] = arr[j], arr[i]
                moved = j
            if moved is None:
                return
            self._persist_settings()
            _fill(moved)

        def _edit():
            idxs = _selected_indexes()
            if len(idxs) != 1:
                QMessageBox.information(self, self.tr('提示'), self.tr('请选择一条子任务。'))
                return
            arr = self._field_schemes.get(name) or []
            updated = self._edit_field_task_dialog(arr[idxs[0]])
            if updated is None:
                return
            arr[idxs[0]] = updated
            self._persist_settings()
            _fill(idxs[0])

        def _delete():
            idxs = _selected_indexes()
            if not idxs:
                return
            reply = QMessageBox.question(
                dlg, self.tr('删除子任务'),
                self.tr('确定删除选中的 {0} 条子任务吗？').format(len(idxs)),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            arr = self._field_schemes.get(name) or []
            for i in reversed(idxs):
                if 0 <= i < len(arr):
                    arr.pop(i)
            self._persist_settings()
            _fill()

        def _load_current():
            idxs = _selected_indexes()
            if len(idxs) != 1:
                QMessageBox.information(self, self.tr('提示'), self.tr('请选择一条子任务。'))
                return
            arr = self._field_schemes.get(name) or []
            self._apply_field_scheme_payload(arr[idxs[0]])
            QMessageBox.information(self, self.tr('提示'), self.tr('已载入到当前参数，可修改后再添加。'))

        row = QHBoxLayout()
        btn_up = QPushButton(self.tr('上移'))
        btn_down = QPushButton(self.tr('下移'))
        btn_edit = QPushButton(self.tr('编辑'))
        btn_del = QPushButton(self.tr('删除'))
        btn_load = QPushButton(self.tr('载入当前'))
        btn_close = QPushButton(self.tr('关闭'))
        for b in (btn_up, btn_down, btn_edit, btn_del, btn_load, btn_close):
            b.setObjectName('schemeImportBtn')
            b.setFixedHeight(27)
            row.addWidget(b)
        btn_up.clicked.connect(lambda: _move(-1))
        btn_down.clicked.connect(lambda: _move(1))
        btn_edit.clicked.connect(_edit)
        btn_del.clicked.connect(_delete)
        btn_load.clicked.connect(_load_current)
        btn_close.clicked.connect(dlg.accept)
        lay.addLayout(row)
        _fill()
        run_dialog(dlg)

    def _edit_field_task_dialog(self, task):
        task = self._clean_field_task(task)
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr('编辑子任务'))
        dlg.resize(560, 640)
        lay = QVBoxLayout(dlg)
        grid = QGridLayout()
        name_edit = QLineEdit(task.get('method_name') or '')
        tol = QDoubleSpinBox()
        tol.setDecimals(6)
        tol.setRange(0.000001, 10000.0)
        tol.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        tol.setMinimumWidth(132)
        try:
            tol.setValue(float(task.get('tolerance') or 0.00001))
        except Exception:
            tol.setValue(0.00001)
        out = QComboBox()
        out.addItem(self.tr('直接修改图层'), 'direct')
        out.addItem(self.tr('生成临时图层'), 'memory')
        oidx = out.findData(task.get('field_output_mode') or 'direct')
        if oidx >= 0:
            out.setCurrentIndex(oidx)
        mode = QComboBox()
        mode.setEditable(True)
        stored_mode = task.get('spatial_mode') or ''
        t_layers, _m1 = self._layers_from_names(task.get('target_names'))
        r_layers, _m2 = self._layers_from_names(task.get('ref_names'))
        if t_layers and r_layers:
            for entry in spatial_mode_choices(t_layers[0], r_layers[0]):
                mode.addItem(entry[1], entry[0])
                mode.setItemData(mode.count() - 1, entry[2], Qt.ItemDataRole.ToolTipRole)
        if stored_mode and mode.findData(stored_mode) < 0:
            mode.addItem(spatial_mode_label(stored_mode), stored_mode)
        midx = mode.findData(stored_mode)
        if midx >= 0:
            mode.setCurrentIndex(midx)
        elif stored_mode:
            mode.setCurrentText(stored_mode)
        multi = QComboBox()
        for code, label in multi_match_choices():
            multi.addItem(label, code)
            multi.setItemData(multi.count() - 1, multi_match_tip(code), Qt.ItemDataRole.ToolTipRole)
        multi.setToolTip(_i18n_tr(MULTI_MATCH_COMMON_TIP))
        mm = task.get('multi_strategy') or 'nearest'
        mmidx = multi.findData(mm)
        if mmidx >= 0:
            multi.setCurrentIndex(mmidx)
        named = QLineEdit(task.get('named_field') or '')
        refv = QLineEdit(task.get('ref_value_source') or '')
        head_ref = QLineEdit(task.get('end_head_ref') or '')
        head_named = QLineEdit(task.get('end_head_named') or '')
        tail_ref = QLineEdit(task.get('end_tail_ref') or '')
        tail_named = QLineEdit(task.get('end_tail_named') or '')
        rows = (
            (self.tr('方法名称'), name_edit),
            (self.tr('容差'), tol),
            (self.tr('输出'), out),
            (self.tr('空间模式'), mode),
            (self.tr('多匹配'), multi),
            (self.tr('被命名字段'), named),
            (self.tr('参考取值'), refv),
            (self.tr('头点字段'), head_ref),
            (self.tr('头写入线字段'), head_named),
            (self.tr('尾点字段'), tail_ref),
            (self.tr('尾写入线字段'), tail_named),
        )
        for i, (label, widget) in enumerate(rows):
            grid.addWidget(QLabel(label), i, 0)
            grid.addWidget(widget, i, 1)
        lay.addLayout(grid)
        field_mode_row = ModeParamRow()
        field_mode_row.set_mode(stored_mode, task.get('mode_param'))
        mode.currentIndexChanged.connect(
            lambda _i: field_mode_row.set_mode(mode.currentData(), field_mode_row.value() if mode.currentData() == field_mode_row._code else self._mode_params.get(mode.currentData()))
        )
        lay.addWidget(field_mode_row)

        def _name_box(title, names):
            box = QGroupBox(title)
            box_lay = QVBoxLayout(box)
            lst = QListWidget()
            lst.setMaximumHeight(96)
            for n in names or []:
                if n:
                    lst.addItem(str(n))
            box_lay.addWidget(lst)
            row = QHBoxLayout()
            edit = QLineEdit()
            edit.setPlaceholderText(self.tr('图层名称'))
            btn_add = QPushButton(self.tr('添加'))
            btn_rm = QPushButton(self.tr('移除'))
            row.addWidget(edit, 1)
            row.addWidget(btn_add)
            row.addWidget(btn_rm)
            box_lay.addLayout(row)

            def _add():
                text = (edit.text() or '').strip()
                if text:
                    lst.addItem(text)
                    edit.clear()

            def _rm():
                for it in lst.selectedItems():
                    lst.takeItem(lst.row(it))

            btn_add.clicked.connect(_add)
            btn_rm.clicked.connect(_rm)
            return box, lst

        box_t, list_t = _name_box(self.tr('被命名图层'), task.get('target_names'))
        box_r, list_r = _name_box(self.tr('参考图层'), task.get('ref_names'))
        lay.addWidget(box_t)
        lay.addWidget(box_r)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        localize_button_box(bb)
        lay.addWidget(bb)

        def _accept():
            targets = [list_t.item(i).text().strip() for i in range(list_t.count()) if list_t.item(i).text().strip()]
            refs = [list_r.item(i).text().strip() for i in range(list_r.count()) if list_r.item(i).text().strip()]
            sm = mode.currentData() or (mode.currentText() or '').strip()
            updated = dict(task)
            updated.update({
                'method_name': (name_edit.text() or '').strip() or task.get('method_name') or '',
                'run_name': (name_edit.text() or '').strip() or task.get('run_name') or '',
                'tolerance': float(tol.value()),
                'field_output_mode': out.currentData() or 'direct',
                'spatial_mode': sm,
                'multi_strategy': multi.currentData() or 'nearest',
                'named_field': (named.text() or '').strip(),
                'ref_value_source': (refv.text() or '').strip(),
                'end_head_ref': (head_ref.text() or '').strip(),
                'end_head_named': (head_named.text() or '').strip(),
                'end_tail_ref': (tail_ref.text() or '').strip(),
                'end_tail_named': (tail_named.text() or '').strip(),
                'mode_param': field_mode_row.value(),
                'target_names': targets,
                'ref_names': refs,
                'target_categories': self._trim_category_map(task.get('target_categories'), targets),
                'ref_categories': self._trim_category_map(task.get('ref_categories'), refs),
            })
            err = self._field_task_ready(updated)
            if err:
                QMessageBox.warning(dlg, self.tr('提示'), err)
                return
            dlg.setProperty('task', self._clean_field_task(updated))
            dlg.accept()

        bb.accepted.connect(_accept)
        bb.rejected.connect(dlg.reject)
        if run_dialog(dlg) != QDialog.DialogCode.Accepted:
            return None
        return dlg.property('task')

    def _field_scheme_manage_menu(self):
        menu = QMenu(self)
        act_new = menu.addAction(self.tr('新建方案'))
        act_rename = menu.addAction(self.tr('重命名'))
        act_dup = menu.addAction(self.tr('复制方案'))
        act_del = menu.addAction(self.tr('删除'))
        has = self._active_field_scheme in self._field_schemes
        act_rename.setEnabled(has)
        act_dup.setEnabled(has)
        act_del.setEnabled(has)
        chosen = run_menu(menu, self.btn_field_scheme_manage.mapToGlobal(self.btn_field_scheme_manage.rect().bottomLeft()))
        if chosen is act_new:
            self._create_field_scheme()
        elif chosen is act_rename:
            self._rename_field_scheme()
        elif chosen is act_dup:
            self._duplicate_field_scheme()
        elif chosen is act_del:
            self._delete_field_scheme()

    def _create_field_scheme(self):
        name, ok = ask_text(self, self.tr('新建方案'), self.tr('请输入方案名称：'))
        if not ok:
            return
        name = (name or '').strip()
        if not name or name == self.FIELD_SCHEME_CUSTOM or name in self._field_schemes:
            QMessageBox.warning(self, self.tr('提示'), self.tr('请输入未占用的方案名称。'))
            return
        self._field_schemes[name] = []
        self._active_field_scheme = name
        self._refresh_field_scheme_combo()
        self._persist_settings()

    def _duplicate_field_scheme(self):
        old = self._active_field_scheme
        if old not in self._field_schemes:
            QMessageBox.information(self, self.tr('提示'), self.tr('请先选择一个命名方案。'))
            return
        base = '{0}{1}'.format(old, self.tr('副本'))
        name = base
        n = 2
        while name in self._field_schemes:
            name = '{0}{1}'.format(base, n)
            n += 1
        self._field_schemes[name] = copy.deepcopy(self._field_schemes.get(old) or [])
        self._active_field_scheme = name
        self._refresh_field_scheme_combo()
        self._persist_settings()

    def _rename_field_scheme(self):
        old = self._active_field_scheme
        if old == self.FIELD_SCHEME_CUSTOM or old not in self._field_schemes:
            QMessageBox.information(self, self.tr('提示'), self.tr('请先选择一个命名方案。'))
            return
        name, ok = ask_text(self, self.tr('重命名方案'), self.tr('请输入新名称：'), text=old)
        if not ok:
            return
        name = (name or '').strip()
        if not name:
            QMessageBox.warning(self, self.tr('提示'), self.tr('请输入未占用的方案名称。'))
            return
        if name == old:
            return
        if name == self.FIELD_SCHEME_CUSTOM or name in self._field_schemes:
            QMessageBox.warning(self, self.tr('提示'), self.tr('方案名称已存在，请更换名称。'))
            return
        self._field_schemes[name] = self._field_schemes.pop(old)
        self._active_field_scheme = name
        self._refresh_field_scheme_combo()
        self._persist_settings()

    def _delete_field_scheme(self):
        name = self._active_field_scheme
        if name == self.FIELD_SCHEME_CUSTOM or name not in self._field_schemes:
            QMessageBox.information(self, self.tr('提示'), self.tr('请先选择一个命名方案。'))
            return
        reply = QMessageBox.question(
            self,
            self.tr('删除方案'),
            self.tr('确定删除命名方案「{0}」吗？').format(name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._field_schemes.pop(name, None)
        self._active_field_scheme = self.FIELD_SCHEME_CUSTOM
        self._refresh_field_scheme_combo()
        self._persist_settings()

    def _export_field_schemes(self):
        names = sorted(k for k, v in self._field_schemes.items() if isinstance(v, list))
        if not names:
            QMessageBox.information(self, self.tr('提示'), self.tr('暂无可导出的命名方案。'))
            return
        picked = self._pick_checked_names(self.tr('选择要导出的命名方案'), names)
        if picked is None:
            return
        if not picked:
            QMessageBox.information(self, self.tr('提示'), self.tr('请至少勾选一个方案。'))
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr('导出命名方案'),
            'spatial_match_topo_adjust_field_schemes.json',
            'JSON (*.json)',
        )
        path = self._json_save_path(path)
        if not path:
            return
        payload = {
            'kind': self.FIELD_SCHEME_KIND,
            'schema_version': 2,
            'plugin_version': PLUGIN_VERSION,
            'generator': DISPLAY_NAME,
            'exported_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'schemes': {k: self._field_schemes[k] for k in picked if k in self._field_schemes},
        }
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            QMessageBox.information(
                self, self.tr('提示'), self.tr('已导出 {0} 个命名方案。').format(len(payload['schemes']))
            )
        except Exception as exc:
            QMessageBox.warning(self, self.tr('提示'), self.tr('导出失败：{0}').format(str(exc)))

    def _import_field_schemes(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr('导入命名方案'), '', 'JSON (*.json)')
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
        except Exception as exc:
            QMessageBox.warning(self, self.tr('提示'), self.tr('导入失败：{0}').format(str(exc)))
            return
        if isinstance(payload, dict) and is_move_scheme_kind(payload.get('kind')):
            QMessageBox.warning(self, self.tr('提示'), self.tr('这是移动方案，请在移动模式里导入（方案库与吸附分存）。'))
            return
        if not isinstance(payload, dict) or not is_field_scheme_kind(payload.get('kind')):
            QMessageBox.warning(self, self.tr('提示'), self.tr('这不是字段命名方案，请在吸附检测里导入吸附方案。'))
            return
        incoming = payload.get('schemes')
        if not isinstance(incoming, dict):
            QMessageBox.warning(self, self.tr('提示'), self.tr('文件格式无效。'))
            return
        merged = 0
        overwritten = 0
        for name, body in incoming.items():
            if not isinstance(name, str) or not name or name == self.FIELD_SCHEME_CUSTOM:
                continue
            if not isinstance(body, list):
                continue
            if name in self._field_schemes:
                overwritten += 1
            self._field_schemes[name] = [self._clean_field_task(t) for t in body if isinstance(t, dict)]
            merged += 1
        self._refresh_field_scheme_combo()
        self._persist_settings()
        if merged == 0:
            QMessageBox.warning(self, self.tr('提示'), self.tr('文件里没有子任务列表。'))
            return
        QMessageBox.information(
            self,
            self.tr('提示'),
            self.tr('导入完成：共 {0} 个命名方案（其中同名覆盖 {1} 个）。').format(merged, overwritten),
        )

    def load_all_layers(self):
        self._load_layers_to_list(self.target_layer_list, None)
        if getattr(self, '_ui_mode', None) == 'snap':
            self._refresh_snap_ref_layer_list()
        else:
            # Move (and any non-snap): always load the reference list.
            # _refresh_snap_ref_layer_list no-ops when not in snap, which left move empty
            # after leaving a field-mode (possibly group-filtered) reference list.
            self._load_layers_to_list(self.ref_layer_list, None)

    def _load_layers_to_list(self, list_widget, geom_type=None):
        side = 'target' if list_widget is self.target_layer_list else 'ref'
        self._harvest_list_categories(list_widget, side)
        prev_sel = [self._item_layer_name(i) for i in list_widget.selectedItems()]
        list_widget.clear()
        layers = self.project.mapLayers().values()
        for layer in layers:
            if not isinstance(layer, QgsVectorLayer):
                continue
            if geom_type is not None and layer.geometryType() != geom_type:
                continue
            item = self._add_project_layer_item(list_widget, layer, side)
            if layer.name() in prev_sel:
                item.setSelected(True)
        self._sync_snap_filter_checked(side, geom_type)

    def bind_signals(self):
        self.btn_help.clicked.connect(self._show_help)
        self.target_btn_point.clicked.connect(
            lambda: self._load_layers_to_list(self.target_layer_list, QgsWkbTypes.GeometryType.PointGeometry))
        self.target_btn_line.clicked.connect(
            lambda: self._load_layers_to_list(self.target_layer_list, QgsWkbTypes.GeometryType.LineGeometry))
        self.target_btn_polygon.clicked.connect(
            lambda: self._load_layers_to_list(self.target_layer_list, QgsWkbTypes.GeometryType.PolygonGeometry))
        self.target_btn_all.clicked.connect(
            lambda: self._load_layers_to_list(self.target_layer_list, None))

        self.field_tgt_btn_point.clicked.connect(
            lambda: self._set_field_geom_filter('target', QgsWkbTypes.GeometryType.PointGeometry))
        self.field_tgt_btn_line.clicked.connect(
            lambda: self._set_field_geom_filter('target', QgsWkbTypes.GeometryType.LineGeometry))
        self.field_tgt_btn_polygon.clicked.connect(
            lambda: self._set_field_geom_filter('target', QgsWkbTypes.GeometryType.PolygonGeometry))
        self.field_tgt_btn_group.clicked.connect(
            lambda: self._open_layer_group_menu('target'))

        self.field_ref_btn_point.clicked.connect(
            lambda: self._set_field_geom_filter('ref', QgsWkbTypes.GeometryType.PointGeometry))
        self.field_ref_btn_line.clicked.connect(
            lambda: self._set_field_geom_filter('ref', QgsWkbTypes.GeometryType.LineGeometry))
        self.field_ref_btn_polygon.clicked.connect(
            lambda: self._set_field_geom_filter('ref', QgsWkbTypes.GeometryType.PolygonGeometry))
        self.field_ref_btn_group.clicked.connect(
            lambda: self._open_layer_group_menu('ref'))

        self.ref_btn_point.clicked.connect(
            lambda: self._load_layers_to_list(self.ref_layer_list, QgsWkbTypes.GeometryType.PointGeometry))
        self.ref_btn_line.clicked.connect(
            lambda: self._load_layers_to_list(self.ref_layer_list, QgsWkbTypes.GeometryType.LineGeometry))
        self.ref_btn_polygon.clicked.connect(
            lambda: self._load_layers_to_list(self.ref_layer_list, QgsWkbTypes.GeometryType.PolygonGeometry))
        self.ref_btn_all.clicked.connect(
            lambda: self._load_layers_to_list(self.ref_layer_list, None))

        self.btn_confirm.clicked.connect(self._run_core)
        self.btn_refresh.clicked.connect(self._refresh_layers)
        self.btn_mode_toggle.clicked.connect(self._show_mode_menu)

        self.target_layer_list.itemSelectionChanged.connect(self._on_layer_selection_changed)
        self.ref_layer_list.itemSelectionChanged.connect(self._on_layer_selection_changed)
        self.spin_tolerance.valueChanged.connect(self._update_meter_hint)
        self.combo_ref_field.currentIndexChanged.connect(self._on_ref_field_index_changed)
        self.combo_ref_field.activated.connect(self._on_ref_field_activated)
        self.combo_spatial_mode.currentIndexChanged.connect(self._sync_end_field_rows)
        self.combo_field_scheme.currentIndexChanged.connect(self._on_field_scheme_changed)
        self.btn_field_scheme_add.clicked.connect(self._add_field_task)
        self.btn_field_scheme_view.clicked.connect(self._view_field_scheme)
        self.btn_field_scheme_manage.clicked.connect(self._field_scheme_manage_menu)
        self.btn_field_scheme_import.clicked.connect(self._import_schemes_shared)
        self.btn_field_scheme_export.clicked.connect(self._export_schemes_shared)
        self.combo_move_scheme.currentIndexChanged.connect(self._on_move_scheme_changed)
        self.btn_move_scheme_add.clicked.connect(self._add_move_task)
        self.btn_move_scheme_view.clicked.connect(self._view_move_scheme)
        self.btn_move_scheme_manage.clicked.connect(self._move_scheme_manage_menu)
        self.btn_move_scheme_import.clicked.connect(self._import_schemes_shared)
        self.btn_move_scheme_export.clicked.connect(self._export_schemes_shared)
        self.chk_move_batch_continue.toggled.connect(
            lambda c: setattr(self, '_move_batch_continue', bool(c))
        )
        self.combo_move_mode.currentIndexChanged.connect(self._sync_move_mode_tip)
        self.target_layer_list.viewport().installEventFilter(self)
        self.ref_layer_list.viewport().installEventFilter(self)
        self.combo_snap_scheme.currentIndexChanged.connect(self._on_snap_scheme_changed)
        self.project.layersAdded.connect(self._on_project_layers_changed)
        self.project.layersRemoved.connect(self._on_project_layers_changed)
        self.btn_scheme_manage.clicked.connect(self._show_scheme_manage_menu)
        self.btn_scheme_import.clicked.connect(self._import_schemes_shared)
        self.btn_scheme_export.clicked.connect(self._export_schemes_shared)
        self.btn_memory_style.clicked.connect(self._open_memory_style_dialog)
        self.btn_scheme_add.clicked.connect(self._add_current_to_schemes)
        self.btn_scheme_view.clicked.connect(self._view_current_scheme)
        self.combo_snap_ref_mode.currentIndexChanged.connect(self._on_snap_ref_mode_combo_changed)
        self.btn_line_length_rule.clicked.connect(self._open_snap_metric_rule_dialog)
        self.combo_count_attach.currentIndexChanged.connect(self._on_count_attach_changed)
        self.chk_count_output_mates.toggled.connect(self._on_count_mates_toggled)
        self.btn_polygon_out_all.clicked.connect(lambda: self._set_all_polygon_outputs(True))
        self.btn_polygon_out_none.clicked.connect(lambda: self._set_all_polygon_outputs(False))
        for combo in (self.combo_spatial_mode, self.combo_snap_spatial_mode, self.combo_snap_ref_mode):
            combo.currentIndexChanged.connect(self._sync_combo_tips)
        self.combo_multi_match.currentIndexChanged.connect(self._on_multi_match_changed)

    def _sync_combo_tips(self, *_args):
        """下拉框自身的浮动提示＝用途说明 + 当前选中项的完整说明（列表里逐项悬停同样可见）。"""
        pairs = (
            (self.combo_spatial_mode, self.tr('空间命名模式：被命名要素与参考要素满足什么位置关系，才算「命中」并写入。')),
            (self.combo_snap_spatial_mode, self.tr('空间命名模式：判断图层要素与参考要素满足什么位置关系，才算「已吸附（命中）」。')),
            (self.combo_snap_ref_mode, self.tr('检测方式：第一项为标准；其后为现行特殊检测。下拉框不能用鼠标滚轮改值。')),
        )
        for combo, base in pairs:
            idx = combo.currentIndex()
            if idx < 0:
                combo.setToolTip(base)
                continue
            tip = combo.itemData(idx, Qt.ItemDataRole.ToolTipRole) or ''
            combo.setToolTip('{0}\n\n{1}{2}\n{3}'.format(base, self.tr('当前：'), combo.currentText(), tip).rstrip())
        self._sync_mode_param_widgets()

    def _sync_mode_param_widgets(self):
        if not hasattr(self, 'row_field_mode_param'):
            return
        fcode = self.combo_spatial_mode.currentData()
        self.row_field_mode_param.set_mode(fcode, self._mode_params.get(fcode))
        scode = self.combo_snap_spatial_mode.currentData() if self.combo_snap_spatial_mode.isEnabled() else None
        self.row_snap_mode_param.set_mode(scode, self._mode_params.get(scode))

    def _on_mode_param_changed(self, code, value):
        self._mode_params[code] = value
        self._persist_settings()

    def _current_mode_param(self, code):
        """当前界面上该模式的阈值；无阈值的模式返回 None。"""
        if mode_param_spec(code) is None:
            return None
        return mode_param_value(code, self._mode_params.get(code))

    def _multi_match_tip_text(self):
        tip = multi_match_tip(self.combo_multi_match.currentData())
        if not tip:
            return self.tr(MULTI_MATCH_COMMON_TIP)
        return '{0}\n\n{1}{2}\n{3}'.format(
            self.tr(MULTI_MATCH_COMMON_TIP), self.tr('当前：'), self.combo_multi_match.currentText(), tip
        )

    def _end_fields_multi_tip_text(self):
        return '{0}\n\n{1}'.format(
            self.tr('头、尾各自按这里的多匹配处理。某一端没有点时，另一端照常写入。'),
            self._multi_match_tip_text(),
        )

    def _on_multi_match_changed(self, _idx):
        if not self.combo_multi_match.isEnabled():
            return
        if self.combo_spatial_mode.currentData() == LP_END_FIELDS:
            self.combo_multi_match.setToolTip(self._end_fields_multi_tip_text())
        else:
            self.combo_multi_match.setToolTip(self._multi_match_tip_text())

    def _init_polygon_output_checklist(self):
        self.list_polygon_outputs.clear()
        items = (
            (POLYGON_SUB_OVERLAP_HIT, self.tr('重叠：输出参与重叠的面要素')),
            (POLYGON_OUT_OVERLAP_FRAGMENTS, self.tr('重叠：相交面片（可多片独立多边形）')),
            (POLYGON_OUT_OVERLAP_FRAG_CENTER, self.tr('重叠：相交面片的质心点')),
            (POLYGON_SUB_HOLES_LAYER, self.tr('内部孔洞：生成孔洞面图层')),
            (POLYGON_OUT_HOLES_CENTER, self.tr('内部孔洞：中心点图层')),
            (
                POLYGON_SUB_GAPS_INTERNAL,
                self.tr('面间隙（斑块之间，需补缺）——面图层'),
            ),
            (
                POLYGON_SUB_GAPS_EDGE,
                self.tr('外缘留白（与制图边界接壤，多为正常）——面图层'),
            ),
            (POLYGON_OUT_GAPS_INTERNAL_CENTER, self.tr('斑块间空隙：中心点图层')),
            (POLYGON_OUT_GAPS_EDGE_CENTER, self.tr('外缘留白：中心点图层')),
            (POLYGON_OUT_CENTROID_HIT, self.tr('中心坐标：重叠相关面的质心点（图层附 CentroidX/Y）')),
            (POLYGON_OUT_CENTROID_ALL, self.tr('中心坐标：全部面的质心（点图层）')),
        )
        default_on = frozenset({
            POLYGON_SUB_OVERLAP_HIT,
            POLYGON_SUB_HOLES_LAYER,
            POLYGON_OUT_HOLES_CENTER,
            POLYGON_SUB_GAPS_INTERNAL,
            POLYGON_OUT_GAPS_INTERNAL_CENTER,
            POLYGON_OUT_OVERLAP_FRAG_CENTER,
        })
        tips = {
            POLYGON_SUB_OVERLAP_HIT: self.tr('输出原始面要素（带全部属性）。受「提取已吸附」控制：勾选输出有重叠的面，不勾选输出没有重叠的面。'),
            POLYGON_OUT_OVERLAP_FRAGMENTS: self.tr('只输出两两重叠的那一块区域；附两个来源面的图层名、FID 和重叠面积（㎡）。'),
            POLYGON_OUT_OVERLAP_FRAG_CENTER: self.tr('每块重叠区域输出一个质心点，方便逐个定位修改。'),
            POLYGON_SUB_HOLES_LAYER: self.tr('单个面内部的「洞」（内环），面积 ≥ 阈值的才输出。'),
            POLYGON_OUT_HOLES_CENTER: self.tr('每个孔洞输出一个中心点。'),
            POLYGON_SUB_GAPS_INTERNAL: self.tr('被面包围、不与外边界相接的空隙，通常是漏画或没接好的缝，需要补。'),
            POLYGON_SUB_GAPS_EDGE: self.tr('与所有面外轮廓相连的空白，多为制图范围边缘，一般不需要处理。'),
            POLYGON_OUT_GAPS_INTERNAL_CENTER: self.tr('每片斑块间空隙输出一个中心点。'),
            POLYGON_OUT_GAPS_EDGE_CENTER: self.tr('每片外缘留白输出一个中心点。'),
            POLYGON_OUT_CENTROID_HIT: self.tr('与「参与重叠的面要素」同一批面，输出其质心点，并附 CentroidX / CentroidY 坐标字段。'),
            POLYGON_OUT_CENTROID_ALL: self.tr('所有面都输出质心点，不管有没有重叠。'),
        }
        for code, label in items:
            it = QListWidgetItem(label)
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            it.setData(Qt.ItemDataRole.UserRole, code)
            it.setToolTip(tips.get(code, ''))
            it.setCheckState(Qt.CheckState.Checked if code in default_on else Qt.CheckState.Unchecked)
            self.list_polygon_outputs.addItem(it)

    def _polygon_outputs_selected(self):
        codes = []
        for row in range(self.list_polygon_outputs.count()):
            it = self.list_polygon_outputs.item(row)
            if it.checkState() == Qt.CheckState.Checked:
                c = it.data(Qt.ItemDataRole.UserRole)
                if c:
                    codes.append(c)
        return codes

    def _set_all_polygon_outputs(self, checked):
        st = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for row in range(self.list_polygon_outputs.count()):
            self.list_polygon_outputs.item(row).setCheckState(st)

    def _set_polygon_checks_from_codes(self, codes):
        want = frozenset(expand_polygon_output_codes_for_tasks(codes))
        for row in range(self.list_polygon_outputs.count()):
            it = self.list_polygon_outputs.item(row)
            code = it.data(Qt.ItemDataRole.UserRole)
            if code:
                it.setCheckState(Qt.CheckState.Checked if code in want else Qt.CheckState.Unchecked)

    def _selected_geom_uniform(self, list_widget):
        layers = self._get_selected_layers(list_widget)
        if not layers:
            return None
        ks = {_layer_geom_class(lyr) for lyr in layers}
        ks.discard(None)
        if len(ks) != 1:
            return None
        return ks.pop()

    def _snap_target_geom_uniform(self):
        return self._selected_geom_uniform(self.target_layer_list)

    def _overlap_kind_auto(self):
        g = self._snap_target_geom_uniform()
        mp = {
            QgsWkbTypes.GeometryType.PointGeometry: 'point',
            QgsWkbTypes.GeometryType.LineGeometry: 'line',
            QgsWkbTypes.GeometryType.PolygonGeometry: 'polygon',
        }
        return mp.get(g)

    def _effective_snap_ref_mode(self):
        """检测方式下拉：空或非特殊 key 视为「标准」，否则为该特殊检测 key。"""
        if not hasattr(self, 'combo_snap_ref_mode') or self.combo_snap_ref_mode.count() == 0:
            return 'standard'
        cd = self.combo_snap_ref_mode.currentData()
        if not cd or cd == 'standard' or cd not in SPECIAL_KEYS:
            return 'standard'
        return cd

    def _snap_ref_layer_geom_filter(self):
        """特殊检测子类型限定参考图层几何类型时返回 QgsWkbTypes，否则 None（列表等价于「全部」）。"""
        mode = self._effective_snap_ref_mode()
        if mode == 'standard':
            return None
        return self._special_ref_wkb(mode)

    @staticmethod
    def _special_ref_wkb(sp_key):
        return {
            'point': QgsWkbTypes.GeometryType.PointGeometry,
            'line': QgsWkbTypes.GeometryType.LineGeometry,
            'polygon': QgsWkbTypes.GeometryType.PolygonGeometry,
        }.get(SPECIAL_REF_GEOM.get(sp_key))

    def _special_entries_for_geom(self, geo):
        """按判断图层列出特殊检测，顺序与 SPECIAL_MODE_INFO 一致。

        判断侧类型统一时只列该类型；混选或未选时只列三种几何都支持的。
        参考图层不参与这份列表：需要参考几何的检查仍然出现，选中之后再去限定参考列表。
        """
        names = {
            QgsWkbTypes.GeometryType.PointGeometry: 'point',
            QgsWkbTypes.GeometryType.LineGeometry: 'line',
            QgsWkbTypes.GeometryType.PolygonGeometry: 'polygon',
        }
        if geo in names:
            keys = special_modes_for_geom(names[geo])
        else:
            keys = [
                k for k in special_modes_for_geom('point')
                if len(SPECIAL_TARGET_GEOMS.get(k, ())) == 3
            ]
        return [(k, special_mode_label(k), special_mode_tip(k)) for k in keys]

    def _refresh_snap_ref_layer_list(self):
        """按当前检测方式筛选参考图层列表；切换回其它方式时恢复「全部」并启用手动筛选按钮。"""
        if getattr(self, '_ui_mode', None) != 'snap':
            return
        filt = self._snap_ref_layer_geom_filter()
        lw = self.ref_layer_list
        prev_sel = [self._item_layer_name(i) for i in lw.selectedItems()]
        self._load_layers_to_list(lw, filt)
        locked = filt is not None
        tip_locked = self.tr('当前检测方式已限定参考图层类型；切换到其它检测方式后恢复筛选按钮。')
        ref_btns = (self.ref_btn_point, self.ref_btn_line, self.ref_btn_polygon, self.ref_btn_all)
        for b in ref_btns:
            b.setEnabled(not locked)
        self._restore_filter_button_tips(ref_btns, extra=tip_locked if locked else None)
        self._sync_snap_filter_checked('ref', filt)
        for row in range(lw.count()):
            it = lw.item(row)
            if self._item_layer_name(it) in prev_sel:
                it.setSelected(True)
        self._snap_ref_geom_filter_cache = filt

    def _maybe_refresh_snap_ref_layer_list_if_filter_changed(self):
        """仅当「参考图层几何筛选条件」变化时重载列表，避免每次切换判断/参考选中都整表刷新。"""
        if getattr(self, '_ui_mode', None) != 'snap':
            return
        nf = self._snap_ref_layer_geom_filter()
        if nf == getattr(self, '_snap_ref_geom_filter_cache', CDETDialog._SNAP_REF_FILT_CACHE_UNSET):
            return
        self._refresh_snap_ref_layer_list()

    def _refresh_snap_ref_mode_combo(self):
        if not hasattr(self, 'combo_snap_ref_mode'):
            return
        if getattr(self, '_ui_mode', None) != 'snap':
            return
        geo = self._snap_target_geom_uniform()
        prev_norm = None
        if getattr(self, '_restore_snap_ref_mode', None):
            prev_norm = self._restore_snap_ref_mode
            self._restore_snap_ref_mode = None
        else:
            prev_norm = self.combo_snap_ref_mode.currentData()
        if not prev_norm or prev_norm == 'standard' or prev_norm not in SPECIAL_KEYS:
            prev_norm = 'standard'
        self.combo_snap_ref_mode.blockSignals(True)
        self.combo_snap_ref_mode.clear()
        self.combo_snap_ref_mode.addItem(self.tr('标准'), 'standard')
        add_mode_items(self.combo_snap_ref_mode, self._special_entries_for_geom(geo))
        if prev_norm == 'standard':
            self.combo_snap_ref_mode.setCurrentIndex(0)
        else:
            ix = self.combo_snap_ref_mode.findData(prev_norm)
            if ix >= 0:
                self.combo_snap_ref_mode.setCurrentIndex(ix)
            else:
                # Current special no longer applies: fall back to 标准, never pick another special.
                self.combo_snap_ref_mode.setCurrentIndex(0)
        self.combo_snap_ref_mode.blockSignals(False)
        self._refresh_snap_special_extra_visibility()
        self._refresh_snap_spatial_combo()
        self._maybe_refresh_snap_ref_layer_list_if_filter_changed()
        self._sync_combo_tips()

    def _retranslate_snap_ref_mode_combo(self):
        """Update item labels only. Do not rebuild or reload the layer lists."""
        combo = getattr(self, 'combo_snap_ref_mode', None)
        if combo is None:
            return
        combo.blockSignals(True)
        try:
            for i in range(combo.count()):
                data = combo.itemData(i)
                if not data or data == 'standard' or data not in SPECIAL_KEYS:
                    combo.setItemText(i, self.tr('标准'))
                else:
                    combo.setItemText(i, special_mode_label(data))
        finally:
            combo.blockSignals(False)
        self._sync_combo_tips()

    def _sync_ref_list_participation(self, use_ref):
        """参考图层只在标准模式、以及需要参考几何的特殊检测里参与。

        不需要参考图层时清掉已有选择，并禁用列表和点/线/面/全部按钮。
        回到需要参考的模式时重新启用，不把刚才清掉的选择补回来。
        """
        lw = self.ref_layer_list
        if not use_ref and (lw.selectedItems() or lw.currentItem() is not None):
            lw.blockSignals(True)
            lw.clearSelection()
            lw.setCurrentRow(-1)
            lw.blockSignals(False)
        lw.setEnabled(bool(use_ref))
        self.ref_filter_stack.setEnabled(bool(use_ref))
        self._paint_ref_list_enabled(bool(use_ref))

    def _paint_ref_list_enabled(self, enabled):
        """只有参考图层整列禁用时，这一列的列表底色才是灰；平时保持纯白。"""
        color = "#ffffff" if enabled else "#eff0f0"
        self.ref_layer_list.viewport().setStyleSheet("background-color: %s;" % color)

    def _refresh_snap_special_extra_visibility(self):
        mode = self._effective_snap_ref_mode()
        use_ref = mode == 'standard' or mode in SPECIAL_REF_GEOM
        self._rebuild_special_form(mode)
        self._sync_ref_list_participation(use_ref)
        poly_area_row = mode == 'polygon_inspect'
        self.w_poly_extra.setVisible(poly_area_row)
        show_metric = mode in (
            'line_length',
            'point_line_count',
            'line_point_count',
            'poly_point_count',
            'poly_line_count',
        )
        self.w_line_extra.setVisible(show_metric)
        if hasattr(self, 'lbl_line_extra_title'):
            if mode == 'line_length':
                self.lbl_line_extra_title.setText(self.tr('线长规则'))
            elif show_metric:
                self.lbl_line_extra_title.setText(self.tr('个数规则'))
        if hasattr(self, 'w_count_attach_extra'):
            self.w_count_attach_extra.setVisible(mode in ('point_line_count', 'line_point_count'))
        self.w_overlap_hint.setVisible(mode == 'overlap_grp')
        self.combo_overlap_scope.setVisible(mode == 'overlap_grp')
        self.w_chain_extra.setVisible(mode == 'point_line_chain')
        if hasattr(self, 'w_line_overlap_extra'):
            self.w_line_overlap_extra.setVisible(mode == 'line_overlap_pt')

        if mode == 'polygon_inspect':
            self.snap_right_stack.setCurrentIndex(1)
            self._set_title_text(self.lbl_polygon_stack_title, '面检测输出')
            self.lbl_polygon_stack_title.setVisible(True)
        else:
            self.snap_right_stack.setCurrentIndex(0)
            self.lbl_polygon_stack_title.setVisible(False)

        if mode == 'overlap_grp':
            self.chk_snap.setEnabled(False)
            self.chk_snap.setToolTip(
                self.tr(
                    '「重复要素」检测固定输出重复的要素（线/面按顶点在容差内逐个对得上），'
                    '不使用「提取已吸附」。切换到「标准」或其它特殊检测后可勾选此项。',
                ))
        else:
            self.chk_snap.setEnabled(True)
            if mode == 'polygon_inspect':
                self.chk_snap.setToolTip(
                    self.tr(
                        '勾选：重叠「面」图层中仅输出确实存在重叠的面；不勾选：输出无重叠的面。'
                        '孔洞/空隙图层不受此项影响。「中心坐标」中与重叠相关的点图层同步受此规则。',
                    ))
            elif mode == 'line_length':
                self.chk_snap.setToolTip(
                    self.tr(
                        '勾选：输出「长度满足规则」的线（米，见右侧「编辑…」）；'
                        '不勾选：输出不满足规则的线。',
                    ))
            elif mode == 'line_ends':
                self.chk_snap.setEnabled(False)
                self.chk_snap.setToolTip(
                    self.tr('「标出起点和终点」固定为每条线输出头尾两个点，不使用「提取已吸附」。')
                )
            elif mode == 'line_overlap_pt':
                self.chk_snap.setEnabled(False)
                self.chk_snap.setToolTip(
                    self.tr('「两线重叠段」固定输出重叠段中心点，不使用「提取已吸附」。')
                )
            elif mode in ('point_line_count', 'line_point_count', 'poly_point_count', 'poly_line_count'):
                self.chk_snap.setToolTip(
                    self.tr(
                        '勾选：输出「个数满足规则」的要素；不勾选：输出个数不满足规则的要素。',
                    ))
            elif mode == 'point_line_chain':
                self.chk_snap.setToolTip(
                    self.tr(
                        '勾选（提取已吸附）：输出任一连通方向上「段数≥阈值」的点及对应线段；'
                        '不勾选：输出最大段数小于阈值的点及该点处接线。',
                    ))
            elif mode in SPECIAL_KEYS_NO_SNAP_FILTER:
                self.chk_snap.setEnabled(False)
                self.chk_snap.setToolTip(
                    self.tr('「{0}」固定输出问题位置点，不使用「提取已吸附」。').format(special_mode_label(mode))
                )
            elif mode == 'geom_validity':
                self.chk_snap.setToolTip(
                    self.tr('勾选：输出有问题的要素（附 CDET_问题 字段）；不勾选：输出没问题的要素。')
                )
            elif mode == 'poly_area':
                self.chk_snap.setToolTip(
                    self.tr('勾选：输出「面积满足规则」的面；不勾选：输出不满足规则的面。')
                )
            elif mode == 'point_near':
                self.chk_snap.setToolTip(
                    self.tr('勾选：输出附近有别的点（过近）的点；不勾选：输出周围没有近邻的点。')
                )
            else:
                self.chk_snap.setToolTip(self._snap_chk_tip_standard)
        self._update_snap_metric_summary()

    def _rebuild_special_form(self, mode):
        """2.1 新增特殊检测的参数表单：按当前检测重建，数值改动写回 self._special_values。"""
        if not hasattr(self, 'w_quality_extra') or mode == self._special_form_key:
            return
        self._special_form_key = mode
        while self._quality_extra_lay.count():
            it = self._quality_extra_lay.takeAt(0)
            if it.widget() is not None:
                it.widget().deleteLater()
        w, _getter = build_special_param_form(
            mode, self._special_values, self.w_quality_extra, self._on_special_values_changed
        )
        if w is not None:
            self._quality_extra_lay.addWidget(w)
        self.w_quality_extra.setVisible(w is not None)

    def _on_special_values_changed(self, vals):
        self._special_values.update(vals)
        self._persist_settings()

    def _on_snap_ref_mode_combo_changed(self, _idx):
        self._refresh_snap_special_extra_visibility()
        self._refresh_snap_spatial_combo()
        self._maybe_refresh_snap_ref_layer_list_if_filter_changed()

    def _update_line_rule_label(self):
        self._update_snap_metric_summary()

    def _update_snap_metric_summary(self):
        mode = self._effective_snap_ref_mode()
        if mode == 'line_length':
            r = dict(self._line_length_rule or {'kind': 'le', 'threshold': 0})
            k = r.get('kind', 'le')
            if k == 'ge':
                txt = self.tr('长度 ≥ {0} m').format(r.get('threshold', 0))
            elif k == 'between':
                txt = self.tr('长度 ∈ [{0}, {1}] m').format(r.get('t_min', 0), r.get('t_max', 0))
            else:
                txt = self.tr('长度 ≤ {0} m').format(r.get('threshold', 0))
            self.lbl_line_rule_summary.setText(txt)
        elif mode in ('point_line_count', 'line_point_count', 'poly_point_count', 'poly_line_count'):
            self.lbl_line_rule_summary.setText(format_snap_count_rule_summary(self._snap_count_rule))
        else:
            self.lbl_line_rule_summary.setText('')

    def _open_snap_metric_rule_dialog(self):
        mode = self._effective_snap_ref_mode()
        if mode == 'line_length':
            dlg = CdetLineLengthRuleDialog(self, self._line_length_rule)
            if run_dialog(dlg) == QDialog.DialogCode.Accepted:
                rr = dlg.result_rule()
                if rr:
                    self._line_length_rule = rr
                    self._update_snap_metric_summary()
                    self._persist_settings()
        elif mode in ('point_line_count', 'line_point_count', 'poly_point_count', 'poly_line_count'):
            dlg = CdetSnapCountRuleDialog(self, self._snap_count_rule)
            if run_dialog(dlg) == QDialog.DialogCode.Accepted:
                rr = dlg.result_rule()
                if rr:
                    self._snap_count_rule = rr
                    self._update_snap_metric_summary()
                    self._persist_settings()

    def _on_count_attach_changed(self, _idx):
        self._count_attach = normalize_count_attach(self.combo_count_attach.currentData())
        self._persist_settings()

    def _on_count_mates_toggled(self, checked):
        self._count_output_mates = bool(checked)
        self._persist_settings()

    def _sync_count_attach_widgets(self):
        if not hasattr(self, 'combo_count_attach'):
            return
        self.combo_count_attach.blockSignals(True)
        ix = self.combo_count_attach.findData(normalize_count_attach(self._count_attach))
        self.combo_count_attach.setCurrentIndex(ix if ix >= 0 else 0)
        self.combo_count_attach.blockSignals(False)
        if hasattr(self, 'chk_count_output_mates'):
            self.chk_count_output_mates.blockSignals(True)
            self.chk_count_output_mates.setChecked(bool(self._count_output_mates))
            self.chk_count_output_mates.blockSignals(False)

    def _compose_snap_run_params(self):
        atol = float(self.spin_overlap_area_tol.value())
        ref_mode = self._effective_snap_ref_mode()
        # 标准模式必须来自下拉项，禁止用 __special__ 回退（否则 _mode_ok 对未知模式恒为 False）
        ssm = self.combo_snap_spatial_mode.currentData()
        if ref_mode == 'standard':
            smode = ssm
            extra = {}
            mp = self._current_mode_param(ssm)
            if mp is not None:
                extra['mode_param'] = mp
        else:
            smode = '__special__'
            extra = {
                '_polygon_outputs': list(self._polygon_outputs_selected()),
                '_polygon_area_tol_m2': atol,
                '_polygon_overlap_area_tol_m2': atol,
                '_line_length_rule': dict(self._line_length_rule),
                '_snap_count_rule': dict(self._snap_count_rule),
                '_count_attach': normalize_count_attach(self._count_attach),
                '_count_output_mates': bool(self._count_output_mates),
                '_overlap_kind': self._overlap_kind_auto() or 'auto',
                '_overlap_scope': normalize_overlap_scope(self.combo_overlap_scope.currentData()),
                '_line_overlap_min_length': float(self.spin_line_overlap_min.value()),
                '_point_line_chain_min_seg': int(self.spin_chain_min_seg.value()),
                '_snap_special': ref_mode,
            }
            extra.update(normalize_special_values(self._special_values))
        out = {
            'snap_enabled': self.chk_snap.isChecked(),
            'tolerance': self.spin_tolerance.value(),
            'spatial_mode': smode,
        }
        out.update(extra)
        t_layers = self._get_selected_layers(self.target_layer_list)
        r_layers = self._get_selected_layers(self.ref_layer_list)
        out['_category_target'] = self._filters_for_list(self.target_layer_list, t_layers)
        out['_category_ref'] = self._filters_for_list(self.ref_layer_list, r_layers)
        return out


    _LANGUAGES = (
        ("en", "English"),
        ("zh", "中文"),
        ("es", "Español"),
        ("fr", "Français"),
        ("ar", "العربية"),
        ("it", "Italiano"),
        ("de", "Deutsch"),
        ("ja", "日本語"),
        ("ko", "한국어"),
    )

    def _show_language_menu(self):
        menu = QMenu(self)
        current = current_language()
        for key, label in self._LANGUAGES:
            action = menu.addAction(language_icon(key), label)
            action.setCheckable(True)
            action.setChecked(key == current)
            action.triggered.connect(lambda _checked=False, lang=key: set_language(lang))
        anchor = self.btn_language
        run_menu(menu, anchor.mapToGlobal(anchor.rect().bottomLeft()))

    def _on_language_changed(self, *_args):
        # Never set RightToLeft / layout direction, including for Arabic.
        retranslate_tree(self)
        if hasattr(self, "btn_language"):
            self.btn_language.setText("")
            self.btn_language.setIcon(language_icon())
            self.btn_language.setToolTip(_i18n_tr("语言"))
        if hasattr(self, "btn_help"):
            self.btn_help.setText("")
            self.btn_help.setToolTip(_i18n_tr("帮助"))
        for btn in (
            getattr(self, "btn_scheme_import", None),
            getattr(self, "btn_field_scheme_import", None),
            getattr(self, "btn_move_scheme_import", None),
        ):
            if btn is not None:
                btn.setText("")
                btn.setToolTip(_i18n_tr("导入"))
        for btn in (
            getattr(self, "btn_scheme_export", None),
            getattr(self, "btn_field_scheme_export", None),
            getattr(self, "btn_move_scheme_export", None),
        ):
            if btn is not None:
                btn.setText("")
                btn.setToolTip(_i18n_tr("导出"))
        self._sync_mode_toggle_text()
        try:
            self._init_multi_combo()
        except Exception:  # nosec B110
            pass
        try:
            self._update_line_rule_label()
        except Exception:  # nosec B110
            pass
        try:
            self._update_tolerance_display()
        except Exception:  # nosec B110
            pass
        try:
            self._refill_translated_combos()
        except Exception:  # nosec B110
            pass
        try:
            self._restore_filter_button_tips()
        except Exception:  # nosec B110
            pass
        try:
            # After name-tip restore, re-apply selected group feature-count (current language).
            self._sync_field_filter_checked()
        except Exception:  # nosec B110
            pass
        try:
            self._update_scheme_layer_match_label()
        except Exception:  # nosec B110
            pass
        try:
            self._retranslate_snap_ref_mode_combo()
        except Exception:  # nosec B110
            pass
        try:
            self._sync_open_category_dialog()
        except Exception:  # nosec B110
            pass
        try:
            self._settle_main_layout()
        except Exception:  # nosec B110
            pass

    def _refresh_layers(self):
        # Refresh is an explicit clear: blank clicks must not do this.
        for lw in (self.target_layer_list, self.ref_layer_list):
            lw.blockSignals(True)
            lw.clearSelection()
            lw.blockSignals(False)
        if self._ui_mode == 'field':
            self._reload_field_side_list('target', refresh=False)
            self._reload_field_side_list('ref')
        else:
            self.load_all_layers()
            self._refresh_snap_ref_mode_combo()
        self._update_scheme_layer_match_label()
        self._restore_filter_button_tips()
        # Recount after restore so a selected field group keeps '组内矢量要素共 N 个' with the refreshed total.
        self._sync_field_filter_checked()
        try:
            self._sync_open_category_dialog()
        except Exception:  # nosec B110
            pass
        self.iface.messageBar().pushSuccess(
            DISPLAY_NAME,
            self.tr('图层列表已刷新'),
        )

    def _update_tolerance_display(self):
        layers = self._get_selected_layers(self.target_layer_list)
        if layers:
            crs = layers[0].crs()
            self.is_geographic = crs.isGeographic()

            if self.is_geographic:
                self.lbl_unit.setText(self.tr('度'))
                current = self.spin_tolerance.value()
                if current >= 1.0:
                    self.spin_tolerance.setValue(0.00001)
                self.spin_tolerance.setSingleStep(0.000001)
                self.spin_tolerance.setDecimals(6)
                self.lbl_meter_hint.setVisible(True)
            else:
                self.lbl_unit.setText(self.tr('米'))
                current = self.spin_tolerance.value()
                if current < 0.001:
                    self.spin_tolerance.setValue(1.0)
                self.spin_tolerance.setSingleStep(0.1)
                self.spin_tolerance.setDecimals(2)
                self.lbl_meter_hint.setVisible(False)

            self._update_meter_hint()
        self._apply_tolerance_spin_compact_width()

    def _apply_tolerance_spin_compact_width(self):
        if not hasattr(self, 'spin_tolerance'):
            return
        spin = self.spin_tolerance
        spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        try:
            spin.setFixedWidth(16777215)
        except Exception:  # nosec B110
            pass
        # Width fits 6 decimal places (e.g. 0.000000) plus frame padding; no step buttons.
        sample = '0.000000'
        try:
            fm = QFontMetrics(spin.font())
            tw = fm.horizontalAdvance(sample) if hasattr(fm, 'horizontalAdvance') else fm.boundingRect(sample).width()
            width = int(tw + 24)
        except Exception:
            width = 88
        spin.setFixedWidth(max(width, 72))
        spin.setMinimumWidth(max(width, 72))
        spin.setMaximumWidth(max(width, 72))
        spin.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        if hasattr(self, 'lbl_unit'):
            self.lbl_unit.setWordWrap(False)
            self.lbl_unit.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        if hasattr(self, 'lbl_meter_hint'):
            self.lbl_meter_hint.setWordWrap(False)
            self.lbl_meter_hint.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

    def _update_meter_hint(self):
        if self.is_geographic:
            degrees = self.spin_tolerance.value()
            meters = degrees * self.METERS_PER_DEGREE
            if meters >= 1000:
                self.lbl_meter_hint.setText(f'(≈{meters/1000:.2f}km)')
            elif meters >= 1:
                self.lbl_meter_hint.setText(f'(≈{meters:.2f}m)')
            else:
                self.lbl_meter_hint.setText(f'(≈{meters*100:.2f}cm)')

    def _format_edit_task_tolerance_caption(self, tol_value, crs):
        """编辑子任务：左侧「容差」标题附带地理坐标系下的约略米制换算，或投影坐标系的地图单位说明。"""
        base = self.tr('容差')
        if crs is None or not crs.isValid():
            return base
        try:
            tv = float(tol_value)
        except (TypeError, ValueError):
            return base
        if crs.isGeographic():
            meters = tv * self.METERS_PER_DEGREE
            if meters >= 1000:
                return self.tr('容差  (≈{0} km)').format(round(meters / 1000.0, 2))
            if meters >= 1:
                return self.tr('容差  (≈{0} m)').format(round(meters, 2))
            return self.tr('容差  (≈{0} cm)').format(round(meters * 100.0, 2))
        try:
            from qgis.core import QgsUnitTypes

            us = QgsUnitTypes.toString(crs.mapUnits())
        except Exception:
            us = ''
        if not us:
            return self.tr('容差  ({0})').format(tv)
        return self.tr('容差  ({0} {1})').format(tv, us)

    def _init_multi_combo(self):
        self.combo_multi_match.clear()
        for code, label in multi_match_choices():
            self.combo_multi_match.addItem(label, code)
            self.combo_multi_match.setItemData(
                self.combo_multi_match.count() - 1, multi_match_tip(code), Qt.ItemDataRole.ToolTipRole
            )
        self.combo_multi_match.setToolTip(self._multi_match_tip_text())

    def _on_layer_selection_changed(self):
        self._update_tolerance_display()
        if self._ui_mode == 'field':
            self._refresh_field_combos()
        elif self._ui_mode == 'snap':
            self._refresh_snap_ref_mode_combo()
        elif self._ui_mode == 'move':
            self._refresh_move_mode_combo()

    _UI_MODE_CYCLE = ('snap', 'field', 'move')

    def _mode_title(self, mode=None):
        mode = mode or getattr(self, '_ui_mode', 'snap')
        return {
            'snap': self.tr('吸附检测'),
            'field': self.tr('字段命名'),
            'move': self.tr('移动'),
        }.get(mode, self.tr('吸附检测'))

    def _next_ui_mode(self, mode=None):
        mode = mode or getattr(self, '_ui_mode', 'snap')
        cycle = self._UI_MODE_CYCLE
        try:
            i = cycle.index(mode)
        except ValueError:
            i = 0
        return cycle[(i + 1) % len(cycle)]

    def _sync_mode_toggle_text(self):
        cur = getattr(self, '_ui_mode', 'snap')
        title = self._mode_title(cur)
        short = self.tr(self._mode_short_src(cur))
        self.btn_mode_toggle.setIcon(mode_icon(cur))
        self.btn_mode_toggle.setIconSize(QSize(16, 16))
        self.btn_mode_toggle.setText(short)
        self.btn_mode_toggle.setToolTip(
            self.tr('当前：{0} — 点击展开三选（吸附检测／字段命名／移动）').format(title)
        )
        self.btn_mode_toggle.setFixedHeight(BOTTOM_BTN_H)
        self.setWindowTitle('%s - %s' % (self.tr('空间匹配与拓扑调整'), title))


    def _show_mode_menu(self):
        # True three-way pick: open all modes at once, then close. Not a cycle.
        menu = QMenu(self)
        cur = getattr(self, '_ui_mode', 'snap')
        for mode in self._UI_MODE_CYCLE:
            act = menu.addAction(mode_icon(mode), self._mode_title(mode))
            act.setCheckable(True)
            act.setChecked(mode == cur)
            act.triggered.connect(lambda _checked=False, m=mode: self._select_ui_mode(m))
        pos = self.btn_mode_toggle.mapToGlobal(self.btn_mode_toggle.rect().topLeft())
        menu.adjustSize()
        pos.setY(pos.y() - menu.sizeHint().height())
        run_menu(menu, pos)


    def _select_ui_mode(self, mode):
        if mode not in self._UI_MODE_CYCLE:
            return
        if mode == getattr(self, '_ui_mode', None):
            return
        self._apply_ui_mode(mode)
        self._persist_settings()

    def _stash_mode_tolerance(self):
        """模式参数独立：吸附／字段共用原容差键；移动单独存。"""
        if not hasattr(self, 'spin_tolerance'):
            return
        val = float(self.spin_tolerance.value())
        if getattr(self, '_ui_mode', None) == 'move':
            self._move_tol = val
        else:
            self._shared_sf_tol = val

    def _restore_mode_tolerance(self, mode):
        if not hasattr(self, 'spin_tolerance'):
            return
        if mode == 'move':
            if self._move_tol is None:
                self._move_tol = float(settings_value(self.settings, 'move_tolerance', 0.00001, type=float))
            self.spin_tolerance.setValue(float(self._move_tol))
        else:
            if self._shared_sf_tol is None:
                self._shared_sf_tol = float(settings_value(self.settings, 'tolerance', 0.00001, type=float))
            self.spin_tolerance.setValue(float(self._shared_sf_tol))

    @staticmethod
    def _layout_take_widget(layout, w):
        if layout is None or w is None:
            return False
        for i in range(layout.count()):
            it = layout.itemAt(i)
            if it is not None and it.widget() is w:
                layout.takeAt(i)
                return True
        return False

    @staticmethod
    def _layout_contains_widget(layout, w):
        if layout is None or w is None:
            return False
        for i in range(layout.count()):
            it = layout.itemAt(i)
            if it is not None and it.widget() is w:
                return True
        return False

    def _sync_tol_row_placement(self):
        """Place tolerance / output as sibling mid groups in the active layout."""
        self._place_tol_clusters()
        if getattr(self, 'lay_snap_left', None) is None:
            return
        mode = getattr(self, '_ui_mode', None)
        if hasattr(self, 'chk_move_batch_continue'):
            self.chk_move_batch_continue.setVisible(mode == 'move')
        if hasattr(self, 'w_snap_options_block'):
            self.w_snap_options_block.setVisible(mode == 'snap')
        self._rebuild_mid_param_layout()
        self._apply_tolerance_spin_compact_width()

    def _apply_ui_mode(self, mode):
        if mode not in ('snap', 'field', 'move'):
            mode = 'snap'
        if getattr(self, '_ui_mode', None) != mode and hasattr(self, 'target_layer_list'):
            self._harvest_list_categories(self.target_layer_list, 'target')
            self._harvest_list_categories(self.ref_layer_list, 'ref')
            self._stash_mode_tolerance()
        self._skip_cat_harvest = True
        self._ui_mode = mode
        snap = mode == 'snap'
        field = mode == 'field'
        move = mode == 'move'
        # 同页互斥：过滤器页 — 吸附／移动用几何筛选；字段用字段筛选
        self.target_filter_stack.setCurrentIndex(0 if (snap or move) else 1)
        self.ref_filter_stack.setCurrentIndex(0 if (snap or move) else 1)
        self.snap_options_extra.setVisible(snap)
        self.field_options_extra.setVisible(field)
        if hasattr(self, 'move_options_extra'):
            self.move_options_extra.setVisible(move)
        if hasattr(self, 'btn_scheme_import'):
            self.btn_scheme_import.setVisible(True)
            self.btn_scheme_export.setVisible(True)
        if hasattr(self, 'btn_field_scheme_import'):
            self.btn_field_scheme_import.setVisible(False)
            self.btn_field_scheme_export.setVisible(False)
        if hasattr(self, 'btn_move_scheme_import'):
            self.btn_move_scheme_import.setVisible(False)
            self.btn_move_scheme_export.setVisible(False)
        self.w_snap_options_block.setVisible(snap)
        # 吸附专属控件：移动只露容差 + move_options_extra 说明
        if hasattr(self, 'w_snap_ad_right'):
            self.w_snap_ad_right.setVisible(False)
        self.chk_snap.setVisible(snap)
        self.btn_scheme_add.setVisible(snap)
        if hasattr(self, 'btn_scheme_view'):
            self.btn_scheme_view.setVisible(snap)
        if snap:
            self._set_title_text(self.lbl_target_title, '判断图层（输出来源）')
            if hasattr(self, 'lbl_snap_ref_title'):
                self._set_title_text(self.lbl_snap_ref_title, '参考图层')
                self.lbl_snap_ref_title.setWordWrap(False)
                self.lbl_snap_ref_title.setMinimumWidth(0)
                self.lbl_snap_ref_title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            self._set_title_text(self.lbl_ref_title, '参考图层')
            self.options_group.setTitle(self.tr('吸附选项'))
            self.options_group.setProperty('boxTitle', '吸附选项')
            self.btn_confirm.setToolTip(self.tr('按当前容差与空间命名模式执行吸附筛选'))
            self.w_snap_special_extra.setVisible(True)
            self.load_all_layers()
            self._refresh_snap_ref_mode_combo()
        elif field:
            self._set_title_text(self.lbl_target_title, '被命名图层')
            self._set_title_text(self.lbl_ref_title, '参考图层')
            self.options_group.setTitle(self.tr('字段命名参数'))
            self.options_group.setProperty('boxTitle', '字段命名参数')
            self.btn_confirm.setToolTip(self.tr('按字段命名模式执行'))
            self.w_snap_special_extra.setVisible(False)
            self.snap_right_stack.setCurrentIndex(0)
            # 吸附「特殊检测」下 overlap / 面检测 / 线测量等会禁用参考列表；字段命名共用同一 ref 控件，此处必须恢复
            self.ref_layer_list.setEnabled(True)
            self.ref_filter_stack.setEnabled(True)
            self._paint_ref_list_enabled(True)
            for b in (self.ref_btn_point, self.ref_btn_line, self.ref_btn_polygon, self.ref_btn_all):
                b.setEnabled(True)
            self._restore_filter_button_tips(
                (self.ref_btn_point, self.ref_btn_line, self.ref_btn_polygon, self.ref_btn_all)
            )
            self._reload_field_side_list('target', refresh=False)
            self._reload_field_side_list('ref', refresh=False)
        else:
            # 移动模式：仿吸附左右列表，参数独立；禁新窗
            self._set_title_text(self.lbl_target_title, '被移图层')
            self._set_title_text(self.lbl_ref_title, '参考图层')
            if hasattr(self, 'lbl_move_ref_title'):
                self._set_title_text(self.lbl_move_ref_title, '参考图层')
            self.options_group.setTitle(self.tr('移动选项'))
            self.options_group.setProperty('boxTitle', '移动选项')
            self.btn_confirm.setToolTip(
                self.tr('按当前移动模式整要素平移：先预览，确认后写回原图层（不产出筛结果层）')
            )
            self.w_snap_special_extra.setVisible(False)
            self.snap_right_stack.setCurrentIndex(0)
            self.ref_layer_list.setEnabled(True)
            self.ref_filter_stack.setEnabled(True)
            self._paint_ref_list_enabled(True)
            for b in (self.ref_btn_point, self.ref_btn_line, self.ref_btn_polygon, self.ref_btn_all):
                b.setEnabled(True)
            self._restore_filter_button_tips(
                (self.ref_btn_point, self.ref_btn_line, self.ref_btn_polygon, self.ref_btn_all)
            )
            self.load_all_layers()
            self._refresh_move_mode_combo()
        if snap:
            self.right_header_stack.setCurrentIndex(0)
        elif field:
            self.right_header_stack.setCurrentIndex(1)
        else:
            self.right_header_stack.setCurrentIndex(2 if self.right_header_stack.count() > 2 else 0)
        # 检测方式下拉仅属于吸附模式；勿与字段命名／移动共用区域叠加显示
        self.combo_snap_ref_mode.setVisible(snap)
        self._restore_mode_tolerance(mode)
        self._sync_tol_row_placement()
        self._sync_mode_toggle_text()
        self._refresh_field_combos()
        self._restore_filter_button_tips()
        self._sync_field_filter_checked()
        self._update_scheme_layer_match_label()
        self._clear_mid_param_stretch()
        self._settle_main_layout()
        self._skip_cat_harvest = False


    def _geom_storage_key(self, geom):
        if geom is None:
            return 'all'
        if geom == QgsWkbTypes.GeometryType.PointGeometry:
            return 'point'
        if geom == QgsWkbTypes.GeometryType.LineGeometry:
            return 'line'
        if geom == QgsWkbTypes.GeometryType.PolygonGeometry:
            return 'polygon'
        return 'all'

    def _geom_from_storage_key(self, key):
        if key == 'point':
            return QgsWkbTypes.GeometryType.PointGeometry
        if key == 'line':
            return QgsWkbTypes.GeometryType.LineGeometry
        if key == 'polygon':
            return QgsWkbTypes.GeometryType.PolygonGeometry
        return None

    def _layers_in_tree_group(self, group):
        out = []
        for child in group.children():
            if isinstance(child, QgsLayerTreeLayer):
                lyr = child.layer()
                if isinstance(lyr, QgsVectorLayer):
                    out.append(lyr)
            elif isinstance(child, QgsLayerTreeGroup):
                out.extend(self._layers_in_tree_group(child))
        return out

    def _resolve_group_from_path(self, path_key):
        if not path_key:
            return None
        parts = path_key.split('\t')
        root = self.project.layerTreeRoot()
        parent = root
        for pname in parts:
            nxt = None
            for c in parent.children():
                if isinstance(c, QgsLayerTreeGroup) and c.name() == pname:
                    nxt = c
                    break
            if nxt is None:
                return None
            parent = nxt
        return parent if isinstance(parent, QgsLayerTreeGroup) else None

    def _vector_layers_for_field_side(self, side):
        if side == 'target':
            gpath = self._field_group_path_target
            geom_f = self._field_target_geom
        else:
            gpath = self._field_group_path_ref
            geom_f = self._field_ref_geom
        if gpath:
            grp = self._resolve_group_from_path(gpath)
            if grp is None:
                layers = []
            else:
                layers = self._layers_in_tree_group(grp)
        else:
            layers = [
                lyr for lyr in self.project.mapLayers().values()
                if isinstance(lyr, QgsVectorLayer)
            ]
        if geom_f is not None:
            layers = [lyr for lyr in layers if lyr.geometryType() == geom_f]
        return layers

    def _reload_field_side_list(self, side, refresh=True):
        if side == 'target':
            lw = self.target_layer_list
        else:
            lw = self.ref_layer_list
        self._harvest_list_categories(lw, side)
        prev_sel = [self._item_layer_name(i) for i in lw.selectedItems()]
        layers = self._vector_layers_for_field_side(side)
        lw.clear()
        for lyr in sorted(layers, key=lambda x: x.name()):
            item = self._add_project_layer_item(lw, lyr, side)
            if lyr.name() in prev_sel:
                item.setSelected(True)
        if refresh and self._ui_mode == 'field':
            self._refresh_field_combos()
        self._sync_field_filter_checked(side)

    def _set_field_geom_filter(self, side, geom):
        if side == 'target':
            if self._field_target_geom == geom:
                self._field_target_geom = None
            else:
                self._field_target_geom = geom
        else:
            if self._field_ref_geom == geom:
                self._field_ref_geom = None
            else:
                self._field_ref_geom = geom
        self._reload_field_side_list(side)

    def _iter_layer_tree_group_paths(self):
        root = self.project.layerTreeRoot()
        out = []

        def walk(group, parts):
            name = group.name()
            new_parts = parts + [name]
            key = '\t'.join(new_parts)
            out.append((' / '.join(new_parts), key))
            for ch in group.children():
                if isinstance(ch, QgsLayerTreeGroup):
                    walk(ch, new_parts)

        for ch in root.children():
            if isinstance(ch, QgsLayerTreeGroup):
                walk(ch, [])
        return out

    def _open_layer_group_menu(self, side):
        menu = QMenu(self)
        act_all = menu.addAction(self.tr('整个工程'))
        act_all.setData('')
        for disp, key in self._iter_layer_tree_group_paths():
            a = menu.addAction(disp)
            a.setData(key)
        btn = self.field_tgt_btn_group if side == 'target' else self.field_ref_btn_group
        pos = btn.mapToGlobal(btn.rect().bottomLeft())
        chosen = run_menu(menu, pos)
        if chosen is None:
            return
        data = chosen.data()
        if data is None:
            data = ''
        if side == 'target':
            self._field_group_path_target = data
        else:
            self._field_group_path_ref = data
        self._reload_field_side_list(side)

    def _refresh_field_combos(self):
        if not hasattr(self, 'combo_spatial_mode'):
            return
        self._ref_combo_populating = True
        named_layers = self._get_selected_layers(self.target_layer_list)
        ref_layers = self._get_selected_layers(self.ref_layer_list)
        prev_named = self.combo_named_field.currentData()
        prev_ref = self.combo_ref_field.currentData()
        prev_spatial = self.combo_spatial_mode.currentData()
        prev_multi = self.combo_multi_match.currentData()
        if self._restore_field_named is not None:
            prev_named = self._restore_field_named
        if self._restore_field_ref is not None:
            prev_ref = self._restore_field_ref
        if self._restore_field_spatial is not None:
            prev_spatial = self._restore_field_spatial
        if self._restore_field_multi is not None:
            prev_multi = self._restore_field_multi
        self._restore_field_named = None
        self._restore_field_ref = None
        self._restore_field_spatial = None
        self._restore_field_multi = None
        self.combo_named_field.blockSignals(True)
        self.combo_ref_field.blockSignals(True)
        self.combo_spatial_mode.blockSignals(True)
        self.combo_multi_match.blockSignals(True)
        self.combo_named_field.clear()
        self.combo_ref_field.clear()
        self.combo_spatial_mode.clear()
        if named_layers:
            names = _field_intersection(named_layers)
            if not names:
                for i in range(named_layers[0].fields().count()):
                    f = named_layers[0].fields().at(i)
                    self.combo_named_field.addItem(field_display_label(f), f.name())
            else:
                for n in names:
                    self.combo_named_field.addItem(
                        field_display_label_from_layer(named_layers[0], n), n
                    )
        if ref_layers:
            self.combo_ref_field.addItem(self.tr('图层名称'), LAYER_NAME_VALUE)
            self.combo_ref_field.addItem(
                self._ref_count_combo_display_text(),
                REF_ELEMENT_COUNT,
            )
            r0 = ref_layers[0]
            for i in range(r0.fields().count()):
                f = r0.fields().at(i)
                self.combo_ref_field.addItem(field_display_label(f), f.name())
        if named_layers and ref_layers:
            add_mode_items(self.combo_spatial_mode, spatial_mode_choices(named_layers[0], ref_layers[0]))
        if prev_named is not None:
            idx = self.combo_named_field.findData(prev_named)
            if idx < 0 and named_layers:
                resolved = resolve_field_name(named_layers[0], prev_named)
                if resolved:
                    idx = self.combo_named_field.findData(resolved)
            if idx >= 0:
                self.combo_named_field.setCurrentIndex(idx)
        if prev_ref is not None:
            idx = self.combo_ref_field.findData(prev_ref)
            if idx < 0 and prev_ref not in (LAYER_NAME_VALUE, REF_ELEMENT_COUNT) and ref_layers:
                resolved = resolve_field_name(ref_layers[0], prev_ref)
                if resolved:
                    idx = self.combo_ref_field.findData(resolved)
            if idx >= 0:
                self.combo_ref_field.setCurrentIndex(idx)
        if prev_spatial is not None:
            idx = self.combo_spatial_mode.findData(prev_spatial)
            if idx >= 0:
                self.combo_spatial_mode.setCurrentIndex(idx)
        if self.combo_spatial_mode.count() > 0 and self.combo_spatial_mode.currentIndex() < 0:
            self.combo_spatial_mode.setCurrentIndex(0)
        idx_cnt = self.combo_ref_field.findData(REF_ELEMENT_COUNT)
        if idx_cnt >= 0:
            self.combo_ref_field.setItemText(idx_cnt, self._ref_count_combo_display_text())
        self._update_multi_match_for_ref_source()
        if prev_multi is not None:
            idx = self.combo_multi_match.findData(prev_multi)
            if idx >= 0:
                self.combo_multi_match.setCurrentIndex(idx)
        self._fill_end_field_combos(named_layers, ref_layers)
        self.combo_named_field.blockSignals(False)
        self.combo_ref_field.blockSignals(False)
        self.combo_spatial_mode.blockSignals(False)
        self.combo_multi_match.blockSignals(False)
        self._ref_combo_populating = False
        self._sync_end_field_rows()
        self._sync_combo_tips()

    def _refresh_snap_spatial_combo(self):
        if not hasattr(self, 'combo_snap_spatial_mode'):
            return
        ref_mode = self._effective_snap_ref_mode()
        named_layers = self._get_selected_layers(self.target_layer_list)
        ref_layers = self._get_selected_layers(self.ref_layer_list)
        prev_sp = self.combo_snap_spatial_mode.currentData()
        if self._restore_snap_spatial is not None:
            prev_sp = self._restore_snap_spatial
        self._restore_snap_spatial = None
        self.combo_snap_spatial_mode.blockSignals(True)
        self.combo_snap_spatial_mode.clear()
        if ref_mode and ref_mode != 'standard':
            self.combo_snap_spatial_mode.addItem(
                self.tr('（特殊检测，无需空间命名模式）'),
                '__special__',
            )
            self.combo_snap_spatial_mode.setEnabled(False)
        else:
            self.combo_snap_spatial_mode.setEnabled(True)
            if named_layers and ref_layers:
                add_mode_items(
                    self.combo_snap_spatial_mode,
                    [e for e in spatial_mode_choices(named_layers[0], ref_layers[0]) if e[0] != LP_END_FIELDS],
                )
        if prev_sp is not None:
            ix = self.combo_snap_spatial_mode.findData(prev_sp)
            if ix >= 0:
                self.combo_snap_spatial_mode.setCurrentIndex(ix)
        if self.combo_snap_spatial_mode.count() > 0 and self.combo_snap_spatial_mode.currentIndex() < 0:
            self.combo_snap_spatial_mode.setCurrentIndex(0)
        self.combo_snap_spatial_mode.blockSignals(False)
        self._sync_combo_tips()

    def _get_selected_layers(self, list_widget):
        layers = []
        for item in list_widget.selectedItems():
            data = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(data, dict) and data.get('uri'):
                lyr = QgsVectorLayer(data['uri'], data.get('name', item.text()), 'ogr')
                if lyr.isValid():
                    layers.append(lyr)
                continue
            name = self._item_layer_name(item)
            found = self.project.mapLayersByName(name)
            if found:
                layers.append(found[0])
        return layers

    def _refresh_snap_scheme_combo(self):
        self.combo_snap_scheme.blockSignals(True)
        self.combo_snap_scheme.clear()
        self.combo_snap_scheme.addItem(self.tr('自定义方案（当前）'), self.SNAP_SCHEME_CUSTOM)
        for name in sorted(self._snap_schemes.keys()):
            self.combo_snap_scheme.addItem(name, name)
        idx = self.combo_snap_scheme.findData(self._active_snap_scheme)
        if idx < 0:
            self._active_snap_scheme = self.SNAP_SCHEME_CUSTOM
            idx = self.combo_snap_scheme.findData(self.SNAP_SCHEME_CUSTOM)
        if idx >= 0:
            self.combo_snap_scheme.setCurrentIndex(idx)
        self.combo_snap_scheme.blockSignals(False)
        self._update_scheme_btn_states()

    def _update_scheme_btn_states(self):
        is_custom = self._active_snap_scheme == self.SNAP_SCHEME_CUSTOM
        has_scheme = (not is_custom) and (self._active_snap_scheme in self._snap_schemes)
        self.btn_scheme_view.setEnabled(has_scheme)
        # Shared import/export must stay usable even when the snap library is empty.
        self.btn_scheme_export.setEnabled(True)
        if hasattr(self, 'btn_scheme_import'):
            self.btn_scheme_import.setEnabled(True)
        self._update_scheme_layer_match_label()

    def _show_scheme_manage_menu(self):
        menu = QMenu(self)
        menu.addAction(self.tr('新建')).triggered.connect(lambda: self._create_snap_scheme())
        is_custom = self._active_snap_scheme == self.SNAP_SCHEME_CUSTOM
        has_scheme = (not is_custom) and (self._active_snap_scheme in self._snap_schemes)
        act_rename = menu.addAction(self.tr('重命名'))
        act_rename.triggered.connect(lambda: self._rename_snap_scheme())
        act_rename.setEnabled(has_scheme)
        act_del = menu.addAction(self.tr('删除'))
        act_del.triggered.connect(lambda: self._delete_snap_scheme())
        act_del.setEnabled(has_scheme)
        act_dup = menu.addAction(self.tr('复制方案'))
        act_dup.triggered.connect(lambda: self._duplicate_snap_scheme())
        act_dup.setEnabled(has_scheme)
        run_menu(menu, self.btn_scheme_manage.mapToGlobal(self.btn_scheme_manage.rect().bottomLeft()))

    def _duplicate_snap_scheme(self):
        old = self._active_snap_scheme
        if old == self.SNAP_SCHEME_CUSTOM or old not in self._snap_schemes:
            QMessageBox.information(
                self, self.tr('提示'),
                self.tr('请先选择一个要复制的方案（非「自定义方案」）。'),
            )
            return
        suffix = self.tr('副本')
        base = '{0}{1}'.format(old, suffix)
        new_name = base
        n = 2
        while new_name in self._snap_schemes:
            new_name = '{0}{1}'.format(base, n)
            n += 1
        self._snap_schemes[new_name] = copy.deepcopy(self._snap_schemes[old])
        if old in self._snap_group_orders:
            self._snap_group_orders[new_name] = copy.deepcopy(self._snap_group_orders[old])
        else:
            self._ensure_group_in_order(new_name, self.UNGROUPED_KEY)
        self._active_snap_scheme = new_name
        self._refresh_snap_scheme_combo()
        self._persist_settings()
        QMessageBox.information(
            self, self.tr('提示'),
            self.tr('已复制为新方案「{0}」。').format(new_name),
        )

    def _on_snap_scheme_changed(self, _idx):
        d = self.combo_snap_scheme.currentData()
        self._active_snap_scheme = d if d else self.SNAP_SCHEME_CUSTOM
        self._update_scheme_btn_states()

    def _create_snap_scheme(self):
        name, ok = ask_text(self, self.tr('新建方案'), self.tr('请输入方案名称：'))
        if not ok:
            return
        name = (name or '').strip()
        if not name:
            QMessageBox.warning(self, self.tr('提示'), self.tr('请输入未占用的方案名称。'))
            return
        if name == self.SNAP_SCHEME_CUSTOM or name in self._snap_schemes:
            QMessageBox.warning(self, self.tr('提示'), self.tr('方案名称已存在，请更换名称。'))
            return
        self._snap_schemes[name] = []
        self._ensure_group_in_order(name, self.UNGROUPED_KEY)
        self._active_snap_scheme = name
        self._refresh_snap_scheme_combo()
        self._persist_settings()

    def _rename_snap_scheme(self):
        old = self._active_snap_scheme
        if old == self.SNAP_SCHEME_CUSTOM or old not in self._snap_schemes:
            return
        name, ok = ask_text(self, self.tr('重命名方案'), self.tr('请输入新名称：'), text=old)
        if not ok:
            return
        name = (name or '').strip()
        if not name:
            QMessageBox.warning(self, self.tr('提示'), self.tr('请输入未占用的方案名称。'))
            return
        if name == old:
            return
        if name == self.SNAP_SCHEME_CUSTOM or name in self._snap_schemes:
            QMessageBox.warning(self, self.tr('提示'), self.tr('方案名称已存在，请更换名称。'))
            return
        self._snap_schemes[name] = self._snap_schemes.pop(old)
        if old in self._snap_group_orders:
            self._snap_group_orders[name] = self._snap_group_orders.pop(old)
        self._active_snap_scheme = name
        self._refresh_snap_scheme_combo()
        self._persist_settings()

    def _delete_snap_scheme(self):
        name = self._active_snap_scheme
        if name == self.SNAP_SCHEME_CUSTOM or name not in self._snap_schemes:
            return
        reply = QMessageBox.question(
            self,
            self.tr('删除方案'),
            self.tr('确定删除方案「{0}」及其全部子任务吗？').format(name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._snap_schemes.pop(name, None)
        self._snap_group_orders.pop(name, None)
        self._active_snap_scheme = self.SNAP_SCHEME_CUSTOM
        self._refresh_snap_scheme_combo()
        self._persist_settings()

    def _classify_scheme_payload(self, payload):
        """Identify a file: bundle, field, move, snap (no kind), or unknown/invalid."""
        if not isinstance(payload, dict):
            return 'invalid'
        if is_scheme_bundle(payload):
            return 'bundle'
        kind = payload.get('kind')
        if is_field_scheme_kind(kind):
            return 'field'
        if is_move_scheme_kind(kind):
            return 'move'
        if is_snap_scheme_kind(kind):
            return 'snap'
        if kind:
            return 'unknown'
        return 'snap'

    def _pick_export_scope(self):
        # QMenu like the language menu, but options have no checkboxes.
        menu = QMenu(self)
        chosen = {'key': None}

        def _pick(key):
            chosen['key'] = key

        try:
            from .icons import load_icon
        except ImportError:
            from icons import load_icon
        act_all = menu.addAction(load_icon('export_all'), self.tr('全部导出'))
        act_all.setCheckable(False)
        act_all.triggered.connect(lambda _checked=False: _pick('all'))
        for key, title in (
            ('snap', self.tr('吸附检测')),
            ('field', self.tr('字段命名')),
            ('move', self.tr('移动')),
        ):
            act = menu.addAction(mode_icon(key), title)
            act.setCheckable(False)
            act.triggered.connect(lambda _checked=False, k=key: _pick(k))
        anchor = getattr(self, 'btn_scheme_export', None) or self
        run_menu(menu, anchor.mapToGlobal(anchor.rect().bottomLeft()))
        return chosen['key']


    def _json_save_path(self, path):
        path = (path or '').strip()
        if path and not path.lower().endswith('.json'):
            path += '.json'
        return path

    def _pick_checked_names(self, title, names):
        """Checkbox list. A click on empty space does not clear the checks."""
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setMinimumWidth(360)
        dlg.setMinimumHeight(320)
        lay = QVBoxLayout(dlg)
        lw = QListWidget()
        lw.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        for name in names:
            it = QListWidgetItem(name)
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            it.setCheckState(Qt.CheckState.Checked)
            lw.addItem(it)
        lay.addWidget(lw, 1)
        row = QHBoxLayout()
        btn_all = QPushButton(self.tr('全选'))
        btn_none = QPushButton(self.tr('全不选'))

        def _set_all(checked):
            state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
            for i in range(lw.count()):
                lw.item(i).setCheckState(state)

        btn_all.clicked.connect(lambda: _set_all(True))
        btn_none.clicked.connect(lambda: _set_all(False))
        row.addWidget(btn_all)
        row.addWidget(btn_none)
        row.addStretch(1)
        lay.addLayout(row)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        localize_button_box(bb)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        lay.addWidget(bb)
        if run_dialog(dlg) != QDialog.DialogCode.Accepted:
            return None
        picked = []
        for i in range(lw.count()):
            it = lw.item(i)
            if it.checkState() == Qt.CheckState.Checked:
                picked.append(it.text())
        return picked

    def _export_schemes_shared(self):
        """Shared top-bar export: pick all or one function. Does not change the current mode."""
        scope = self._pick_export_scope()
        if not scope:
            return
        if scope == 'snap':
            self._export_snap_schemes()
            return
        if scope == 'field':
            self._export_field_schemes()
            return
        if scope == 'move':
            self._export_move_schemes()
            return
        # all: pack every scheme in the three libraries, no per-scheme picker
        snap = dict(self._snap_schemes or {})
        field = {k: v for k, v in (self._field_schemes or {}).items() if isinstance(v, list)}
        move = {k: v for k, v in (self._move_schemes or {}).items() if isinstance(v, list)}
        orders = {
            k: list(v)
            for k, v in (self._snap_group_orders or {}).items()
            if k in snap
        }
        if not snap and not field and not move:
            QMessageBox.information(self, self.tr('提示'), self.tr('三个功能都没有可导出的方案。'))
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr('导出方案'),
            'spatial_match_topo_adjust_schemes_bundle.json',
            'JSON (*.json)',
        )
        path = self._json_save_path(path)
        if not path:
            return
        payload = make_bundle(snap, orders, field, move, plugin_version=PLUGIN_VERSION)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            QMessageBox.information(
                self, self.tr('提示'), self.tr('已把三个功能的全部方案写入总包。')
            )
        except Exception as exc:
            QMessageBox.warning(self, self.tr('提示'), self.tr('导出失败：{0}').format(str(exc)))

    def _import_schemes_shared(self):
        """Shared top-bar import: auto-detect and write the matching library. Does not change mode."""
        path, _ = QFileDialog.getOpenFileName(self, self.tr('导入方案'), '', 'JSON (*.json)')
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
        except Exception as exc:
            QMessageBox.warning(self, self.tr('提示'), self.tr('导入失败：{0}').format(str(exc)))
            return
        kind = self._classify_scheme_payload(payload)
        if kind == 'bundle':
            self._import_scheme_bundle(payload)
            return
        if kind == 'field':
            counts = self._merge_field_from_payload(payload)
        elif kind == 'move':
            counts = self._merge_move_from_payload(payload)
        elif kind == 'snap':
            counts = self._merge_snap_from_payload(payload)
        else:
            QMessageBox.warning(
                self,
                self.tr('提示'),
                self.tr('无法识别该文件。它不是 Spatial Match & Topo Adjust 的方案或方案总包，未写入任何方案库。'),
            )
            return
        if counts is None:
            return
        merged, overwritten, empty_msg = counts
        if merged == 0:
            QMessageBox.warning(self, self.tr('提示'), empty_msg or self.tr('文件里没有可导入的方案。'))
            return
        if kind == 'field':
            msg = self.tr('导入完成：共 {0} 个命名方案（其中同名覆盖 {1} 个）。').format(merged, overwritten)
        elif kind == 'move':
            msg = self.tr('导入完成：共 {0} 个移动方案（其中同名覆盖 {1} 个）。').format(merged, overwritten)
        else:
            msg = self.tr(
                '导入完成：共 {0} 个方案（其中同名覆盖 {1} 个）；'
                '未出现在导入文件中的本地其它方案已保留。'
            ).format(merged, overwritten)
        QMessageBox.information(self, self.tr('提示'), msg)

    def _import_scheme_bundle(self, payload):
        libs = bundle_libraries(payload)
        if not isinstance(libs, dict):
            QMessageBox.warning(
                self, self.tr('提示'),
                self.tr('无法识别该文件。它不是 Spatial Match & Topo Adjust 的方案或方案总包，未写入任何方案库。'),
            )
            return
        snap_c = self._merge_snap_from_payload({
            'schemes': (libs.get(LIB_SNAP) or {}).get('schemes') if isinstance(libs.get(LIB_SNAP), dict) else {},
            'group_orders': (libs.get(LIB_SNAP) or {}).get('group_orders') if isinstance(libs.get(LIB_SNAP), dict) else {},
        }) or (0, 0, None)
        field_c = self._merge_field_from_payload({
            'schemes': (libs.get(LIB_FIELD) or {}).get('schemes') if isinstance(libs.get(LIB_FIELD), dict) else {},
        }) or (0, 0, None)
        move_c = self._merge_move_from_payload({
            'schemes': (libs.get(LIB_MOVE) or {}).get('schemes') if isinstance(libs.get(LIB_MOVE), dict) else {},
        }) or (0, 0, None)
        total = snap_c[0] + field_c[0] + move_c[0]
        if total == 0:
            QMessageBox.warning(self, self.tr('提示'), self.tr('总包里没有可导入的方案。'))
            return
        QMessageBox.information(
            self,
            self.tr('提示'),
            self.tr(
                '导入完成：吸附 {0} 个，字段命名 {1} 个，移动 {2} 个'
                '（同名覆盖：吸附 {3}，字段命名 {4}，移动 {5}）。'
            ).format(snap_c[0], field_c[0], move_c[0], snap_c[1], field_c[1], move_c[1]),
        )

    def _merge_field_from_payload(self, payload):
        incoming = payload.get('schemes') if isinstance(payload, dict) else None
        if not isinstance(incoming, dict):
            return (0, 0, self.tr('文件格式无效。'))
        merged = 0
        overwritten = 0
        for name, body in incoming.items():
            if not isinstance(name, str) or not name or name == self.FIELD_SCHEME_CUSTOM:
                continue
            if not isinstance(body, list):
                continue
            if name in self._field_schemes:
                overwritten += 1
            self._field_schemes[name] = [self._clean_field_task(t) for t in body if isinstance(t, dict)]
            merged += 1
        self._refresh_field_scheme_combo()
        self._persist_settings()
        return (merged, overwritten, self.tr('文件里没有子任务列表。'))

    def _report_move_import_skips(self, skips):
        if not skips:
            return
        lines = []
        for scheme, task, mode in skips:
            lines.append(self.tr('方案「{0}」子任务「{1}」：模式「{2}」').format(scheme, task, mode))
        QMessageBox.warning(
            self,
            self.tr('提示'),
            self.tr('导入已跳过含已撤线-线移动模式的子任务，这些条目未写入方案库：') + '\n' + '\n'.join(lines),
        )

    def _merge_move_from_payload(self, payload):
        incoming = payload.get('schemes') if isinstance(payload, dict) else None
        if not isinstance(incoming, dict):
            return (0, 0, self.tr('文件格式无效。'))
        merged = 0
        overwritten = 0
        skips = []
        for name, body in incoming.items():
            if not isinstance(name, str) or not name or name == self.MOVE_SCHEME_CUSTOM:
                continue
            if not isinstance(body, list):
                continue
            kept = []
            for task in body:
                if not isinstance(task, dict):
                    continue
                mode = str(task.get('move_mode') or 'standard')
                if is_withdrawn_line_line_mode(mode):
                    title = task.get('method_name') or task.get('run_name') or ''
                    skips.append((name, title, mode))
                    continue
                kept.append(self._clean_move_task(task))
            if not kept:
                continue
            if name in self._move_schemes:
                overwritten += 1
            self._move_schemes[name] = kept
            merged += 1
        self._refresh_move_scheme_combo()
        self._persist_settings()
        self._last_move_import_skips = skips
        self._report_move_import_skips(skips)
        return (merged, overwritten, self.tr('文件里没有可导入的移动子任务列表。'))

    def _pick_schemes_for_export(self):
        """弹出勾选列表，返回所选方案名称列表；取消返回 None。"""
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr('选择要导出的方案'))
        dlg.setMinimumWidth(360)
        dlg.setMinimumHeight(320)
        lay = QVBoxLayout(dlg)
        lay.addWidget(
            QLabel(
                self.tr('勾选需要写入 JSON 的方案（可与导入文件格式一致合并导入）。'),
            ),
        )
        lw = QListWidget()
        lw.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        for name in sorted(self._snap_schemes.keys()):
            it = QListWidgetItem(name)
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            it.setCheckState(Qt.CheckState.Checked)
            lw.addItem(it)
        lay.addWidget(lw, 1)

        row_quick = QHBoxLayout()
        btn_all = QPushButton(self.tr('全选'))
        btn_none = QPushButton(self.tr('全不选'))

        def _set_all_checked(checked):
            for i in range(lw.count()):
                lw.item(i).setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

        btn_all.clicked.connect(lambda: _set_all_checked(True))
        btn_none.clicked.connect(lambda: _set_all_checked(False))
        row_quick.addWidget(btn_all)
        row_quick.addWidget(btn_none)
        row_quick.addStretch(1)
        lay.addLayout(row_quick)

        bbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        localize_button_box(bbox)
        bbox.accepted.connect(dlg.accept)
        bbox.rejected.connect(dlg.reject)
        lay.addWidget(bbox)

        if run_dialog(dlg) != QDialog.DialogCode.Accepted:
            return None
        picked = []
        for i in range(lw.count()):
            it = lw.item(i)
            if it.checkState() == Qt.CheckState.Checked:
                picked.append(it.text())
        return picked

    def _export_snap_schemes(self):
        if not self._snap_schemes:
            QMessageBox.information(self, self.tr('提示'), self.tr('暂无可导出的方案。'))
            return
        picked_names = self._pick_schemes_for_export()
        if picked_names is None:
            return
        if not picked_names:
            QMessageBox.information(self, self.tr('提示'), self.tr('请至少勾选一个方案。'))
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr('导出批量方案'),
            'spatial_match_topo_adjust_snap_schemes.json',
            'JSON (*.json)',
        )
        path = self._json_save_path(path)
        if not path:
            return
        subset_schemes = {k: self._snap_schemes[k] for k in picked_names if k in self._snap_schemes}
        payload = {
            'kind': SNAP_SCHEME_KIND,
            'schema_version': 2,
            'plugin_version': PLUGIN_VERSION,
            'generator': DISPLAY_NAME,
            'exported_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'schemes': subset_schemes,
            'group_orders': {
                k: list(v)
                for k, v in self._snap_group_orders.items()
                if k in subset_schemes
            },
        }
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            QMessageBox.information(
                self,
                self.tr('提示'),
                self.tr('已导出 {0} 个方案。').format(len(subset_schemes)),
            )
        except Exception as e:
            QMessageBox.warning(self, self.tr('提示'), self.tr('导出失败：{0}').format(str(e)))

    def _open_memory_style_dialog(self):
        try:
            from .cdet_memory_style_dialog import CdetMemoryStyleDialog
        except ImportError:
            from cdet_memory_style_dialog import CdetMemoryStyleDialog
        dlg = CdetMemoryStyleDialog(self)
        run_dialog(dlg)

    def _merge_snap_from_payload(self, payload):
        incoming = payload.get('schemes', payload if isinstance(payload, dict) else {})
        if not isinstance(incoming, dict):
            return (0, 0, self.tr('文件格式无效。'))

        incoming_orders = payload.get('group_orders') if isinstance(payload, dict) else None
        if not isinstance(incoming_orders, dict):
            incoming_orders = {}

        # 同名方案：以导入文件中的定义完全覆盖；导入文件中未出现的本地方案名称保留不变。
        merged = 0
        overwritten = 0
        for name, tasks in incoming.items():
            if not isinstance(name, str) or not name or name == self.SNAP_SCHEME_CUSTOM:
                continue
            if not isinstance(tasks, list):
                continue
            dst_name = name
            if dst_name in self._snap_schemes:
                overwritten += 1
            norm = []
            for t in tasks:
                if not isinstance(t, dict):
                    continue
                entry = {
                    'run_name': str(t.get('run_name', time.strftime('%Y%m%d_%H%M%S'))),
                    'method_name': str(t.get('method_name', t.get('run_name', ''))),
                    'target_names': list(t.get('target_names', [])),
                    'ref_names': list(t.get('ref_names', [])),
                    'spatial_mode': t.get('spatial_mode'),
                    'tolerance': float(t.get('tolerance', 0.00001)),
                    'snap_enabled': bool(t.get('snap_enabled', True)),
                }
                t_cats = normalize_category_map(t.get('target_categories'))
                r_cats = normalize_category_map(t.get('ref_categories'))
                if t_cats:
                    entry['target_categories'] = t_cats
                if r_cats:
                    entry['ref_categories'] = r_cats
                gk_in = t.get('_group')
                entry['_group'] = self._normalize_group_key(gk_in)
                sp = t.get('_snap_special') or ''
                if sp in SPECIAL_KEYS:
                    entry['_snap_special'] = sp
                    po = t.get('_polygon_outputs')
                    if isinstance(po, list) and po:
                        entry['_polygon_outputs'] = list(po)
                    elif t.get('_polygon_submode'):
                        entry['_polygon_outputs'] = [str(t.get('_polygon_submode'))]
                    entry['_polygon_area_tol_m2'] = float(t.get('_polygon_area_tol_m2', 1.0))
                    entry['_polygon_overlap_area_tol_m2'] = float(
                        t.get('_polygon_overlap_area_tol_m2', t.get('_polygon_area_tol_m2', 1.0))
                    )
                    entry['_line_length_rule'] = dict(t.get('_line_length_rule') or {'kind': 'le', 'threshold': 0})
                    entry['_snap_count_rule'] = dict(t.get('_snap_count_rule') or {'kind': 'le', 'threshold': 0})
                    entry['_count_attach'] = normalize_count_attach(t.get('_count_attach'))
                    entry['_count_output_mates'] = bool(t.get('_count_output_mates'))
                    if sp == 'overlap_grp':
                        ok = str(t.get('_overlap_kind') or 'auto').strip()
                        if ok not in ('auto', 'point', 'line', 'polygon'):
                            ok = 'polygon'
                        entry['_overlap_kind'] = ok
                    else:
                        ok = t.get('_overlap_kind')
                        if ok:
                            entry['_overlap_kind'] = ok
                    entry['_overlap_scope'] = normalize_overlap_scope(str(t.get('_overlap_scope') or 'per_layer'))
                    entry['_line_overlap_min_length'] = float(t.get('_line_overlap_min_length', 0.0))
                    entry['_point_line_chain_min_seg'] = int(t.get('_point_line_chain_min_seg', 3))
                    entry.update(normalize_special_values(t))
                if t.get('mode_param') is not None:
                    entry['mode_param'] = t.get('mode_param')
                norm.append(entry)
            self._snap_schemes[dst_name] = norm
            order_in = incoming_orders.get(name)
            if isinstance(order_in, list) and order_in:
                self._set_scheme_group_order(dst_name, [str(x) for x in order_in])
            else:
                self._ensure_group_in_order(dst_name, self.UNGROUPED_KEY)
            merged += 1
        self._refresh_snap_scheme_combo()
        self._persist_settings()
        return (merged, overwritten, self.tr('文件里没有可导入的方案。'))


    def _import_snap_schemes(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr('导入批量方案'),
            '',
            'JSON (*.json)',
        )
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, self.tr('提示'), self.tr('导入失败：{0}').format(str(e)))
            return
        if isinstance(payload, dict) and is_field_scheme_kind(payload.get('kind')):
            QMessageBox.warning(self, self.tr('提示'), self.tr('这是字段命名方案，请在字段命名里导入。'))
            return
        if isinstance(payload, dict) and is_move_scheme_kind(payload.get('kind')):
            QMessageBox.warning(self, self.tr('提示'), self.tr('这是移动方案，请在移动模式里导入（方案库与吸附分存）。'))
            return
        counts = self._merge_snap_from_payload(payload)
        if counts is None:
            return
        merged, overwritten, empty_msg = counts
        if merged == 0:
            QMessageBox.warning(self, self.tr('提示'), empty_msg or self.tr('文件格式无效。'))
            return
        QMessageBox.information(
            self,
            self.tr('提示'),
            self.tr(
                '导入完成：共 {0} 个方案（其中同名覆盖 {1} 个）；'
                '未出现在导入文件中的本地其它方案已保留。'
            ).format(merged, overwritten),
        )

    def _next_scheme_name(self, base_name):
        if base_name not in self._snap_schemes:
            return base_name
        idx = 2
        while True:
            cand = f'{base_name}_{idx}'
            if cand not in self._snap_schemes:
                return cand
            idx += 1

    def _current_snap_task_payload(self):
        t_names = [self._item_layer_name(i) for i in self.target_layer_list.selectedItems()]
        r_names = [self._item_layer_name(i) for i in self.ref_layer_list.selectedItems()]
        ref_mode = self._effective_snap_ref_mode()
        ssm = self.combo_snap_spatial_mode.currentData()
        if ref_mode != 'standard':
            ssm = ssm or '__special__'
        if not t_names:
            return None
        base = {
            'method_name': '',
            'run_name': time.strftime('%Y%m%d_%H%M%S'),
            'target_names': t_names,
            'ref_names': list(r_names),
            'spatial_mode': ssm,
            'tolerance': float(self.spin_tolerance.value()),
            'snap_enabled': bool(self.chk_snap.isChecked()),
        }
        t_cats = self._categories_map_from_list(self.target_layer_list)
        r_cats = self._categories_map_from_list(self.ref_layer_list)
        if t_cats:
            base['target_categories'] = t_cats
        if r_cats:
            base['ref_categories'] = r_cats
        if ref_mode == 'standard':
            if not r_names or not ssm:
                return None
            mp = self._current_mode_param(ssm)
            if mp is not None:
                base['mode_param'] = mp
            return base
        atol = float(self.spin_overlap_area_tol.value())
        okind = self._overlap_kind_auto()
        allowed = SPECIAL_TARGET_GEOMS.get(ref_mode)
        if allowed:
            gname = {
                QgsWkbTypes.GeometryType.PointGeometry: 'point',
                QgsWkbTypes.GeometryType.LineGeometry: 'line',
                QgsWkbTypes.GeometryType.PolygonGeometry: 'polygon',
            }.get(self._snap_target_geom_uniform())
            if gname not in allowed:
                return None
        if ref_mode in SPECIAL_REF_GEOM and not r_names:
            return None
        if ref_mode == 'polygon_inspect' and not self._polygon_outputs_selected():
            return None
        base['_snap_special'] = ref_mode
        base['_polygon_outputs'] = list(self._polygon_outputs_selected())
        base['_polygon_area_tol_m2'] = atol
        base['_polygon_overlap_area_tol_m2'] = atol
        base['_line_length_rule'] = dict(self._line_length_rule)
        base['_snap_count_rule'] = dict(self._snap_count_rule)
        base['_count_attach'] = normalize_count_attach(self._count_attach)
        base['_count_output_mates'] = bool(self._count_output_mates)
        base['_overlap_scope'] = normalize_overlap_scope(self.combo_overlap_scope.currentData())
        base['_line_overlap_min_length'] = float(self.spin_line_overlap_min.value())
        base['_point_line_chain_min_seg'] = int(self.spin_chain_min_seg.value())
        if ref_mode == 'overlap_grp':
            base['_overlap_kind'] = okind or 'auto'
        elif okind:
            base['_overlap_kind'] = okind
        base.update(normalize_special_values(self._special_values))
        return base

    def _choose_scheme_names_dialog(self):
        names = sorted(self._snap_schemes.keys())
        if not names:
            QMessageBox.information(self, self.tr('提示'), self.tr('暂无可加入的方案，请先新建方案。'))
            return []
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr('加入到方案组'))
        lay = QVBoxLayout(dlg)
        lw = QListWidget()
        lw.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for n in names:
            lw.addItem(n)
        lay.addWidget(lw)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        localize_button_box(bb)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        lay.addWidget(bb)
        if run_dialog(dlg) != QDialog.DialogCode.Accepted:
            return []
        return [i.text() for i in lw.selectedItems()]

    def _add_current_to_schemes(self):
        payload = self._current_snap_task_payload()
        if not payload:
            QMessageBox.warning(
                self,
                self.tr('提示'),
                self.tr('请先正确选择判断图层（及标准模式下的参考图层与空间命名模式）。'),
            )
            return
        mname, ok = ask_text(self, self.tr('方法名称'), self.tr('请输入本次添加的方法名称：'))
        if not ok:
            return
        mname = (mname or '').strip()
        if not mname:
            mname = time.strftime('%Y%m%d_%H%M%S')
        payload['method_name'] = mname
        payload['run_name'] = mname
        chosen = self._choose_scheme_names_dialog()
        if not chosen:
            return
        for name in chosen:
            tasks = self._snap_schemes.setdefault(name, [])
            entry = dict(payload)
            entry['_group'] = self.UNGROUPED_KEY
            tasks.append(entry)
            self._ensure_group_in_order(name, self.UNGROUPED_KEY)
        self._persist_settings()
        QMessageBox.information(self, self.tr('提示'), self.tr('已加入 {0} 个方案组。').format(len(chosen)))

    # ===== 分组数据访问与维护 =====
    def _ungrouped_label(self):
        return self.tr('未分组')

    def _normalize_group_key(self, key):
        if key is None:
            return self.UNGROUPED_KEY
        s = str(key).strip()
        if not s:
            return self.UNGROUPED_KEY
        return s

    def _task_group(self, task):
        return self._normalize_group_key(task.get('_group') if isinstance(task, dict) else None)

    def _set_task_group(self, task, group_key):
        gk = self._normalize_group_key(group_key)
        if isinstance(task, dict):
            task['_group'] = gk

    def _scheme_group_order(self, scheme_name):
        """返回当前方案的组顺序列表（始终包含未分组）。"""
        order = list(self._snap_group_orders.get(scheme_name) or [])
        groups_in_use = []
        for t in self._snap_schemes.get(scheme_name, []) or []:
            gk = self._task_group(t)
            if gk not in groups_in_use:
                groups_in_use.append(gk)
        cleaned = [g for g in order if g == self.UNGROUPED_KEY or g in groups_in_use or g in order]
        seen = set()
        result = []
        for g in cleaned:
            if g in seen:
                continue
            seen.add(g)
            result.append(g)
        for g in groups_in_use:
            if g not in seen:
                seen.add(g)
                result.append(g)
        if self.UNGROUPED_KEY not in seen:
            result.insert(0, self.UNGROUPED_KEY)
        return result

    def _set_scheme_group_order(self, scheme_name, order_list):
        seen = set()
        cleaned = []
        for g in order_list or []:
            gk = self._normalize_group_key(g)
            if gk in seen:
                continue
            seen.add(gk)
            cleaned.append(gk)
        if self.UNGROUPED_KEY not in seen:
            cleaned.insert(0, self.UNGROUPED_KEY)
        self._snap_group_orders[scheme_name] = cleaned

    def _ensure_group_in_order(self, scheme_name, group_key):
        gk = self._normalize_group_key(group_key)
        order = list(self._snap_group_orders.get(scheme_name) or [])
        if not order:
            order = [self.UNGROUPED_KEY]
        if gk not in order:
            order.append(gk)
        if self.UNGROUPED_KEY not in order:
            order.insert(0, self.UNGROUPED_KEY)
        self._snap_group_orders[scheme_name] = order

    def _ordered_tasks_with_groups(self, scheme_name):
        """根据组顺序与组内顺序返回 [(group_key, task_index_in_arr), ...]。"""
        arr = self._snap_schemes.get(scheme_name, []) or []
        order = self._scheme_group_order(scheme_name)
        order_set = set(order)
        buckets = {g: [] for g in order}
        for idx, t in enumerate(arr):
            gk = self._task_group(t)
            if gk not in order_set:
                gk = self.UNGROUPED_KEY
                if gk not in buckets:
                    buckets[gk] = []
            buckets.setdefault(gk, []).append(idx)
        result = []
        for g in order:
            for idx in buckets.get(g, []):
                result.append((g, idx))
        return result

    def _group_display_name(self, key):
        if key == self.UNGROUPED_KEY:
            return self._ungrouped_label()
        return key

    def _view_current_scheme(self):
        name = self._active_snap_scheme
        if name == self.SNAP_SCHEME_CUSTOM or name not in self._snap_schemes:
            QMessageBox.information(self, self.tr('提示'), self.tr('请选择一个批量方案。'))
            return
        self._ensure_group_in_order(name, self.UNGROUPED_KEY)
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr('方案任务 - {0}').format(name))
        dlg.resize(940, 520)
        lay = QVBoxLayout(dlg)

        tree = QTreeWidget()
        tree.setColumnCount(1)
        tree.setHeaderHidden(True)
        tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        tree.setUniformRowHeights(False)
        tree.setRootIsDecorated(True)
        tree.setIndentation(18)
        tree.setExpandsOnDoubleClick(False)

        def _build_tree(preserve_expand=True, focus_payload=None):
            expand_state = {}
            if preserve_expand:
                root = tree.invisibleRootItem()
                for i in range(root.childCount()):
                    g_item = root.child(i)
                    gk = g_item.data(0, Qt.ItemDataRole.UserRole + 1)
                    expand_state[gk] = g_item.isExpanded()
            tree.clear()
            order = self._scheme_group_order(name)
            arr = self._snap_schemes.get(name, []) or []
            buckets = {g: [] for g in order}
            for idx, t in enumerate(arr):
                gk = self._task_group(t)
                buckets.setdefault(gk, []).append(idx)
                if gk not in order:
                    order.append(gk)
            counter = 0
            target_item = None
            for g in order:
                g_item = QTreeWidgetItem(tree)
                child_idxs = buckets.get(g, [])
                g_item.setText(0, self.tr('▸ {0}  ({1})').format(self._group_display_name(g), len(child_idxs)))
                g_item.setData(0, Qt.ItemDataRole.UserRole, ('group', g))
                g_item.setData(0, Qt.ItemDataRole.UserRole + 1, g)
                font = g_item.font(0)
                font.setBold(True)
                g_item.setFont(0, font)
                for idx in child_idxs:
                    counter += 1
                    t = arr[idx]
                    c_item = QTreeWidgetItem(g_item)
                    c_item.setText(0, self._task_display_text(counter, t))
                    c_item.setData(0, Qt.ItemDataRole.UserRole, ('task', idx))
                    c_item.setData(0, Qt.ItemDataRole.UserRole + 1, g)
                    if self._task_missing_layer_names(t):
                        c_item.setForeground(0, QBrush(QColor('#C62828')))
                    if focus_payload is not None and focus_payload[0] == 'task' and focus_payload[1] == idx:
                        target_item = c_item
                if focus_payload is not None and focus_payload[0] == 'group' and focus_payload[1] == g:
                    target_item = g_item
                want_expand = expand_state.get(g, True) if preserve_expand else True
                g_item.setExpanded(want_expand)
            if target_item is not None:
                tree.setCurrentItem(target_item)
                target_item.setSelected(True)

        _build_tree(preserve_expand=False)
        lay.addWidget(tree)

        # 底部一行：任务操作(4) + 分组操作(3) + 关闭；三组底色区分
        row = QHBoxLayout()
        row.setSpacing(6)
        btn_up = QPushButton(self.tr('上移'))
        btn_down = QPushButton(self.tr('下移'))
        btn_edit = QPushButton(self.tr('编辑选中'))
        btn_del = QPushButton(self.tr('删除选中'))
        btn_new_grp = QPushButton(self.tr('新建分组'))
        btn_rename_grp = QPushButton(self.tr('重命名分组'))
        btn_move_to = QPushButton(self.tr('移动到分组...'))
        btn_copy_to_scheme = QPushButton(self.tr('复制到其他方案'))
        btn_close = QPushButton(self.tr('关闭'))

        _bar_ss_task = (
            'QPushButton { background-color: #1565C0; color: #ffffff; border: 1px solid #0D47A1; '
            'border-radius: 4px; padding: 5px 10px; min-height: 22px; } '
            'QPushButton:hover { background-color: #1976D2; } '
            'QPushButton:pressed { background-color: #0D47A1; } '
            'QPushButton:disabled { background-color: #90CAF9; color: #E3F2FD; border-color: #64B5F6; }'
        )
        _bar_ss_group = (
            'QPushButton { background-color: #2E7D32; color: #ffffff; border: 1px solid #1B5E20; '
            'border-radius: 4px; padding: 5px 10px; min-height: 22px; } '
            'QPushButton:hover { background-color: #388E3C; } '
            'QPushButton:pressed { background-color: #1B5E20; } '
            'QPushButton:disabled { background-color: #A5D6A7; color: #E8F5E9; border-color: #81C784; }'
        )
        _bar_ss_close = (
            'QPushButton { background-color: #455A64; color: #ffffff; border: 1px solid #37474F; '
            'border-radius: 4px; padding: 5px 14px; min-height: 22px; } '
            'QPushButton:hover { background-color: #546E7A; } '
            'QPushButton:pressed { background-color: #37474F; } '
            'QPushButton:disabled { background-color: #B0BEC5; color: #ECEFF1; border-color: #90A4AE; }'
        )
        for b in (btn_up, btn_down, btn_edit, btn_del):
            b.setStyleSheet(_bar_ss_task)
        for b in (btn_new_grp, btn_rename_grp, btn_move_to, btn_copy_to_scheme):
            b.setStyleSheet(_bar_ss_group)
        btn_close.setStyleSheet(_bar_ss_close)

        row.addWidget(btn_up)
        row.addWidget(btn_down)
        row.addWidget(btn_edit)
        row.addWidget(btn_del)
        row.addWidget(btn_new_grp)
        row.addWidget(btn_rename_grp)
        row.addWidget(btn_move_to)
        row.addWidget(btn_copy_to_scheme)
        row.addStretch(1)
        row.addWidget(btn_close)
        lay.addLayout(row)

        def _selected_task_indices():
            s = set()
            for it in tree.selectedItems():
                d = it.data(0, Qt.ItemDataRole.UserRole)
                if d and d[0] == 'task':
                    s.add(d[1])
            return sorted(s)

        def _selected_group_keys():
            s = []
            for it in tree.selectedItems():
                d = it.data(0, Qt.ItemDataRole.UserRole)
                if d and d[0] == 'group':
                    s.append(d[1])
            return s

        def _current_payload():
            it = tree.currentItem()
            if it is None:
                return None
            data = it.data(0, Qt.ItemDataRole.UserRole)
            if not data:
                return None
            return data  # ('task', idx) 或 ('group', group_key)

        # ---- 分组管理 ----
        def _list_user_groups():
            return [g for g in self._scheme_group_order(name) if g != self.UNGROUPED_KEY]

        def _is_group_name_used(gname):
            return gname == self._ungrouped_label() or gname in self._scheme_group_order(name)

        def _new_group():
            gname, ok = ask_text(self, self.tr('新建分组'), self.tr('请输入分组名称：'))
            if not ok:
                return
            gname = (gname or '').strip()
            if not gname:
                return
            if gname == self._ungrouped_label():
                QMessageBox.warning(self, self.tr('提示'), self.tr('该名称为系统保留，请更换。'))
                return
            if gname in self._scheme_group_order(name):
                QMessageBox.warning(self, self.tr('提示'), self.tr('分组名已存在。'))
                return
            order = list(self._scheme_group_order(name))
            order.append(gname)
            self._set_scheme_group_order(name, order)
            self._persist_settings()
            _build_tree(focus_payload=('group', gname))

        def _rename_group():
            payload = _current_payload()
            if not payload or payload[0] != 'group':
                QMessageBox.information(self, self.tr('提示'), self.tr('请先选中要重命名的分组。'))
                return
            gk = payload[1]
            if gk == self.UNGROUPED_KEY:
                QMessageBox.information(self, self.tr('提示'), self.tr('「未分组」不可重命名。'))
                return
            new_name, ok = ask_text(self, self.tr('重命名分组'), self.tr('新名称：'), text=gk)
            if not ok:
                return
            new_name = (new_name or '').strip()
            if not new_name or new_name == gk:
                return
            if new_name == self._ungrouped_label():
                QMessageBox.warning(self, self.tr('提示'), self.tr('该名称为系统保留，请更换。'))
                return
            if new_name in self._scheme_group_order(name):
                QMessageBox.warning(self, self.tr('提示'), self.tr('分组名已存在。'))
                return
            for t in self._snap_schemes.get(name, []) or []:
                if self._task_group(t) == gk:
                    self._set_task_group(t, new_name)
            order = [new_name if g == gk else g for g in self._scheme_group_order(name)]
            self._set_scheme_group_order(name, order)
            self._persist_settings()
            _build_tree(focus_payload=('group', new_name))

        def _move_to_group():
            idxs = _selected_task_indices()
            if not idxs:
                QMessageBox.information(self, self.tr('提示'), self.tr('请先选中要移动的子任务（可多选）。'))
                return
            arr = self._snap_schemes.get(name, []) or []
            order = self._scheme_group_order(name)
            display = [self._group_display_name(g) for g in order]
            ref_idx = idxs[0]
            if ref_idx < 0 or ref_idx >= len(arr):
                return
            cur = self._task_group(arr[ref_idx])
            cur_disp = self._group_display_name(cur)
            try:
                cur_i = display.index(cur_disp)
            except ValueError:
                cur_i = 0
            chosen, ok = ask_item(
                self,
                self.tr('移动到分组'),
                self.tr('选择目标分组：'),
                display,
                cur_i,
                False,
            )
            if not ok or not chosen:
                return
            new_g = order[display.index(chosen)]
            for idx in idxs:
                if 0 <= idx < len(arr):
                    self._set_task_group(arr[idx], new_g)
            self._persist_settings()
            _build_tree(focus_payload=('task', idxs[0]))

        def _copy_to_other_scheme():
            idxs = _selected_task_indices()
            if not idxs:
                QMessageBox.information(
                    self, self.tr('提示'),
                    self.tr('请先选中要复制的子任务（可多选）。'),
                )
                return
            others = sorted(n for n in self._snap_schemes.keys() if n != name)
            if not others:
                QMessageBox.information(
                    self, self.tr('提示'),
                    self.tr('没有其他批量方案可复制，请先新建或导入方案。'),
                )
                return
            chosen, ok = ask_item(
                self,
                self.tr('复制到其他方案'),
                self.tr('选择目标方案：'),
                others,
                0,
                False,
            )
            if not ok or not chosen:
                return
            src_arr = self._snap_schemes.get(name, []) or []
            tgt_arr = self._snap_schemes.setdefault(chosen, [])
            n_copy = 0
            for idx in sorted(idxs):
                if 0 <= idx < len(src_arr):
                    t = copy.deepcopy(src_arr[idx])
                    tgt_arr.append(t)
                    self._ensure_group_in_order(chosen, self._task_group(t))
                    n_copy += 1
            self._persist_settings()
            QMessageBox.information(
                self, self.tr('提示'),
                self.tr('已将 {0} 个子任务复制到方案「{1}」。').format(n_copy, chosen),
            )

        # ---- 上/下移（通用） ----
        def _move_task_within_or_across(idx, step):
            arr = self._snap_schemes.get(name, []) or []
            if idx < 0 or idx >= len(arr):
                return
            cur_g = self._task_group(arr[idx])
            order = self._scheme_group_order(name)
            order_idx = order.index(cur_g) if cur_g in order else 0
            same_group_indices = [i for i, t in enumerate(arr) if self._task_group(t) == cur_g]
            pos_in_group = same_group_indices.index(idx)
            if step < 0:
                if pos_in_group > 0:
                    swap_with = same_group_indices[pos_in_group - 1]
                    arr[idx], arr[swap_with] = arr[swap_with], arr[idx]
                    self._persist_settings()
                    _build_tree(focus_payload=('task', swap_with))
                    return
                if order_idx > 0:
                    new_g = order[order_idx - 1]
                    self._set_task_group(arr[idx], new_g)
                    self._persist_settings()
                    _build_tree(focus_payload=('task', idx))
                    return
            else:
                if pos_in_group < len(same_group_indices) - 1:
                    swap_with = same_group_indices[pos_in_group + 1]
                    arr[idx], arr[swap_with] = arr[swap_with], arr[idx]
                    self._persist_settings()
                    _build_tree(focus_payload=('task', swap_with))
                    return
                if order_idx < len(order) - 1:
                    new_g = order[order_idx + 1]
                    self._set_task_group(arr[idx], new_g)
                    self._persist_settings()
                    _build_tree(focus_payload=('task', idx))
                    return

        def _move_group(gk, step):
            order = list(self._scheme_group_order(name))
            if gk not in order:
                return
            i = order.index(gk)
            j = i + step
            if j < 0 or j >= len(order):
                return
            order[i], order[j] = order[j], order[i]
            self._set_scheme_group_order(name, order)
            self._persist_settings()
            _build_tree(focus_payload=('group', gk))

        def _on_move(step):
            tidx = _selected_task_indices()
            gkeys = _selected_group_keys()
            if tidx and gkeys:
                QMessageBox.information(
                    self, self.tr('提示'),
                    self.tr('上移/下移时请只选择子任务，或只选择分组，不要混选。'),
                )
                return
            if len(tidx) > 1:
                QMessageBox.information(
                    self, self.tr('提示'),
                    self.tr('上移/下移请一次只选一个子任务；批量调整分组请用「移动到分组」。'),
                )
                return
            if len(gkeys) > 1:
                QMessageBox.information(self, self.tr('提示'), self.tr('上移/下移请一次只选一个分组。'))
                return
            if len(tidx) == 1:
                _move_task_within_or_across(tidx[0], step)
                return
            if len(gkeys) == 1:
                _move_group(gkeys[0], step)

        # ---- 编辑 ----
        def _edit_selected():
            tidx = _selected_task_indices()
            if len(tidx) != 1:
                QMessageBox.information(self, self.tr('提示'), self.tr('请只选中一个子任务进行编辑。'))
                return
            idx = tidx[0]
            arr = self._snap_schemes.get(name, []) or []
            if idx < 0 or idx >= len(arr):
                return
            old_group = self._task_group(arr[idx])
            edited = self._edit_task_dialog(dict(arr[idx]))
            if not edited:
                return
            edited['_group'] = old_group  # 保留分组归属
            arr[idx] = edited
            self._snap_schemes[name] = arr
            self._persist_settings()
            _build_tree(focus_payload=('task', idx))

        # ---- 删除 ----
        def _delete_selected():
            tidx = _selected_task_indices()
            gkeys = _selected_group_keys()
            if tidx and gkeys:
                QMessageBox.information(
                    self, self.tr('提示'),
                    self.tr('请勿同时选中子任务与分组；请先删除其中一类。'),
                )
                return
            arr = self._snap_schemes.get(name, []) or []
            if tidx:
                if QMessageBox.question(
                    self, self.tr('确认删除'),
                    self.tr('确定删除选中的 {0} 个子任务吗？').format(len(tidx)),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No,
                ) != QMessageBox.StandardButton.Yes:
                    return
                for ix in sorted(tidx, reverse=True):
                    if 0 <= ix < len(arr):
                        arr.pop(ix)
                self._snap_schemes[name] = arr
                self._persist_settings()
                _build_tree()
                return
            if len(gkeys) > 1:
                QMessageBox.information(self, self.tr('提示'), self.tr('删除分组请一次只选一个分组。'))
                return
            if len(gkeys) != 1:
                return
            gk = gkeys[0]
            if gk == self.UNGROUPED_KEY:
                QMessageBox.information(self, self.tr('提示'), self.tr('「未分组」不可删除。'))
                return
            in_group = [t for t in arr if self._task_group(t) == gk]
            if not in_group:
                order = [g for g in self._scheme_group_order(name) if g != gk]
                self._set_scheme_group_order(name, order)
                self._persist_settings()
                _build_tree()
                return
            # 自定义对话框：避免 QMessageBox 横向按钮文字被截断
            del_dlg = QDialog(dlg)
            del_dlg.setWindowTitle(self.tr('删除分组'))
            del_dlg.setMinimumWidth(460)
            del_lay = QVBoxLayout(del_dlg)
            del_lay.setSpacing(12)
            del_lay.setContentsMargins(16, 16, 16, 16)
            msg = QLabel(
                self.tr('分组「{0}」内有 {1} 个子任务，请选择操作：').format(gk, len(in_group))
            )
            msg.setWordWrap(True)
            del_lay.addWidget(msg)
            choice_holder = {'v': None}

            def _pick(val):
                choice_holder['v'] = val
                del_dlg.accept()

            btn_keep = QPushButton(self.tr('保留任务（移到「未分组」）'))
            btn_drop = QPushButton(self.tr('连任务一起删除'))
            btn_cancel = QPushButton(self.tr('取消'))
            btn_ss = (
                'QPushButton { text-align: left; padding: 10px 14px; min-height: 40px; '
                'border-radius: 4px; font-size: 13px; }'
            )
            btn_keep.setStyleSheet(
                btn_ss + 'QPushButton { background-color: #1565C0; color: #fff; border: 1px solid #0D47A1; } '
                'QPushButton:hover { background-color: #1976D2; }'
            )
            btn_drop.setStyleSheet(
                btn_ss + 'QPushButton { background-color: #C62828; color: #fff; border: 1px solid #B71C1C; } '
                'QPushButton:hover { background-color: #D32F2F; }'
            )
            btn_cancel.setStyleSheet(
                btn_ss + 'QPushButton { background-color: #546E7A; color: #fff; border: 1px solid #37474F; } '
                'QPushButton:hover { background-color: #607D8B; }'
            )
            for b in (btn_keep, btn_drop, btn_cancel):
                b.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
            btn_keep.clicked.connect(lambda: _pick('keep'))
            btn_drop.clicked.connect(lambda: _pick('drop'))
            btn_cancel.clicked.connect(del_dlg.reject)
            del_lay.addWidget(btn_keep)
            del_lay.addWidget(btn_drop)
            del_lay.addWidget(btn_cancel)
            run_dialog(del_dlg)
            clicked = choice_holder['v']
            if clicked is None:
                return
            if clicked == 'keep':
                for t in arr:
                    if self._task_group(t) == gk:
                        self._set_task_group(t, self.UNGROUPED_KEY)
                order = [g for g in self._scheme_group_order(name) if g != gk]
                if self.UNGROUPED_KEY not in order:
                    order.insert(0, self.UNGROUPED_KEY)
                self._set_scheme_group_order(name, order)
                self._persist_settings()
                _build_tree()
            elif clicked == 'drop':
                self._snap_schemes[name] = [t for t in arr if self._task_group(t) != gk]
                order = [g for g in self._scheme_group_order(name) if g != gk]
                self._set_scheme_group_order(name, order)
                self._persist_settings()
                _build_tree()

        # 单击组节点切换展开/折叠（不影响子任务）
        def _on_item_clicked(item, _col):
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and data[0] == 'group':
                item.setExpanded(not item.isExpanded())

        tree.itemClicked.connect(_on_item_clicked)
        btn_new_grp.clicked.connect(_new_group)
        btn_rename_grp.clicked.connect(_rename_group)
        btn_move_to.clicked.connect(_move_to_group)
        btn_copy_to_scheme.clicked.connect(_copy_to_other_scheme)
        btn_up.clicked.connect(lambda: _on_move(-1))
        btn_down.clicked.connect(lambda: _on_move(1))
        btn_edit.clicked.connect(_edit_selected)
        btn_del.clicked.connect(_delete_selected)
        btn_close.clicked.connect(dlg.reject)
        run_dialog(dlg)
        self._update_scheme_layer_match_label()

    def _task_display_text(self, idx, t):
        tnames = self._names_with_categories(t.get('target_names', []), t.get('target_categories'))
        rnames = self._names_with_categories(t.get('ref_names', []), t.get('ref_categories'))
        if len(tnames) > 36:
            tnames = tnames[:36] + '...'
        if len(rnames) > 36:
            rnames = rnames[:36] + '...'
        rn_disp = rnames if rnames else '-'
        sp = t.get('_snap_special')
        if sp in SPECIAL_KEYS:
            mode_show = special_mode_label(sp)
        else:
            mode_show = spatial_mode_label(t.get('spatial_mode', '')) or '-'
            mp_txt = format_mode_param(t.get('spatial_mode', ''), t.get('mode_param'))
            if mp_txt:
                mode_show = '{0}（{1}）'.format(mode_show, mp_txt)
        return self.tr(
            '{0}. 方法:{1} | 目标:{2} | 参考:{3} | 模式:{4} | 容差:{5} | {6}'
        ).format(
            idx,
            t.get('method_name', t.get('run_name', '')),
            tnames or '-',
            rn_disp,
            mode_show,
            t.get('tolerance', 0.0),
            self.tr('提取已命中') if t.get('snap_enabled', False) else self.tr('提取未命中'),
        )

    def _edit_task_dialog(self, task):
        sp_key = task.get('_snap_special') or ''
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr('编辑子任务'))
        dlg.resize(620, 640)
        lay = QVBoxLayout(dlg)

        grid = QGridLayout()
        grid.addWidget(QLabel(self.tr('方法名称')), 0, 0)
        name_edit = QComboBox()
        name_edit.setEditable(True)
        name_edit.addItem(task.get('method_name', task.get('run_name', '')))
        name_edit.setCurrentText(task.get('method_name', task.get('run_name', '')))
        grid.addWidget(name_edit, 0, 1)
        lbl_tol = QLabel()
        lbl_tol.setWordWrap(True)
        lbl_tol.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        def _crs_for_edit_tol_hint():
            for n in task.get('target_names', []):
                if not n:
                    continue
                found = self.project.mapLayersByName(n)
                if found:
                    c = found[0].crs()
                    if c.isValid():
                        return c
            c = self.project.crs()
            return c if c.isValid() else None

        def _refresh_tol_caption():
            lbl_tol.setText(self._format_edit_task_tolerance_caption(tol.value(), _crs_for_edit_tol_hint()))

        tol = QDoubleSpinBox()
        tol.setDecimals(6)
        tol.setMinimum(0.000001)
        tol.setMaximum(10000.0)
        tol.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        tol.setMinimumWidth(132)
        tol.setValue(float(task.get('tolerance', 0.00001)))
        _refresh_tol_caption()
        tol.valueChanged.connect(lambda _v: _refresh_tol_caption())

        grid.addWidget(lbl_tol, 1, 0)
        grid.addWidget(tol, 1, 1)
        grid.addWidget(QLabel(self.tr('空间模式')), 2, 0)
        sm = QComboBox()
        sm.setEditable(True)
        chk = QCheckBox(self.tr('提取已命中（不勾选=提取未命中）'))
        chk.setChecked(bool(task.get('snap_enabled', True)))
        grid.addWidget(sm, 2, 1)
        grid.addWidget(chk, 3, 0, 1, 2)
        if sp_key == 'overlap_grp':
            chk.setEnabled(False)
            chk.setChecked(True)
            chk.setToolTip(
                self.tr('「重复要素」检测固定输出重复的要素，此项不可用（与主界面一致）。'),
            )
        elif sp_key == 'polygon_inspect':
            chk.setToolTip(
                self.tr(
                    '面检测：勾选＝按各输出项规则输出「命中」侧要素；'
                    '不勾选＝输出对应「未命中」侧（如未参与重叠判定的面等，依所选输出项而定）。',
                )
            )
        elif sp_key == 'line_length':
            chk.setToolTip(
                self.tr('线长度：勾选＝输出满足当前长度规则的线；不勾选＝输出不满足规则的线。'),
            )
        elif sp_key == 'line_ends':
            chk.setEnabled(False)
            chk.setToolTip(self.tr('「标出起点和终点」固定为每条线输出头尾两个点，此项不可用。'))
        elif sp_key == 'line_overlap_pt':
            chk.setEnabled(False)
            chk.setToolTip(
                self.tr('「两线重叠段」固定输出重叠段中心点，此项不可用。端点相接不算重叠。'),
            )
        elif sp_key in ('point_line_count', 'line_point_count', 'poly_point_count', 'poly_line_count'):
            chk.setToolTip(
                self.tr('勾选＝输出个数满足规则的要素；不勾选＝输出个数不满足规则的要素。'),
            )
        elif sp_key == 'point_line_chain':
            chk.setToolTip(
                self.tr('勾选＝链段数≥阈值的点与线段；不勾选＝链段数小于阈值的点与接线。'),
            )
        elif sp_key in SPECIAL_KEYS_NO_SNAP_FILTER:
            chk.setEnabled(False)
            chk.setToolTip(
                self.tr('「{0}」固定输出问题位置点，此项不可用。').format(special_mode_label(sp_key))
            )
        elif sp_key == 'geom_validity':
            chk.setToolTip(self.tr('勾选：输出有问题的要素；不勾选：输出没问题的要素。'))
        elif sp_key == 'poly_area':
            chk.setToolTip(self.tr('勾选：输出面积满足规则的面；不勾选：输出不满足规则的面。'))
        elif sp_key == 'point_near':
            chk.setToolTip(self.tr('勾选：输出过近的点；不勾选：输出周围没有近邻的点。'))
        lay.addLayout(grid)
        snap_mode_row = ModeParamRow()
        if not sp_key:
            snap_mode_row.set_mode(task.get('spatial_mode'), task.get('mode_param'))
            lay.addWidget(snap_mode_row)

        gb_t = QGroupBox(self.tr('判断图层'))
        lt = QVBoxLayout(gb_t)
        lw_t = QListWidget()
        lw_t.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        lw_t.setMinimumHeight(100)
        for n in task.get('target_names', []):
            if n:
                lw_t.addItem(self._layer_name_list_item(n))
        row_mnt = QHBoxLayout()
        le_manual_t = QLineEdit()
        le_manual_t.setPlaceholderText(self.tr('手动输入工程中的图层名称…'))
        btn_name_t = QPushButton(self.tr('按名称添加'))
        row_mnt.addWidget(le_manual_t, 1)
        row_mnt.addWidget(btn_name_t)
        row_at = QHBoxLayout()
        cb_pick_t = QComboBox()
        cb_pick_t.setMinimumWidth(200)
        btn_add_t = QPushButton(self.tr('➕ 从列表添加'))
        btn_del_t = QPushButton(self.tr('➖ 删除选中'))
        row_at.addWidget(cb_pick_t, 1)
        row_at.addWidget(btn_add_t)
        row_at.addWidget(btn_del_t)
        lt.addWidget(lw_t)
        lt.addLayout(row_mnt)
        lt.addLayout(row_at)

        gb_spec = None
        lw_poly_out = None
        poly_atol = None
        edit_line_rule = dict(task.get('_line_length_rule') or {'kind': 'le', 'threshold': 0.0})
        edit_count_rule = dict(task.get('_snap_count_rule') or {'kind': 'le', 'threshold': 0.0})
        lbl_line_rule = None
        overlap_kind_combo = None
        overlap_scope_combo = None
        spin_plc = None
        spin_ol_min = None
        combo_attach = None
        chk_mates = None
        quality_getter = None

        if sp_key == 'polygon_inspect':
            gb_spec = QGroupBox(self.tr('面检测输出与阈值'))
            vpoly = QVBoxLayout(gb_spec)
            lw_poly_out = QListWidget()
            lw_poly_out.setMinimumHeight(160)
            lw_poly_out.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
            POLY_ROWS = (
                (POLYGON_SUB_OVERLAP_HIT, self.tr('重叠：输出参与重叠的面要素')),
                (POLYGON_OUT_OVERLAP_FRAGMENTS, self.tr('重叠：相交面片（可多片独立多边形）')),
                (POLYGON_OUT_OVERLAP_FRAG_CENTER, self.tr('重叠：相交面片的质心点')),
                (POLYGON_SUB_HOLES_LAYER, self.tr('内部孔洞：生成孔洞面图层')),
                (POLYGON_OUT_HOLES_CENTER, self.tr('内部孔洞：中心点图层')),
                (POLYGON_SUB_GAPS_INTERNAL, self.tr('面间隙（斑块之间）')),
                (POLYGON_SUB_GAPS_EDGE, self.tr('外缘留白（制图边界）')),
                (POLYGON_OUT_GAPS_INTERNAL_CENTER, self.tr('斑块间空隙中心点')),
                (POLYGON_OUT_GAPS_EDGE_CENTER, self.tr('外缘留白中心点')),
                (POLYGON_OUT_CENTROID_HIT, self.tr('重叠相关面的质心点（附 CentroidX/Y）')),
                (POLYGON_OUT_CENTROID_ALL, self.tr('全部面的质心（点图层）')),
            )
            want_user = task.get('_polygon_outputs')
            if isinstance(want_user, (list, tuple)) and want_user:
                want_codes = frozenset(expand_polygon_output_codes_for_tasks(want_user))
            else:
                want_codes = None
            default_on = frozenset({
                POLYGON_SUB_OVERLAP_HIT,
                POLYGON_SUB_HOLES_LAYER,
                POLYGON_OUT_HOLES_CENTER,
                POLYGON_SUB_GAPS_INTERNAL,
                POLYGON_OUT_GAPS_INTERNAL_CENTER,
            })
            chk_src = want_codes if want_codes is not None else default_on
            for code, lbl in POLY_ROWS:
                it = QListWidgetItem(lbl)
                it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                it.setData(Qt.ItemDataRole.UserRole, code)
                it.setCheckState(Qt.CheckState.Checked if code in chk_src else Qt.CheckState.Unchecked)
                lw_poly_out.addItem(it)
            vpoly.addWidget(lw_poly_out)
            row_atol = QHBoxLayout()
            row_atol.addWidget(QLabel(self.tr('孔洞/重叠/空隙面积阈值（㎡）')))
            poly_atol = QDoubleSpinBox()
            poly_atol.setDecimals(6)
            poly_atol.setMinimum(0.0)
            poly_atol.setMaximum(1e15)
            poly_atol.setValue(float(task.get('_polygon_area_tol_m2', 1.0)))
            row_atol.addWidget(poly_atol, 1)
            vpoly.addLayout(row_atol)

        elif sp_key == 'line_length':
            gb_spec = QGroupBox(self.tr('线长度规则'))
            vl = QVBoxLayout(gb_spec)
            lbl_line_rule = QLabel()

            def _preview_line_rule(rr):
                r = dict(rr or {})
                k = r.get('kind', 'le')
                if k == 'ge':
                    return self.tr('长度 ≥ {0} m').format(r.get('threshold', 0))
                if k == 'between':
                    return self.tr('长度 ∈ [{0}, {1}] m').format(r.get('t_min', 0), r.get('t_max', 0))
                return self.tr('长度 ≤ {0} m').format(r.get('threshold', 0))

            lbl_line_rule.setText(_preview_line_rule(edit_line_rule))
            btn_lr = QPushButton(self.tr('编辑规则…'))

            def _open_lr_editor():
                d = CdetLineLengthRuleDialog(self, dict(edit_line_rule))
                if run_dialog(d) == QDialog.DialogCode.Accepted:
                    nr = d.result_rule()
                    if nr:
                        edit_line_rule.clear()
                        edit_line_rule.update(nr)
                        lbl_line_rule.setText(_preview_line_rule(edit_line_rule))

            btn_lr.clicked.connect(_open_lr_editor)
            vl.addWidget(lbl_line_rule)
            vl.addWidget(btn_lr)

        elif sp_key in ('point_line_count', 'line_point_count', 'poly_point_count', 'poly_line_count'):
            gb_spec = QGroupBox(self.tr('个数筛选规则'))
            vl = QVBoxLayout(gb_spec)
            lbl_line_rule = QLabel()
            lbl_line_rule.setText(format_snap_count_rule_summary(edit_count_rule))
            btn_cr = QPushButton(self.tr('编辑规则…'))

            def _open_cr_editor():
                d = CdetSnapCountRuleDialog(self, dict(edit_count_rule))
                if run_dialog(d) == QDialog.DialogCode.Accepted:
                    nr = d.result_rule()
                    if nr:
                        edit_count_rule.clear()
                        edit_count_rule.update(nr)
                        lbl_line_rule.setText(format_snap_count_rule_summary(edit_count_rule))

            btn_cr.clicked.connect(_open_cr_editor)
            vl.addWidget(lbl_line_rule)
            vl.addWidget(btn_cr)
            combo_attach = None
            chk_mates = None
            if sp_key in ('point_line_count', 'line_point_count'):
                row_att = QHBoxLayout()
                row_att.addWidget(QLabel(self.tr('挂接位置')))
                combo_attach = QComboBox()
                combo_attach.addItem(self.tr('端点（默认）'), 'endpoint')
                combo_attach.addItem(self.tr('任意折点'), 'vertex')
                combo_attach.addItem(self.tr('沿线身'), 'along')
                aix = combo_attach.findData(normalize_count_attach(task.get('_count_attach')))
                combo_attach.setCurrentIndex(aix if aix >= 0 else 0)
                row_att.addWidget(combo_attach, 1)
                vl.addLayout(row_att)
                chk_mates = QCheckBox(self.tr('同时输出对端要素'))
                chk_mates.setChecked(bool(task.get('_count_output_mates')))
                vl.addWidget(chk_mates)

        elif sp_key == 'overlap_grp':
            gb_spec = QGroupBox(self.tr('组内重叠'))
            vo = QVBoxLayout(gb_spec)
            overlap_kind_combo = QComboBox()
            overlap_kind_combo.addItem(self.tr('自动（混合点/线/面分型）'), 'auto')
            overlap_kind_combo.addItem(self.tr('面（顶点一致·吸附容差）'), 'polygon')
            overlap_kind_combo.addItem(self.tr('点重合（欧式距离阈值）'), 'point')
            overlap_kind_combo.addItem(self.tr('线（顶点一致·吸附容差）'), 'line')
            ok_cur = str(task.get('_overlap_kind') or 'auto').strip()
            if ok_cur not in ('auto', 'point', 'line', 'polygon'):
                ok_cur = 'polygon'
            ik = overlap_kind_combo.findData(ok_cur)
            overlap_kind_combo.setCurrentIndex(max(ik, 0))
            overlap_scope_combo = QComboBox()
            overlap_scope_combo.addItem(self.tr('单独判断 + 单独输出'), 'per_layer')
            overlap_scope_combo.addItem(self.tr('单独判断 + 集合输出'), 'merged_concat')
            overlap_scope_combo.addItem(self.tr('集合判断 + 单独输出'), 'group_per_layer')
            overlap_scope_combo.addItem(self.tr('集合判断 + 集合输出'), 'merged_group')
            isc = overlap_scope_combo.findData(
                normalize_overlap_scope((task.get('_overlap_scope') or 'per_layer').strip())
            )
            overlap_scope_combo.setCurrentIndex(max(isc, 0))
            vo.addWidget(QLabel(self.tr('判定几何类型')))
            vo.addWidget(overlap_kind_combo)
            vo.addWidget(QLabel(self.tr('输出范围')))
            vo.addWidget(overlap_scope_combo)

        elif sp_key == 'point_line_chain':
            gb_spec = QGroupBox(special_mode_label('point_line_chain'))
            plc_lay = QVBoxLayout(gb_spec)
            row_pc = QHBoxLayout()
            row_pc.addWidget(QLabel(self.tr('最小段数阈值（≥）')))
            spin_plc = QSpinBox()
            spin_plc.setRange(1, 100000)
            spin_plc.setValue(int(task.get('_point_line_chain_min_seg', 3)))
            row_pc.addWidget(spin_plc)
            row_pc.addStretch(1)
            plc_lay.addLayout(row_pc)
            plc_lay.addWidget(
                QLabel(self.tr('仅「≥」规则；勾选提取已命中输出链段数达阈值的点与线段。')),
            )

        elif sp_key == 'line_overlap_pt':
            gb_spec = QGroupBox(self.tr('线重叠中心'))
            ol_lay = QHBoxLayout(gb_spec)
            ol_lay.addWidget(QLabel(self.tr('最短重叠（米）')))
            spin_ol_min = QDoubleSpinBox()
            spin_ol_min.setRange(0.0, 1e7)
            spin_ol_min.setDecimals(2)
            spin_ol_min.setValue(float(task.get('_line_overlap_min_length', 1.0) or 1.0))
            ol_lay.addWidget(spin_ol_min)
            ol_lay.addStretch(1)

        elif sp_key in QUALITY_KEYS:
            w_q, quality_getter = build_special_param_form(sp_key, task)
            if w_q is not None:
                gb_spec = QGroupBox(special_mode_label(sp_key))
                vq = QVBoxLayout(gb_spec)
                vq.addWidget(w_q)

        gb_r = QGroupBox(self.tr('参考图层'))
        lr = QVBoxLayout(gb_r)
        if sp_key in SPECIAL_KEYS_NO_REF:
            lr.addWidget(QLabel(self.tr('此类特殊检测不要求参考图层，可保持为空。')))
        elif sp_key == 'point_line_count':
            lr.addWidget(QLabel(self.tr('须指定参考线图层（可多选）；判断图层须为点图层。')))
        elif sp_key == 'line_point_count':
            lr.addWidget(QLabel(self.tr('须指定参考点图层（可多选）；判断图层须为线图层。')))
        elif sp_key == 'poly_point_count':
            lr.addWidget(QLabel(self.tr('须指定参考点图层（可多选）；判断图层须为面图层。')))
        elif sp_key == 'poly_line_count':
            lr.addWidget(QLabel(self.tr('须指定参考线图层（可多选）；判断图层须为面图层。')))
        elif sp_key == 'point_line_chain':
            lr.addWidget(QLabel(self.tr('须指定参考线图层（可多选）；判断图层须为点图层。')))
        lw_r = QListWidget()
        lw_r.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        lw_r.setMinimumHeight(100)
        for n in task.get('ref_names', []):
            if n:
                lw_r.addItem(self._layer_name_list_item(n))
        row_mnr = QHBoxLayout()
        le_manual_r = QLineEdit()
        le_manual_r.setPlaceholderText(self.tr('手动输入工程中的图层名称…'))
        btn_name_r = QPushButton(self.tr('按名称添加'))
        row_mnr.addWidget(le_manual_r, 1)
        row_mnr.addWidget(btn_name_r)
        row_ar = QHBoxLayout()
        cb_pick_r = QComboBox()
        cb_pick_r.setMinimumWidth(200)
        btn_add_r = QPushButton(self.tr('➕ 从列表添加'))
        btn_del_r = QPushButton(self.tr('➖ 删除选中'))
        row_ar.addWidget(cb_pick_r, 1)
        row_ar.addWidget(btn_add_r)
        row_ar.addWidget(btn_del_r)
        lr.addWidget(lw_r)
        lr.addLayout(row_mnr)
        lr.addLayout(row_ar)
        if sp_key in SPECIAL_KEYS_NO_REF:
            lw_r.setEnabled(False)
            le_manual_r.setEnabled(False)
            btn_name_r.setEnabled(False)
            cb_pick_r.setEnabled(False)
            btn_add_r.setEnabled(False)
            btn_del_r.setEnabled(False)

        lay.addWidget(gb_t)
        if gb_spec is not None:
            lay.addWidget(gb_spec)
        lay.addWidget(gb_r)

        def _fill_vector_combo(combo):
            combo.clear()
            names = sorted(
                {
                    lyr.name()
                    for lyr in self.project.mapLayers().values()
                    if isinstance(lyr, QgsVectorLayer)
                },
                key=lambda x: x.lower(),
            )
            for n in names:
                combo.addItem(n)

        def _list_names(lw):
            return [lw.item(i).text() for i in range(lw.count())]

        def refresh_sm():
            preserve = sm.currentData()
            if preserve is None:
                preserve = task.get('spatial_mode')
            sm.blockSignals(True)
            sm.clear()
            sm.setEditable(True)
            ok_any = False
            if sp_key in SPECIAL_KEYS:
                sm.addItem(self.tr('特殊检测：{0}').format(special_mode_label(sp_key)), '__special__')
                sm.setItemData(0, special_mode_tip(sp_key), Qt.ItemDataRole.ToolTipRole)
                sm.setToolTip(special_mode_tip(sp_key))
                idx = sm.findData(preserve if preserve else '__special__')
                if idx < 0 and preserve:
                    sm.addItem(str(preserve), preserve)
                    idx = sm.findData(preserve)
                if idx >= 0:
                    sm.setCurrentIndex(idx)
                elif sm.count():
                    sm.setCurrentIndex(0)
                sm.blockSignals(False)
                return
            t_layers, _ = self._resolve_layers_by_names(_list_names(lw_t))
            r_layers, _ = self._resolve_layers_by_names(_list_names(lw_r))
            if t_layers and r_layers:
                for entry in spatial_mode_choices(t_layers[0], r_layers[0]):
                    sm.addItem(entry[1], entry[0])
                    sm.setItemData(sm.count() - 1, entry[2], Qt.ItemDataRole.ToolTipRole)
                    ok_any = True
            idx = sm.findData(preserve)
            if idx >= 0:
                sm.setCurrentIndex(idx)
            elif preserve and not ok_any:
                sm.addItem(spatial_mode_label(preserve), preserve)
                sm.setCurrentIndex(0)
            elif sm.count():
                sm.setCurrentIndex(0)
            sm.blockSignals(False)
            if not sp_key:
                snap_mode_row.set_mode(sm.currentData(), snap_mode_row.value() if sm.currentData() == snap_mode_row._code else task.get('mode_param'))

        def add_to_list(lw, combo):
            name = (combo.currentText() or '').strip()
            if not name:
                return
            for i in range(lw.count()):
                if lw.item(i).text() == name:
                    return
            lw.addItem(self._layer_name_list_item(name))
            refresh_sm()

        def add_name_to_list(lw, line_edit):
            name = (line_edit.text() or '').strip()
            if not name:
                return
            for i in range(lw.count()):
                if lw.item(i).text() == name:
                    return
            lw.addItem(self._layer_name_list_item(name))
            line_edit.clear()
            refresh_sm()

        def remove_selected(lw):
            rows = sorted({lw.row(it) for it in lw.selectedItems()}, reverse=True)
            for r in rows:
                lw.takeItem(r)
            refresh_sm()

        _fill_vector_combo(cb_pick_t)
        _fill_vector_combo(cb_pick_r)
        btn_name_t.clicked.connect(lambda: add_name_to_list(lw_t, le_manual_t))
        btn_name_r.clicked.connect(lambda: add_name_to_list(lw_r, le_manual_r))
        le_manual_t.returnPressed.connect(lambda: add_name_to_list(lw_t, le_manual_t))
        le_manual_r.returnPressed.connect(lambda: add_name_to_list(lw_r, le_manual_r))
        btn_add_t.clicked.connect(lambda: add_to_list(lw_t, cb_pick_t))
        btn_add_r.clicked.connect(lambda: add_to_list(lw_r, cb_pick_r))
        btn_del_t.clicked.connect(lambda: remove_selected(lw_t))
        btn_del_r.clicked.connect(lambda: remove_selected(lw_r))

        refresh_sm()

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        localize_button_box(bb)
        lay.addWidget(bb)

        def _polygon_codes_editor():
            codes = []
            if lw_poly_out is None:
                return codes
            for row in range(lw_poly_out.count()):
                it = lw_poly_out.item(row)
                if it.checkState() == Qt.CheckState.Checked:
                    c = it.data(Qt.ItemDataRole.UserRole)
                    if c:
                        codes.append(c)
            return codes

        def _try_accept():
            if lw_t.count() == 0:
                QMessageBox.warning(self, self.tr('提示'), self.tr('请至少保留一个判断图层。'))
                return
            requires_ref = sp_key not in SPECIAL_KEYS_NO_REF
            if requires_ref and lw_r.count() == 0:
                QMessageBox.warning(
                    self,
                    self.tr('提示'),
                    self.tr('标准子任务需至少选择一个参考图层。'),
                )
                return
            if sp_key == 'polygon_inspect' and not _polygon_codes_editor():
                QMessageBox.warning(
                    self,
                    self.tr('提示'),
                    self.tr('面检测：请勾选至少一类输出项。'),
                )
                return
            dlg.accept()

        bb.accepted.connect(_try_accept)
        bb.rejected.connect(dlg.reject)
        if run_dialog(dlg) != QDialog.DialogCode.Accepted:
            return None
        out = dict(task)
        out.update({
            'method_name': (name_edit.currentText() or '').strip() or task.get('method_name', task.get('run_name', '')),
            'run_name': (name_edit.currentText() or '').strip() or task.get('run_name', ''),
            'target_names': _list_names(lw_t),
            'ref_names': _list_names(lw_r),
            'spatial_mode': sm.currentData() if sm.currentData() is not None else sm.currentText(),
            'tolerance': float(tol.value()),
            'snap_enabled': bool(chk.isChecked()),
        })
        kept_t = self._trim_category_map(task.get('target_categories'), out.get('target_names'))
        kept_r = self._trim_category_map(task.get('ref_categories'), out.get('ref_names'))
        if kept_t:
            out['target_categories'] = kept_t
        else:
            out.pop('target_categories', None)
        if kept_r:
            out['ref_categories'] = kept_r
        else:
            out.pop('ref_categories', None)
        if sp_key == 'polygon_inspect' and lw_poly_out is not None:
            out['_polygon_outputs'] = _polygon_codes_editor()
            out['_polygon_area_tol_m2'] = float(poly_atol.value())
            out['_polygon_overlap_area_tol_m2'] = float(poly_atol.value())
        elif sp_key == 'line_length':
            out['_line_length_rule'] = dict(edit_line_rule)
        elif sp_key in ('point_line_count', 'line_point_count', 'poly_point_count', 'poly_line_count'):
            out['_snap_count_rule'] = dict(edit_count_rule)
            if sp_key in ('point_line_count', 'line_point_count'):
                if combo_attach is not None:
                    out['_count_attach'] = normalize_count_attach(combo_attach.currentData())
                if chk_mates is not None:
                    out['_count_output_mates'] = bool(chk_mates.isChecked())
        elif sp_key == 'overlap_grp' and overlap_kind_combo is not None:
            out['_overlap_kind'] = overlap_kind_combo.currentData() or 'auto'
            out['_overlap_scope'] = normalize_overlap_scope(overlap_scope_combo.currentData())
        elif sp_key == 'point_line_chain' and spin_plc is not None:
            out['_point_line_chain_min_seg'] = int(spin_plc.value())
        elif sp_key == 'line_overlap_pt' and spin_ol_min is not None:
            out['_line_overlap_min_length'] = float(spin_ol_min.value())
        elif sp_key in QUALITY_KEYS and quality_getter is not None:
            out.update(normalize_special_values(quality_getter()))
        if not sp_key:
            mp = snap_mode_row.value()
            if mp is not None:
                out['mode_param'] = mp
            else:
                out.pop('mode_param', None)
        if sp_key == 'overlap_grp':
            out['snap_enabled'] = True
        return out

    def _persist_settings(self):
        settings_set(self.settings, 'snap_enabled', self.chk_snap.isChecked())
        if getattr(self, '_ui_mode', None) == 'move':
            settings_set(self.settings, 'move_tolerance', self.spin_tolerance.value())
        else:
            settings_set(self.settings, 'tolerance', self.spin_tolerance.value())
        settings_set(self.settings, 'snap_batch_continue', self.chk_batch_continue.isChecked())
        ssp = self.combo_snap_spatial_mode.currentData()
        if ssp is not None:
            settings_set(self.settings, 'snap_spatial', ssp)
        rm_save = self._effective_snap_ref_mode()
        settings_set(self.settings, 'snap_ref_mode', rm_save or 'standard')
        settings_set(self.settings, 'point_line_chain_min_seg', int(self.spin_chain_min_seg.value()))
        settings_set(self.settings, 'line_overlap_min_m', float(self.spin_line_overlap_min.value()))
        settings_set(self.settings, 'poly_area_tol_m2', float(self.spin_overlap_area_tol.value()))
        try:
            settings_set(self.settings, 'polygon_outputs_json',
                json.dumps(self._polygon_outputs_selected(), ensure_ascii=False),
            )
        except Exception:  # nosec B110
            pass
        settings_set(self.settings, 'overlap_scope',
            normalize_overlap_scope(self.combo_overlap_scope.currentData()),
        )
        try:
            settings_set(self.settings, 'line_length_rule_json',
                json.dumps(self._line_length_rule, ensure_ascii=False),
            )
        except Exception:  # nosec B110
            pass
        try:
            settings_set(self.settings, 'snap_count_rule_json',
                json.dumps(self._snap_count_rule, ensure_ascii=False),
            )
        except Exception:  # nosec B110
            pass
        settings_set(self.settings, 'count_attach', normalize_count_attach(self._count_attach))
        settings_set(self.settings, 'count_output_mates', bool(self._count_output_mates))
        try:
            settings_set(self.settings, 'mode_params_json',
                json.dumps(self._mode_params, ensure_ascii=False),
            )
        except Exception:
            settings_set(self.settings, 'mode_params_json', '{}')
        try:
            settings_set(self.settings, 'special_values_json',
                json.dumps(normalize_special_values(self._special_values), ensure_ascii=False),
            )
        except Exception:
            settings_set(self.settings, 'special_values_json', '{}')
        settings_set(self.settings, 'snap_scheme_current', self._active_snap_scheme)
        try:
            settings_set(self.settings, 'snap_schemes_json', json.dumps(self._snap_schemes, ensure_ascii=False))
        except Exception:
            settings_set(self.settings, 'snap_schemes_json', '{}')
        try:
            settings_set(self.settings, 'snap_group_orders_json',
                json.dumps(self._snap_group_orders, ensure_ascii=False),
            )
        except Exception:
            settings_set(self.settings, 'snap_group_orders_json', '{}')
        self._stash_mode_tolerance()
        settings_set(self.settings, 'ui_mode', self._ui_mode)
        if self._shared_sf_tol is not None:
            settings_set(self.settings, 'tolerance', float(self._shared_sf_tol))
        if self._move_tol is not None:
            settings_set(self.settings, 'move_tolerance', float(self._move_tol))
        settings_set(self.settings, 'field_grp_target', self._field_group_path_target or '')
        settings_set(self.settings, 'field_grp_ref', self._field_group_path_ref or '')
        settings_set(self.settings, 'field_geom_target', self._geom_storage_key(self._field_target_geom))
        settings_set(self.settings, 'field_geom_ref', self._geom_storage_key(self._field_ref_geom))
        nf = self.combo_named_field.currentData()
        if nf is not None:
            settings_set(self.settings, 'f_named_field', nf)
        rd = self.combo_ref_field.currentData()
        if rd == LAYER_NAME_VALUE:
            settings_set(self.settings, 'f_ref_source', LAYER_TITLE_NEW)
        elif rd == REF_ELEMENT_COUNT:
            settings_set(self.settings, 'f_ref_source', ELEMENT_COUNT_NEW)
            try:
                settings_set(self.settings, 'f_count_rule_json', json.dumps(self._count_rule, ensure_ascii=False))
            except Exception:
                settings_set(self.settings, 'f_count_rule_json', '')
        elif rd is not None:
            settings_set(self.settings, 'f_ref_source', rd)
        sp = self.combo_spatial_mode.currentData()
        if sp is not None:
            settings_set(self.settings, 'f_spatial', sp)
        mm = self.combo_multi_match.currentData()
        if mm is not None:
            settings_set(self.settings, 'f_multi', mm)
        fo = self.combo_field_output.currentData()
        if fo is not None:
            settings_set(self.settings, 'field_output_mode', fo)
        self._harvest_list_categories(self.target_layer_list, 'target' if self._ui_mode == 'snap' else 'target')
        self._harvest_list_categories(self.ref_layer_list, 'ref')
        settings_set(self.settings, 'field_scheme_current', self._active_field_scheme)
        try:
            settings_set(self.settings, 'field_schemes_json',
                json.dumps(self._field_schemes, ensure_ascii=False),
            )
        except Exception:
            settings_set(self.settings, 'field_schemes_json', '{}')
        settings_set(self.settings, 'move_scheme_current', self._active_move_scheme)
        if hasattr(self, 'chk_move_batch_continue'):
            self._move_batch_continue = bool(self.chk_move_batch_continue.isChecked())
        settings_set(self.settings, 'move_batch_continue', bool(self._move_batch_continue))
        if hasattr(self, 'combo_move_mode'):
            mm = self.combo_move_mode.currentData() or getattr(self, '_invalid_move_mode', None)
            if mm:
                settings_set(self.settings, 'move_mode', mm)
        try:
            settings_set(self.settings, 'move_schemes_json',
                json.dumps(self._move_schemes, ensure_ascii=False),
            )
        except Exception:
            settings_set(self.settings, 'move_schemes_json', '{}')
        for key, store in (
            ('cat_snap_target_json', self._cat_snap.get('target')),
            ('cat_snap_ref_json', self._cat_snap.get('ref')),
            ('cat_field_target_json', self._cat_field.get('target')),
            ('cat_field_ref_json', self._cat_field.get('ref')),
            ('cat_move_target_json', self._cat_move.get('target')),
            ('cat_move_ref_json', self._cat_move.get('ref')),
        ):
            try:
                settings_set(self.settings, key, json.dumps(store or {}, ensure_ascii=False))
            except Exception:
                settings_set(self.settings, key, '{}')
        for attr, skey in (
            ('combo_head_ref', 'f_head_ref'),
            ('combo_head_named', 'f_head_named'),
            ('combo_tail_ref', 'f_tail_ref'),
            ('combo_tail_named', 'f_tail_named'),
        ):
            combo = getattr(self, attr, None)
            if combo is None:
                continue
            val = combo.currentData()
            settings_set(self.settings, skey, val or '')

    def load_settings(self):
        self.chk_snap.setChecked(settings_value(self.settings, 'snap_enabled', False, type=bool))
        self.spin_tolerance.setValue(settings_value(self.settings, 'tolerance', 0.00001, type=float))
        self.chk_batch_continue.setChecked(settings_value(self.settings, 'snap_batch_continue', True, type=bool))
        self._update_meter_hint()
        fo = settings_value(self.settings, 'field_output_mode', 'direct', type=str)
        fidx = self.combo_field_output.findData(fo)
        if fidx >= 0:
            self.combo_field_output.setCurrentIndex(fidx)
        self._field_group_path_target = settings_value(self.settings, 'field_grp_target', '', type=str) or ''
        self._field_group_path_ref = settings_value(self.settings, 'field_grp_ref', '', type=str) or ''
        self._field_target_geom = self._geom_from_storage_key(
            settings_value(self.settings, 'field_geom_target', 'all', type=str))
        self._field_ref_geom = self._geom_from_storage_key(
            settings_value(self.settings, 'field_geom_ref', 'all', type=str))
        mode = settings_value(self.settings, 'ui_mode', 'snap', type=str)
        rn = settings_value(self.settings, 'f_named_field', '', type=str)
        rr = settings_value(self.settings, 'f_ref_source', '', type=str)
        rs = settings_value(self.settings, 'f_spatial', '', type=str)
        rm = settings_value(self.settings, 'f_multi', '', type=str)
        ssp = settings_value(self.settings, 'snap_spatial', '', type=str)
        ssc = settings_value(self.settings, 'snap_scheme_current', self.SNAP_SCHEME_CUSTOM, type=str)
        ssj = settings_value(self.settings, 'snap_schemes_json', '{}', type=str)
        try:
            raw = json.loads(ssj) if ssj else {}
            self._snap_schemes = raw if isinstance(raw, dict) else {}
        except Exception:
            self._snap_schemes = {}
        sgj = settings_value(self.settings, 'snap_group_orders_json', '{}', type=str)
        try:
            raw_g = json.loads(sgj) if sgj else {}
            if isinstance(raw_g, dict):
                clean = {}
                for k, v in raw_g.items():
                    if isinstance(v, list):
                        clean[k] = [str(x) for x in v]
                self._snap_group_orders = clean
            else:
                self._snap_group_orders = {}
        except Exception:
            self._snap_group_orders = {}
        for sname in list(self._snap_schemes.keys()):
            self._ensure_group_in_order(sname, self.UNGROUPED_KEY)
        self.spin_overlap_area_tol.setValue(
            settings_value(self.settings, 'poly_area_tol_m2', 1.0, type=float)
        )
        llj_snap = settings_value(self.settings, 'line_length_rule_json', '', type=str)
        if llj_snap:
            try:
                self._line_length_rule = json.loads(llj_snap)
            except Exception:
                self._line_length_rule = {'kind': 'le', 'threshold': 0.0}
        scj = settings_value(self.settings, 'snap_count_rule_json', '', type=str)
        if scj:
            try:
                self._snap_count_rule = json.loads(scj)
            except Exception:
                self._snap_count_rule = {'kind': 'le', 'threshold': 0.0}
        self._count_attach = normalize_count_attach(
            settings_value(self.settings, 'count_attach', 'endpoint', type=str)
        )
        self._count_output_mates = bool(settings_value(self.settings, 'count_output_mates', False, type=bool))
        try:
            raw_mp = json.loads(settings_value(self.settings, 'mode_params_json', '{}', type=str) or '{}')
            self._mode_params = raw_mp if isinstance(raw_mp, dict) else {}
        except Exception:
            self._mode_params = {}
        try:
            raw_sv = json.loads(settings_value(self.settings, 'special_values_json', '{}', type=str) or '{}')
            self._special_values = normalize_special_values(raw_sv if isinstance(raw_sv, dict) else {})
        except Exception:
            self._special_values = special_defaults()
        self._special_form_key = None
        self._sync_count_attach_widgets()
        self._active_snap_scheme = ssc or self.SNAP_SCHEME_CUSTOM
        self._refresh_snap_scheme_combo()
        self._restore_snap_spatial = ssp or None
        self._restore_snap_ref_mode = settings_value(self.settings, 'snap_ref_mode', '', type=str)
        self.spin_chain_min_seg.setValue(settings_value(self.settings, 'point_line_chain_min_seg', 3, type=int))
        self.spin_line_overlap_min.setValue(
            float(settings_value(self.settings, 'line_overlap_min_m', 1.0, type=float))
        )
        poj = settings_value(self.settings, 'polygon_outputs_json', '', type=str)
        self._pending_polygon_outputs = None
        if poj:
            try:
                self._pending_polygon_outputs = json.loads(poj)
                if not isinstance(self._pending_polygon_outputs, list):
                    self._pending_polygon_outputs = None
            except Exception:
                self._pending_polygon_outputs = None
        if self._pending_polygon_outputs is None:
            leg_ps = settings_value(self.settings, 'poly_submode', '', type=str)
            if leg_ps:
                self._pending_polygon_outputs = [leg_ps]
        osc = normalize_overlap_scope(settings_value(self.settings, 'overlap_scope', 'per_layer', type=str))
        if osc:
            ios = self.combo_overlap_scope.findData(osc)
            if ios >= 0:
                self.combo_overlap_scope.setCurrentIndex(ios)
        self._restore_field_named = rn or None
        if is_layer_title_token(rr):
            self._restore_field_ref = LAYER_NAME_VALUE
        elif is_element_count_token(rr):
            self._restore_field_ref = REF_ELEMENT_COUNT
        else:
            self._restore_field_ref = rr or None
        crj = settings_value(self.settings, 'f_count_rule_json', '', type=str)
        if crj:
            try:
                self._count_rule = json.loads(crj)
            except Exception:
                self._count_rule = default_element_count_rule()
        else:
            self._count_rule = default_element_count_rule()
        self._restore_field_spatial = rs or None
        self._restore_field_multi = rm or None
        self._restore_end_head_ref = settings_value(self.settings, 'f_head_ref', '', type=str) or None
        self._restore_end_head_named = settings_value(self.settings, 'f_head_named', '', type=str) or None
        self._restore_end_tail_ref = settings_value(self.settings, 'f_tail_ref', '', type=str) or None
        self._restore_end_tail_named = settings_value(self.settings, 'f_tail_named', '', type=str) or None
        fsj = settings_value(self.settings, 'field_schemes_json', '{}', type=str)
        try:
            raw_f = json.loads(fsj) if fsj else {}
            self._field_schemes = self._normalize_field_schemes(raw_f)
        except Exception:
            self._field_schemes = {}
        self._active_field_scheme = settings_value(self.settings, 'field_scheme_current', self.FIELD_SCHEME_CUSTOM, type=str
        ) or self.FIELD_SCHEME_CUSTOM
        msj = settings_value(self.settings, 'move_schemes_json', '{}', type=str)
        try:
            raw_m = json.loads(msj) if msj else {}
            self._move_schemes = self._normalize_move_schemes(raw_m)
        except Exception:
            self._move_schemes = {}
        self._active_move_scheme = settings_value(self.settings, 'move_scheme_current', self.MOVE_SCHEME_CUSTOM, type=str
        ) or self.MOVE_SCHEME_CUSTOM
        self._move_batch_continue = settings_value(self.settings, 'move_batch_continue', True, type=bool)
        if hasattr(self, 'chk_move_batch_continue'):
            self.chk_move_batch_continue.setChecked(bool(self._move_batch_continue))
        self._restore_move_mode = settings_value(self.settings, 'move_mode', 'standard', type=str) or 'standard'
        self._cat_snap = {
            'target': self._load_cat_json('cat_snap_target_json'),
            'ref': self._load_cat_json('cat_snap_ref_json'),
        }
        self._cat_field = {
            'target': self._load_cat_json('cat_field_target_json'),
            'ref': self._load_cat_json('cat_field_ref_json'),
        }
        self._refresh_field_scheme_combo()
        self._refresh_move_scheme_combo()
        # 预载各模式容差，供 _apply_ui_mode 切换时写入 spin
        self._shared_sf_tol = float(settings_value(self.settings, 'tolerance', 0.00001, type=float))
        self._move_tol = float(settings_value(self.settings, 'move_tolerance', self._shared_sf_tol, type=float))
        self._cat_move = {
            'target': self._load_cat_json('cat_move_target_json'),
            'ref': self._load_cat_json('cat_move_ref_json'),
        }
        if mode == 'field':
            self._apply_ui_mode('field')
        elif mode == 'move':
            self._apply_ui_mode('move')
        else:
            self._apply_ui_mode('snap')
        self._update_tolerance_display()
        ppend = getattr(self, '_pending_polygon_outputs', None)
        if isinstance(ppend, list) and ppend:
            self._set_polygon_checks_from_codes(ppend)
        self._pending_polygon_outputs = None
        self._update_line_rule_label()
        self._special_form_key = None
        self._refresh_snap_special_extra_visibility()
        self._sync_mode_param_widgets()

    def _ref_count_combo_display_text(self):
        return self.tr('元素数量 | {0}').format(format_element_count_rule_summary(self._count_rule))

    def _update_multi_match_for_ref_source(self):
        rs = self.combo_ref_field.currentData()
        en = rs == REF_ELEMENT_COUNT
        self.combo_multi_match.setEnabled(not en)
        if en:
            self.combo_multi_match.setToolTip(
                self.tr(
                    '元素数量：仅统计满足当前「空间命名模式」与容差的参考要素（多层相加）。'
                    '此处为单值结果，多匹配策略不适用。'))
        else:
            self.combo_multi_match.setToolTip(self._multi_match_tip_text())

    def _on_ref_field_index_changed(self, idx):
        if idx < 0:
            return
        d = self.combo_ref_field.itemData(idx)
        if d != REF_ELEMENT_COUNT:
            self._last_non_count_ref_index = idx
        if self._ui_mode == 'field':
            self._update_multi_match_for_ref_source()

    def _on_ref_field_activated(self, index):
        if getattr(self, '_ref_combo_populating', False):
            return
        if index < 0:
            return
        if self.combo_ref_field.itemData(index) != REF_ELEMENT_COUNT:
            return
        if not self._show_count_rule_dialog():
            self.combo_ref_field.blockSignals(True)
            self.combo_ref_field.setCurrentIndex(self._last_non_count_ref_index)
            self.combo_ref_field.blockSignals(False)
            return
        self.combo_ref_field.setItemText(index, self._ref_count_combo_display_text())
        self._persist_settings()

    def _show_count_rule_dialog(self):
        dlg = CdetCountRuleDialog(self, self._count_rule)
        if run_dialog(dlg) != QDialog.DialogCode.Accepted:
            return False
        rule = dlg.result_rule()
        if not rule:
            return False
        self._count_rule = rule
        return True

    def _run_field_naming(self):
        named_layers = self._get_selected_layers(self.target_layer_list)
        ref_layers = self._get_selected_layers(self.ref_layer_list)
        nf = self.combo_named_field.currentData()
        rs = self.combo_ref_field.currentData()
        sm = self.combo_spatial_mode.currentData()
        mm = self.combo_multi_match.currentData()
        if sm != LP_END_FIELDS:
            if not nf or not rs or not sm:
                QMessageBox.warning(self, self.tr('提示'), self.tr('请完整选择字段与模式'))
                return
            if rs != REF_ELEMENT_COUNT and not mm:
                QMessageBox.warning(self, self.tr('提示'), self.tr('请完整选择字段与模式'))
                return
        elif not sm:
            QMessageBox.warning(self, self.tr('提示'), self.tr('请完整选择字段与模式'))
            return
        if rs == REF_ELEMENT_COUNT:
            mm = 'first'
        if not mm:
            mm = 'nearest'
        params = {
            'named_field': nf,
            'ref_value_source': rs,
            'spatial_mode': sm,
            'multi_strategy': mm,
            'tolerance': self.spin_tolerance.value(),
            'field_output_mode': self.combo_field_output.currentData() or 'direct',
            'element_count_rule': dict(self._count_rule) if rs == REF_ELEMENT_COUNT else None,
            'end_head_ref': self.combo_head_ref.currentData() or '',
            'end_head_named': self.combo_head_named.currentData() or '',
            'end_tail_ref': self.combo_tail_ref.currentData() or '',
            'end_tail_named': self.combo_tail_named.currentData() or '',
            'mode_param': self._current_mode_param(sm),
            '_category_target': self._filters_for_list(self.target_layer_list, named_layers),
            '_category_ref': self._filters_for_list(self.ref_layer_list, ref_layers),
        }
        run_field_naming(self.iface, self.project, named_layers, ref_layers, params)

    def _layers_from_names(self, names):
        layers = []
        missing = []
        for name in names or []:
            found = self.project.mapLayersByName(name)
            if found:
                layers.append(found[0])
            elif name:
                missing.append(name)
        return layers, missing

    def _field_task_run_params(self, task, named_layers, ref_layers):
        ref = task.get('ref_value_source') or ''
        if is_layer_title_token(ref):
            ref = LAYER_NAME_VALUE
        elif is_element_count_token(ref):
            ref = REF_ELEMENT_COUNT
        return {
            'named_field': task.get('named_field') or '',
            'ref_value_source': ref,
            'spatial_mode': task.get('spatial_mode') or '',
            'multi_strategy': task.get('multi_strategy') or 'nearest',
            'tolerance': float(task.get('tolerance') or 0.00001),
            'field_output_mode': task.get('field_output_mode') or 'direct',
            'element_count_rule': task.get('element_count_rule') or dict(self._count_rule),
            'end_head_ref': task.get('end_head_ref') or '',
            'end_head_named': task.get('end_head_named') or '',
            'end_tail_ref': task.get('end_tail_ref') or '',
            'end_tail_named': task.get('end_tail_named') or '',
            '_category_target': filters_by_layer_id(named_layers, task.get('target_categories')),
            '_category_ref': filters_by_layer_id(ref_layers, task.get('ref_categories')),
            'mode_param': task.get('mode_param'),
            '_quiet': True,
        }

    def _pick_field_tasks_dialog(self, scheme_name, tasks):
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr('选择批量子任务'))
        dlg.setMinimumSize(480, 360)
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel(
            self.tr('方案「{0}」— 勾选要执行的子方法（本次运行有效，不保存）').format(scheme_name)
        ))
        lw = QListWidget()
        for i, task in enumerate(tasks):
            it = QListWidgetItem(task.get('method_name') or task.get('run_name') or self.tr('子任务'))
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            it.setCheckState(Qt.CheckState.Checked)
            it.setData(Qt.ItemDataRole.UserRole, i)
            lw.addItem(it)
        layout.addWidget(lw, 1)
        row = QHBoxLayout()
        btn_all = QPushButton(self.tr('全选'))
        btn_none = QPushButton(self.tr('全不选'))
        btn_ok = QPushButton(self.tr('确定'))
        btn_cancel = QPushButton(self.tr('取消'))
        row.addWidget(btn_all)
        row.addWidget(btn_none)
        row.addStretch(1)
        row.addWidget(btn_ok)
        row.addWidget(btn_cancel)
        layout.addLayout(row)

        def _set_all(state):
            for i in range(lw.count()):
                lw.item(i).setCheckState(state)

        btn_all.clicked.connect(lambda: _set_all(Qt.CheckState.Checked))
        btn_none.clicked.connect(lambda: _set_all(Qt.CheckState.Unchecked))
        btn_ok.clicked.connect(dlg.accept)
        btn_cancel.clicked.connect(dlg.reject)
        if run_dialog(dlg) != QDialog.DialogCode.Accepted:
            return None
        picked = []
        for i in range(lw.count()):
            it = lw.item(i)
            if it.checkState() == Qt.CheckState.Checked:
                picked.append(tasks[it.data(Qt.ItemDataRole.UserRole)])
        return picked

    def _run_field_scheme_batch(self, scheme_name):
        tasks = list(self._field_schemes.get(scheme_name) or [])
        if not tasks:
            QMessageBox.information(self, self.tr('提示'), self.tr('该方案还没有子任务。'))
            return
        picked = self._pick_field_tasks_dialog(scheme_name, tasks)
        if picked is None:
            return
        if not picked:
            QMessageBox.information(self, self.tr('提示'), self.tr('请至少勾选一条子任务。'))
            return
        lines = []
        ok_n = 0
        for i, task in enumerate(picked, 1):
            title = task.get('method_name') or task.get('run_name') or self.tr('子任务')
            named_layers, miss_t = self._layers_from_names(task.get('target_names'))
            ref_layers, miss_r = self._layers_from_names(task.get('ref_names'))
            missing = miss_t + miss_r
            if missing or not named_layers or not ref_layers:
                detail = '、'.join(missing) if missing else self.tr('图层为空')
                lines.append(self.tr('{0}. {1} 失败：{2}').format(i, title, detail))
                continue
            ret = run_field_naming(
                self.iface, self.project, named_layers, ref_layers,
                self._field_task_run_params(task, named_layers, ref_layers),
            )
            if not isinstance(ret, dict):
                ret = {'ok': False, 'error': self.tr('未返回结果')}
            if ret.get('ok'):
                ok_n += 1
                lines.append(self.tr('{0}. {1} 完成，写入 {2}').format(i, title, ret.get('written', 0)))
            else:
                lines.append(self.tr('{0}. {1} 失败：{2}').format(i, title, ret.get('error') or self.tr('未完成')))
        QMessageBox.information(
            self,
            self.tr('字段命名'),
            self.tr('完成 {0}/{1} 条。失败的已跳过，继续执行后面的子任务。\n').format(ok_n, len(picked))
            + '\n'.join(lines),
        )



    # ===== ①c 移动方案（与吸附／字段方案库分存，禁串库） =====
    def _geom_type_name(self, geom_type):
        return {
            QgsWkbTypes.GeometryType.PointGeometry: self.tr('点'),
            QgsWkbTypes.GeometryType.LineGeometry: self.tr('线'),
            QgsWkbTypes.GeometryType.PolygonGeometry: self.tr('面'),
        }.get(geom_type, self.tr('未知'))

    def _first_project_layer(self, names):
        for name in names or []:
            if not name:
                continue
            found = self.project.mapLayersByName(str(name))
            if found and isinstance(found[0], QgsVectorLayer):
                return found[0]
        return None

    def _populate_move_mode_combo(self, combo, target_names, ref_names, current):
        # Refill the move-mode combo when editing a subtask. Do not silently map withdrawn line-line codes to standard.
        current = current or 'standard'
        t_layer = self._first_project_layer(target_names)
        r_layer = self._first_project_layer(ref_names)
        combo.blockSignals(True)
        combo.clear()
        if t_layer is not None and r_layer is not None:
            add_mode_items(combo, move_mode_choices(t_layer, r_layer))
            combo.setToolTip(self.tr('按被移{0}、参考{1}列出。').format(
                self._geom_type_name(t_layer.geometryType()),
                self._geom_type_name(r_layer.geometryType()),
            ))
        else:
            if is_withdrawn_line_line_mode(current):
                combo.setToolTip(withdrawn_line_line_message(current))
            else:
                code = current if move_mode_known(current) else 'standard'
                combo.addItem(move_mode_label(code), code)
                combo.setToolTip(self.tr('工程里暂时找不到这些图层，还不能按点 / 线 / 面切换。'))
        self._select_move_mode_or_keep_withdrawn(combo, current, t_layer, r_layer)
        combo.blockSignals(False)

    def _select_move_mode_or_keep_withdrawn(self, combo, current, t_layer=None, r_layer=None):
        if current and is_withdrawn_line_line_mode(current):
            line_line = True
            if t_layer is not None and r_layer is not None:
                line_line = layers_are_line_line(t_layer, r_layer)
            if line_line:
                combo.setCurrentIndex(-1)
                self._invalid_move_mode = current
                return
        ix = combo.findData(current) if current else -1
        if ix >= 0:
            combo.setCurrentIndex(ix)
            self._invalid_move_mode = None
        elif current and not is_withdrawn_line_line_mode(current):
            ix = combo.findData('standard')
            if ix >= 0:
                combo.setCurrentIndex(ix)
            elif combo.count():
                combo.setCurrentIndex(0)
            self._invalid_move_mode = None
        elif combo.count() and combo.itemData(0) is not None:
            # Placeholder row (no layers yet) or empty selection: do not invent standard for a withdrawn code.
            if not current:
                combo.setCurrentIndex(0)
            else:
                combo.setCurrentIndex(-1)
        else:
            combo.setCurrentIndex(-1)


    def _update_move_pair_hint(self, targets, refs):
        # 2.2.7: hide the "select layers on both sides" hint; do not change list or validation.
        if hasattr(self, 'lbl_move_pair'):
            self.lbl_move_pair.hide()
            self.lbl_move_pair.setVisible(False)
        return
        if not hasattr(self, 'lbl_move_pair'):
            return
        if not targets or not refs:
            self.lbl_move_pair.setText(self.tr(
                '左右两侧都选好图层后，列表会按点 / 线 / 面切换。'
                '同一位置有两种选法：最近那一个要素，或容差内这个位置本身最近。'
            ))
            return
        text = self.tr(
            '当前：被移{0} → 参考{1}。'
            '「最近那条／那个」先按整条要素选，再取它上面的位置；'
            '「容差内距离最近」直接比这个位置，位置本身也要在容差内。'
        ).format(
            self._geom_type_name(targets[0].geometryType()),
            self._geom_type_name(refs[0].geometryType()),
        )
        extra = []
        if len({lyr.geometryType() for lyr in targets}) > 1:
            extra.append(self.tr('被移图层类型不一致，列表按第一个；其它类型执行时跳过。'))
        if len({lyr.geometryType() for lyr in refs}) > 1:
            extra.append(self.tr('参考图层类型不一致，列表按第一个。'))
        if extra:
            text += ''.join(extra)
        self.lbl_move_pair.setText(text)

    def _sync_move_mode_tip(self, *_args):
        combo = getattr(self, 'combo_move_mode', None)
        if combo is None:
            return
        base = self.tr(
            '移动模式：整要素平移，形状不变。列表随被移图层和参考图层的类型变化，'
            '不用再到参考图层那边单独选特殊检测。'
        )
        idx = combo.currentIndex()
        tip = combo.itemData(idx, Qt.ItemDataRole.ToolTipRole) if idx >= 0 else ''
        text = combo.currentText() if idx >= 0 else ''
        combo.setToolTip('{0}\n\n{1}{2}\n{3}'.format(
            base, self.tr('当前：'), text, tip or '',
        ).rstrip())

    def _refresh_move_mode_combo(self):
        if not hasattr(self, 'combo_move_mode'):
            return
        prev = self.combo_move_mode.currentData()
        if not prev:
            prev = getattr(self, '_invalid_move_mode', None)
        restore = getattr(self, '_restore_move_mode', None)
        if restore:
            prev = restore
            self._restore_move_mode = None
        targets = self._get_selected_layers(self.target_layer_list)
        refs = self._get_selected_layers(self.ref_layer_list)
        combo = self.combo_move_mode
        combo.blockSignals(True)
        combo.clear()
        if targets and refs:
            add_mode_items(combo, move_mode_choices(targets[0], refs[0]))
        else:
            combo.addItem(self.tr('请先选择被移图层和参考图层'), None)
        t_layer = targets[0] if targets else None
        r_layer = refs[0] if refs else None
        if prev:
            if is_withdrawn_line_line_mode(prev) and (not targets or not refs):
                self._restore_move_mode = prev
                self._invalid_move_mode = prev
                combo.setCurrentIndex(0 if combo.count() else -1)
            else:
                self._select_move_mode_or_keep_withdrawn(combo, prev, t_layer, r_layer)
                if combo.currentIndex() < 0 and prev and not (targets and refs):
                    self._restore_move_mode = prev
        elif combo.count() > 0 and combo.currentIndex() < 0:
            combo.setCurrentIndex(0)
        combo.blockSignals(False)
        self._update_move_pair_hint(targets, refs)
        self._sync_move_mode_tip()


    def _refresh_move_scheme_combo(self):
        if not hasattr(self, 'combo_move_scheme'):
            return
        self._move_scheme_loading = True
        self.combo_move_scheme.blockSignals(True)
        self.combo_move_scheme.clear()
        self.combo_move_scheme.addItem(self.tr('自定义方案（当前）'), self.MOVE_SCHEME_CUSTOM)
        for name in sorted(self._move_schemes.keys()):
            if isinstance(self._move_schemes.get(name), list):
                self.combo_move_scheme.addItem(name, name)
        idx = self.combo_move_scheme.findData(self._active_move_scheme)
        if idx < 0:
            self._active_move_scheme = self.MOVE_SCHEME_CUSTOM
            idx = 0
        self.combo_move_scheme.setCurrentIndex(idx)
        self.combo_move_scheme.blockSignals(False)
        self._move_scheme_loading = False
        has_scheme = any(isinstance(v, list) for v in self._move_schemes.values())
        if hasattr(self, 'btn_move_scheme_export'):
            self.btn_move_scheme_export.setEnabled(has_scheme)
        if hasattr(self, 'btn_move_scheme_view'):
            self.btn_move_scheme_view.setEnabled(self._active_move_scheme in self._move_schemes)

    def _on_move_scheme_changed(self, _index):
        if self._move_scheme_loading:
            return
        name = self.combo_move_scheme.currentData()
        self._active_move_scheme = name or self.MOVE_SCHEME_CUSTOM
        if hasattr(self, 'btn_move_scheme_view'):
            self.btn_move_scheme_view.setEnabled(self._active_move_scheme in self._move_schemes)

    def _current_move_scheme_payload(self):
        self._harvest_list_categories(self.target_layer_list, 'target')
        self._harvest_list_categories(self.ref_layer_list, 'ref')
        move_mode = 'standard'
        if hasattr(self, 'combo_move_mode'):
            move_mode = self.combo_move_mode.currentData() or 'standard'
        return {
            'target_names': [self._item_layer_name(i) for i in self.target_layer_list.selectedItems()],
            'ref_names': [self._item_layer_name(i) for i in self.ref_layer_list.selectedItems()],
            'target_categories': self._categories_map_from_list(self.target_layer_list),
            'ref_categories': self._categories_map_from_list(self.ref_layer_list),
            'tolerance': float(self.spin_tolerance.value()),
            'move_mode': move_mode,
        }

    def _clean_move_task(self, task):
        src = task if isinstance(task, dict) else {}
        clean = {
            'method_name': str(src.get('method_name') or src.get('run_name') or ''),
            'run_name': str(src.get('run_name') or src.get('method_name') or ''),
            'target_names': [str(n) for n in (src.get('target_names') or []) if n],
            'ref_names': [str(n) for n in (src.get('ref_names') or []) if n],
            'target_categories': normalize_category_map(src.get('target_categories')),
            'ref_categories': normalize_category_map(src.get('ref_categories')),
            'move_mode': str(src.get('move_mode') or 'standard'),
        }
        try:
            clean['tolerance'] = float(src.get('tolerance', 0.00001))
        except Exception:
            clean['tolerance'] = 0.00001
        if not move_mode_known(clean['move_mode']):
            clean['move_mode'] = 'standard'
        return clean

    def _normalize_move_schemes(self, raw):
        out = {}
        if not isinstance(raw, dict):
            return out
        for name, body in raw.items():
            if not isinstance(name, str) or not name or name == self.MOVE_SCHEME_CUSTOM:
                continue
            if not isinstance(body, list):
                continue
            out[name] = [self._clean_move_task(t) for t in body if isinstance(t, dict)]
        return out

    def _move_task_ready(self, payload):
        if not payload.get('target_names'):
            return self.tr('请先选择被移图层。')
        if not payload.get('ref_names'):
            return self.tr('请先选择参考图层。')
        return ''

    def _move_task_display_text(self, idx, task):
        tnames = self._names_with_categories(task.get('target_names') or [], task.get('target_categories'))
        rnames = self._names_with_categories(task.get('ref_names') or [], task.get('ref_categories'))
        mode = task.get('move_mode') or 'standard'
        mode_show = move_mode_label(mode)
        return self.tr('{0}. {1} | 被移:{2} | 参考:{3} | {4} | 容差:{5}').format(
            idx,
            task.get('method_name') or task.get('run_name') or self.tr('子任务'),
            tnames or '-',
            rnames or '-',
            mode_show,
            task.get('tolerance', 0.0),
        )

    def _choose_move_scheme_names_dialog(self):
        names = sorted(k for k, v in self._move_schemes.items() if isinstance(v, list))
        if not names:
            QMessageBox.information(self, self.tr('提示'), self.tr('暂无可加入的移动方案，请先在方案管理里新建方案。'))
            return []
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr('加入到移动方案'))
        lay = QVBoxLayout(dlg)
        lw = QListWidget()
        lw.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for name in names:
            lw.addItem(name)
        lay.addWidget(lw)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        localize_button_box(bb)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        lay.addWidget(bb)
        if run_dialog(dlg) != QDialog.DialogCode.Accepted:
            return []
        return [i.text() for i in lw.selectedItems()]

    def _add_move_task(self):
        payload = self._current_move_scheme_payload()
        err = self._move_task_ready(payload)
        if err:
            QMessageBox.warning(self, self.tr('提示'), err)
            return
        mname, ok = ask_text(self, self.tr('方法名称'), self.tr('请输入本次添加的方法名称：'))
        if not ok:
            return
        mname = (mname or '').strip() or time.strftime('%Y%m%d_%H%M%S')
        payload['method_name'] = mname
        payload['run_name'] = mname
        chosen = self._choose_move_scheme_names_dialog()
        if not chosen:
            return
        for name in chosen:
            tasks = self._move_schemes.setdefault(name, [])
            if not isinstance(tasks, list):
                tasks = []
                self._move_schemes[name] = tasks
            tasks.append(self._clean_move_task(payload))
        self._persist_settings()
        QMessageBox.information(self, self.tr('提示'), self.tr('已加入 {0} 个移动方案。').format(len(chosen)))

    def _apply_move_scheme_payload(self, data):
        if not isinstance(data, dict):
            return
        self._move_scheme_loading = True
        try:
            self._cat_move['target'] = normalize_category_map(data.get('target_categories'))
            self._cat_move['ref'] = normalize_category_map(data.get('ref_categories'))
            try:
                self.spin_tolerance.setValue(float(data.get('tolerance', self.spin_tolerance.value())))
            except Exception:  # nosec B110
                pass
            self._restore_move_mode = data.get('move_mode') or 'standard'
            self._skip_cat_harvest = True
            try:
                self.load_all_layers()
            finally:
                self._skip_cat_harvest = False
            self._select_layer_names(self.target_layer_list, data.get('target_names') or [])
            self._select_layer_names(self.ref_layer_list, data.get('ref_names') or [])
            self._refresh_move_mode_combo()
        finally:
            self._move_scheme_loading = False

    def _view_move_scheme(self):
        name = self._active_move_scheme
        if name == self.MOVE_SCHEME_CUSTOM or name not in self._move_schemes:
            QMessageBox.information(self, self.tr('提示'), self.tr('请选择一个移动方案。'))
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr('移动方案任务 - {0}').format(name))
        dlg.resize(760, 460)
        lay = QVBoxLayout(dlg)
        lw = QListWidget()
        lw.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        lay.addWidget(lw, 1)

        def _fill(focus=None):
            lw.clear()
            arr = self._move_schemes.get(name) or []
            for i, task in enumerate(arr):
                it = QListWidgetItem(self._move_task_display_text(i + 1, task))
                it.setData(Qt.ItemDataRole.UserRole, i)
                missing = []
                for layer_name in (task.get('target_names') or []) + (task.get('ref_names') or []):
                    if layer_name and not self.project.mapLayersByName(layer_name):
                        missing.append(layer_name)
                if missing:
                    it.setForeground(QBrush(QColor('#C62828')))
                    it.setToolTip(self.tr('工程中找不到：{0}').format('、'.join(missing)))
                lw.addItem(it)
                if focus is not None and i == focus:
                    it.setSelected(True)
                    lw.setCurrentItem(it)

        def _selected_indexes():
            idxs = []
            for it in lw.selectedItems():
                val = it.data(Qt.ItemDataRole.UserRole)
                if isinstance(val, int):
                    idxs.append(val)
            return sorted(set(idxs))

        def _move(delta):
            arr = self._move_schemes.get(name) or []
            idxs = _selected_indexes()
            if not idxs or not arr:
                return
            order = idxs if delta < 0 else list(reversed(idxs))
            moved = None
            for i in order:
                j = i + delta
                if j < 0 or j >= len(arr):
                    continue
                if delta < 0 and j in idxs:
                    continue
                if delta > 0 and j in idxs:
                    continue
                arr[i], arr[j] = arr[j], arr[i]
                moved = j
            if moved is None:
                return
            self._persist_settings()
            _fill(moved)

        def _edit():
            idxs = _selected_indexes()
            if len(idxs) != 1:
                QMessageBox.information(self, self.tr('提示'), self.tr('请选择一条子任务。'))
                return
            arr = self._move_schemes.get(name) or []
            updated = self._edit_move_task_dialog(arr[idxs[0]])
            if updated is None:
                return
            arr[idxs[0]] = updated
            self._persist_settings()
            _fill(idxs[0])

        def _delete():
            idxs = _selected_indexes()
            if not idxs:
                return
            reply = QMessageBox.question(
                dlg, self.tr('删除子任务'),
                self.tr('确定删除选中的 {0} 条子任务吗？').format(len(idxs)),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            arr = self._move_schemes.get(name) or []
            for i in reversed(idxs):
                if 0 <= i < len(arr):
                    arr.pop(i)
            self._persist_settings()
            _fill()

        def _load_current():
            idxs = _selected_indexes()
            if len(idxs) != 1:
                QMessageBox.information(self, self.tr('提示'), self.tr('请选择一条子任务。'))
                return
            arr = self._move_schemes.get(name) or []
            self._apply_move_scheme_payload(arr[idxs[0]])
            QMessageBox.information(self, self.tr('提示'), self.tr('已载入到当前参数，可修改后再添加。'))

        row = QHBoxLayout()
        btn_up = QPushButton(self.tr('上移'))
        btn_down = QPushButton(self.tr('下移'))
        btn_edit = QPushButton(self.tr('编辑'))
        btn_del = QPushButton(self.tr('删除'))
        btn_load = QPushButton(self.tr('载入当前'))
        btn_close = QPushButton(self.tr('关闭'))
        for b in (btn_up, btn_down, btn_edit, btn_del, btn_load, btn_close):
            b.setObjectName('schemeImportBtn')
            b.setFixedHeight(27)
            row.addWidget(b)
        btn_up.clicked.connect(lambda: _move(-1))
        btn_down.clicked.connect(lambda: _move(1))
        btn_edit.clicked.connect(_edit)
        btn_del.clicked.connect(_delete)
        btn_load.clicked.connect(_load_current)
        btn_close.clicked.connect(dlg.accept)
        lay.addLayout(row)
        _fill()
        run_dialog(dlg)

    def _edit_move_task_dialog(self, task):
        task = self._clean_move_task(task)
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr('编辑移动子任务'))
        dlg.resize(720, 480)
        lay = QVBoxLayout(dlg)
        grid = QGridLayout()
        name_edit = QLineEdit(task.get('method_name') or '')
        tol = QDoubleSpinBox()
        tol.setDecimals(6)
        tol.setRange(0.000001, 10000.0)
        tol.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        tol.setMinimumWidth(132)
        try:
            tol.setValue(float(task.get('tolerance') or 0.00001))
        except Exception:
            tol.setValue(0.00001)
        mode = QComboBox()
        mode.setMinimumWidth(280)
        mode.setMaxVisibleItems(22)
        mode.view().setMinimumWidth(680)
        self._populate_move_mode_combo(
            mode,
            task.get('target_names'),
            task.get('ref_names'),
            task.get('move_mode') or 'standard',
        )
        rows = (
            (self.tr('方法名称'), name_edit),
            (self.tr('容差'), tol),
            (self.tr('移动模式'), mode),
        )
        for i, (label, widget) in enumerate(rows):
            grid.addWidget(QLabel(label), i, 0)
            grid.addWidget(widget, i, 1)
        lay.addLayout(grid)

        def _name_box(title, names, on_changed):
            box = QGroupBox(title)
            box_lay = QVBoxLayout(box)
            lst = QListWidget()
            lst.setMaximumHeight(96)
            for n in names or []:
                if n:
                    lst.addItem(str(n))
            box_lay.addWidget(lst)
            row = QHBoxLayout()
            edit = QLineEdit()
            edit.setPlaceholderText(self.tr('图层名称'))
            btn_add = QPushButton(self.tr('添加'))
            btn_rm = QPushButton(self.tr('移除'))
            row.addWidget(edit, 1)
            row.addWidget(btn_add)
            row.addWidget(btn_rm)
            box_lay.addLayout(row)

            def _add():
                text = (edit.text() or '').strip()
                if text:
                    lst.addItem(text)
                    edit.clear()
                if on_changed:
                    on_changed()

            def _rm():
                for it in lst.selectedItems():
                    lst.takeItem(lst.row(it))
                if on_changed:
                    on_changed()

            btn_add.clicked.connect(_add)
            btn_rm.clicked.connect(_rm)
            return box, lst

        def _names_of(lst):
            return [
                lst.item(i).text().strip()
                for i in range(lst.count())
                if lst.item(i).text().strip()
            ]

        def _on_names_changed():
            self._populate_move_mode_combo(
                mode, _names_of(list_t), _names_of(list_r), mode.currentData() or 'standard',
            )

        box_t, list_t = _name_box(self.tr('被移图层'), task.get('target_names'), _on_names_changed)
        box_r, list_r = _name_box(self.tr('参考图层'), task.get('ref_names'), _on_names_changed)
        lay.addWidget(box_t)
        lay.addWidget(box_r)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        localize_button_box(bb)
        lay.addWidget(bb)

        def _accept():
            targets = [list_t.item(i).text().strip() for i in range(list_t.count()) if list_t.item(i).text().strip()]
            refs = [list_r.item(i).text().strip() for i in range(list_r.count()) if list_r.item(i).text().strip()]
            updated = dict(task)
            updated.update({
                'method_name': (name_edit.text() or '').strip() or task.get('method_name') or '',
                'run_name': (name_edit.text() or '').strip() or task.get('run_name') or '',
                'tolerance': float(tol.value()),
                'move_mode': mode.currentData() or 'standard',
                'target_names': targets,
                'ref_names': refs,
                'target_categories': self._trim_category_map(task.get('target_categories'), targets),
                'ref_categories': self._trim_category_map(task.get('ref_categories'), refs),
            })
            err = self._move_task_ready(updated)
            if err:
                QMessageBox.warning(dlg, self.tr('提示'), err)
                return
            dlg.setProperty('task', self._clean_move_task(updated))
            dlg.accept()

        bb.accepted.connect(_accept)
        bb.rejected.connect(dlg.reject)
        if run_dialog(dlg) != QDialog.DialogCode.Accepted:
            return None
        return dlg.property('task')

    def _move_scheme_manage_menu(self):
        menu = QMenu(self)
        act_new = menu.addAction(self.tr('新建方案'))
        act_rename = menu.addAction(self.tr('重命名'))
        act_dup = menu.addAction(self.tr('复制方案'))
        act_del = menu.addAction(self.tr('删除'))
        has = self._active_move_scheme in self._move_schemes
        act_rename.setEnabled(has)
        act_dup.setEnabled(has)
        act_del.setEnabled(has)
        chosen = run_menu(menu, self.btn_move_scheme_manage.mapToGlobal(self.btn_move_scheme_manage.rect().bottomLeft()))
        if chosen is act_new:
            self._create_move_scheme()
        elif chosen is act_rename:
            self._rename_move_scheme()
        elif chosen is act_dup:
            self._duplicate_move_scheme()
        elif chosen is act_del:
            self._delete_move_scheme()

    def _create_move_scheme(self):
        name, ok = ask_text(self, self.tr('新建移动方案'), self.tr('请输入方案名称：'))
        if not ok:
            return
        name = (name or '').strip()
        if not name:
            QMessageBox.warning(self, self.tr('提示'), self.tr('请输入未占用的方案名称。'))
            return
        if name == self.MOVE_SCHEME_CUSTOM or name in self._move_schemes:
            QMessageBox.warning(self, self.tr('提示'), self.tr('方案名称已存在，请更换名称。'))
            return
        self._move_schemes[name] = []
        self._active_move_scheme = name
        self._refresh_move_scheme_combo()
        self._persist_settings()

    def _duplicate_move_scheme(self):
        old = self._active_move_scheme
        if old == self.MOVE_SCHEME_CUSTOM or old not in self._move_schemes:
            QMessageBox.information(self, self.tr('提示'), self.tr('请先选择一个要复制的移动方案。'))
            return
        suffix = self.tr('副本')
        base = '{0}{1}'.format(old, suffix)
        new_name = base
        n = 2
        while new_name in self._move_schemes:
            new_name = '{0}{1}'.format(base, n)
            n += 1
        self._move_schemes[new_name] = copy.deepcopy(self._move_schemes[old])
        self._active_move_scheme = new_name
        self._refresh_move_scheme_combo()
        self._persist_settings()
        QMessageBox.information(self, self.tr('提示'), self.tr('已复制为新移动方案「{0}」。').format(new_name))

    def _rename_move_scheme(self):
        old = self._active_move_scheme
        if old == self.MOVE_SCHEME_CUSTOM or old not in self._move_schemes:
            return
        name, ok = ask_text(self, self.tr('重命名移动方案'), self.tr('请输入新名称：'), text=old)
        if not ok:
            return
        name = (name or '').strip()
        if not name:
            QMessageBox.warning(self, self.tr('提示'), self.tr('请输入未占用的方案名称。'))
            return
        if name == old:
            return
        if name == self.MOVE_SCHEME_CUSTOM or name in self._move_schemes:
            QMessageBox.warning(self, self.tr('提示'), self.tr('方案名称已存在，请更换名称。'))
            return
        self._move_schemes[name] = self._move_schemes.pop(old)
        self._active_move_scheme = name
        self._refresh_move_scheme_combo()
        self._persist_settings()

    def _delete_move_scheme(self):
        name = self._active_move_scheme
        if name == self.MOVE_SCHEME_CUSTOM or name not in self._move_schemes:
            return
        reply = QMessageBox.question(
            self,
            self.tr('删除移动方案'),
            self.tr('确定删除移动方案「{0}」及其全部子任务吗？').format(name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._move_schemes.pop(name, None)
        self._active_move_scheme = self.MOVE_SCHEME_CUSTOM
        self._refresh_move_scheme_combo()
        self._persist_settings()

    def _export_move_schemes(self):
        names = sorted(k for k, v in self._move_schemes.items() if isinstance(v, list))
        if not names:
            QMessageBox.information(self, self.tr('提示'), self.tr('暂无可导出的移动方案。'))
            return
        picked = self._pick_checked_names(self.tr('选择要导出的移动方案'), names)
        if picked is None:
            return
        if not picked:
            QMessageBox.information(self, self.tr('提示'), self.tr('请至少勾选一个方案。'))
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr('导出移动方案'),
            'spatial_match_topo_adjust_move_schemes.json',
            'JSON (*.json)',
        )
        path = self._json_save_path(path)
        if not path:
            return
        payload = {
            'kind': self.MOVE_SCHEME_KIND,
            'schema_version': 1,
            'plugin_version': PLUGIN_VERSION,
            'generator': DISPLAY_NAME,
            'exported_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'schemes': {k: self._move_schemes[k] for k in picked if k in self._move_schemes},
        }
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            QMessageBox.information(
                self, self.tr('提示'), self.tr('已导出 {0} 个移动方案。').format(len(payload['schemes']))
            )
        except Exception as exc:
            QMessageBox.warning(self, self.tr('提示'), self.tr('导出失败：{0}').format(str(exc)))

    def _import_move_schemes(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr('导入移动方案'), '', 'JSON (*.json)')
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
        except Exception as exc:
            QMessageBox.warning(self, self.tr('提示'), self.tr('导入失败：{0}').format(str(exc)))
            return
        if not isinstance(payload, dict):
            QMessageBox.warning(self, self.tr('提示'), self.tr('文件格式无效。'))
            return
        kind = payload.get('kind')
        if is_field_scheme_kind(kind):
            QMessageBox.warning(self, self.tr('提示'), self.tr('这是字段命名方案，请在字段命名里导入。'))
            return
        if not is_move_scheme_kind(kind):
            # 无 kind 的旧吸附导出 / 其它文件：一律拒，禁串入移动库
            QMessageBox.warning(
                self,
                self.tr('提示'),
                self.tr('这不是移动方案（kind 须为 cdet_move_schemes）。吸附方案请在吸附检测里导入，禁串库。'),
            )
            return
        incoming = payload.get('schemes')
        if not isinstance(incoming, dict):
            QMessageBox.warning(self, self.tr('提示'), self.tr('文件格式无效。'))
            return
        merged = 0
        overwritten = 0
        for name, body in incoming.items():
            if not isinstance(name, str) or not name or name == self.MOVE_SCHEME_CUSTOM:
                continue
            if not isinstance(body, list):
                continue
            if name in self._move_schemes:
                overwritten += 1
            self._move_schemes[name] = [self._clean_move_task(t) for t in body if isinstance(t, dict)]
            merged += 1
        self._refresh_move_scheme_combo()
        self._persist_settings()
        if merged == 0:
            QMessageBox.warning(self, self.tr('提示'), self.tr('文件里没有可导入的移动子任务列表。'))
            return
        QMessageBox.information(
            self,
            self.tr('提示'),
            self.tr('导入完成：共 {0} 个移动方案（其中同名覆盖 {1} 个）。').format(merged, overwritten),
        )

    def _pick_move_tasks_dialog(self, scheme_name, tasks):
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr('选择要执行的移动子任务 - {0}').format(scheme_name))
        dlg.setMinimumWidth(520)
        dlg.setMinimumHeight(360)
        lay = QVBoxLayout(dlg)
        lw = QListWidget()
        lw.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        for i, task in enumerate(tasks):
            it = QListWidgetItem(self._move_task_display_text(i + 1, task))
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            it.setCheckState(Qt.CheckState.Checked)
            it.setData(Qt.ItemDataRole.UserRole, i)
            lw.addItem(it)
        lay.addWidget(lw, 1)
        row = QHBoxLayout()
        btn_all = QPushButton(self.tr('全选'))
        btn_none = QPushButton(self.tr('全不选'))
        btn_ok = QPushButton(self.tr('执行'))
        btn_cancel = QPushButton(self.tr('取消'))
        btn_all.clicked.connect(lambda: [lw.item(i).setCheckState(Qt.CheckState.Checked) for i in range(lw.count())])
        btn_none.clicked.connect(lambda: [lw.item(i).setCheckState(Qt.CheckState.Unchecked) for i in range(lw.count())])
        row.addWidget(btn_all)
        row.addWidget(btn_none)
        row.addStretch(1)
        row.addWidget(btn_ok)
        row.addWidget(btn_cancel)
        lay.addLayout(row)
        btn_ok.clicked.connect(dlg.accept)
        btn_cancel.clicked.connect(dlg.reject)
        if run_dialog(dlg) != QDialog.DialogCode.Accepted:
            return None
        picked = []
        for i in range(lw.count()):
            it = lw.item(i)
            if it.checkState() == Qt.CheckState.Checked:
                picked.append(tasks[it.data(Qt.ItemDataRole.UserRole)])
        return picked

    def _run_move_scheme_batch(self, scheme_name):
        tasks = list(self._move_schemes.get(scheme_name) or [])
        if not tasks:
            QMessageBox.information(self, self.tr('提示'), self.tr('该移动方案还没有子任务。'))
            return
        picked = self._pick_move_tasks_dialog(scheme_name, tasks)
        if picked is None:
            return
        if not picked:
            QMessageBox.information(self, self.tr('提示'), self.tr('请至少勾选一条子任务。'))
            return
        cont = bool(getattr(self, 'chk_move_batch_continue', None) and self.chk_move_batch_continue.isChecked())
        lines = []
        ok_n = 0
        for i, task in enumerate(picked, 1):
            title = task.get('method_name') or task.get('run_name') or self.tr('子任务')
            named_layers, miss_t = self._layers_from_names(task.get('target_names'))
            ref_layers, miss_r = self._layers_from_names(task.get('ref_names'))
            missing = miss_t + miss_r
            if missing or not named_layers or not ref_layers:
                detail = '、'.join(missing) if missing else self.tr('图层为空')
                lines.append(self.tr('{0}. {1} 失败：{2}').format(i, title, detail))
                if not cont:
                    break
                continue
            try:
                ret = run_move(
                    self.iface,
                    self.project,
                    named_layers,
                    ref_layers,
                    float(task.get('tolerance', 0.00001)),
                    category_filters=filters_by_layer_id(
                        named_layers, task.get('target_categories')
                    ),
                    ref_category_filters=filters_by_layer_id(
                        ref_layers, task.get('ref_categories')
                    ),
                    show_messages=False,
                    show_progress=True,
                    move_mode=str(task.get('move_mode') or 'standard'),
                )
            except Exception as exc:
                lines.append(self.tr('{0}. {1} 失败：{2}').format(i, title, str(exc)))
                if not cont:
                    break
                continue
            if not isinstance(ret, dict):
                ret = {'ok': False, 'error': self.tr('未返回结果')}
            if ret.get('ok'):
                ok_n += 1
                lines.append(
                    self.tr('{0}. {1} 完成，移动 {2}').format(i, title, ret.get('moved', ret.get('written', 0)))
                )
            else:
                lines.append(self.tr('{0}. {1} 失败：{2}').format(i, title, ret.get('error') or self.tr('未完成')))
                if not cont:
                    break
        QMessageBox.information(
            self,
            self.tr('移动'),
            self.tr('完成 {0}/{1} 条。\n').format(ok_n, len(picked)) + '\n'.join(lines),
        )

    def _run_move_mode(self):
        # Whole-feature translate: preview first, write back after confirm. No snap-result layer.
        target_layers = self._get_selected_layers(self.target_layer_list)
        ref_layers = self._get_selected_layers(self.ref_layer_list)
        if not target_layers:
            QMessageBox.warning(self, self.tr('提示'), self.tr('请选择被移图层！'))
            return
        if not ref_layers:
            QMessageBox.warning(self, self.tr('提示'), self.tr('请选择参考图层！'))
            return
        tol = float(self.spin_tolerance.value())
        move_mode = self.combo_move_mode.currentData() or getattr(self, '_invalid_move_mode', None)
        if layers_are_line_line(target_layers[0], ref_layers[0]) and is_withdrawn_line_line_mode(move_mode):
            QMessageBox.warning(self, self.tr('提示'), withdrawn_line_line_message(move_mode))
            return
        if not move_mode or not move_mode_known(move_mode):
            QMessageBox.warning(self, self.tr('提示'), self.tr('请选择移动模式。'))
            return
        run_move(
            self.iface,
            self.project,
            target_layers,
            ref_layers,
            tol,
            category_filters=self._filters_for_list(self.target_layer_list, target_layers),
            ref_category_filters=self._filters_for_list(self.ref_layer_list, ref_layers),
            show_messages=True,
            show_progress=True,
            move_mode=move_mode,
        )


    def _run_core(self):
        self._persist_settings()
        if self._ui_mode == 'move':
            if self._active_move_scheme in self._move_schemes:
                self._run_move_scheme_batch(self._active_move_scheme)
            else:
                self._run_move_mode()
            return
        if self._ui_mode == 'field':
            if self._active_field_scheme in self._field_schemes:
                self._run_field_scheme_batch(self._active_field_scheme)
            else:
                self._run_field_naming()
            return
        if self._active_snap_scheme == self.SNAP_SCHEME_CUSTOM:
            target_layers = self._get_selected_layers(self.target_layer_list)
            ref_layers = self._get_selected_layers(self.ref_layer_list)
            ref_mode = self._effective_snap_ref_mode()
            ssm = self.combo_snap_spatial_mode.currentData()
            if ref_mode != 'standard':
                ssm = ssm or '__special__'
                if not target_layers:
                    QMessageBox.warning(self, self.tr('提示'), self.tr('请选择判断图层！'))
                    return
                geo = self._snap_target_geom_uniform()
                allowed = SPECIAL_TARGET_GEOMS.get(ref_mode)
                if allowed:
                    gname = {
                        QgsWkbTypes.GeometryType.PointGeometry: 'point',
                        QgsWkbTypes.GeometryType.LineGeometry: 'line',
                        QgsWkbTypes.GeometryType.PolygonGeometry: 'polygon',
                    }.get(geo)
                    if gname not in allowed:
                        kind = {
                            'point': self.tr('点'),
                            'line': self.tr('线'),
                            'polygon': self.tr('面'),
                        }
                        need = ' / '.join(kind[x] for x in allowed if x in kind)
                        QMessageBox.warning(
                            self, self.tr('提示'),
                            self.tr('{0}：判断图层须为{1}图层').format(special_mode_label(ref_mode), need),
                        )
                        return
                if ref_mode == 'polygon_inspect' and not self._polygon_outputs_selected():
                    QMessageBox.warning(
                        self, self.tr('提示'), self.tr('请在右侧「面检测输出」列表勾选至少一类输出'),
                    )
                    return
                if ref_mode in SPECIAL_REF_GEOM:
                    ref_need = SPECIAL_REF_GEOM[ref_mode]
                    ref_wkb = {
                        'point': QgsWkbTypes.GeometryType.PointGeometry,
                        'line': QgsWkbTypes.GeometryType.LineGeometry,
                        'polygon': QgsWkbTypes.GeometryType.PolygonGeometry,
                    }[ref_need]
                    ref_txt = {'point': self.tr('点'), 'line': self.tr('线'), 'polygon': self.tr('面')}[ref_need]
                    if not ref_layers:
                        QMessageBox.warning(
                            self, self.tr('提示'),
                            self.tr('{0}：请选择参考{1}图层').format(special_mode_label(ref_mode), ref_txt),
                        )
                        return
                    for rl in ref_layers:
                        if _layer_geom_class(rl) != ref_wkb:
                            QMessageBox.warning(
                                self, self.tr('提示'),
                                self.tr('{0}：参考图层须均为{1}图层').format(special_mode_label(ref_mode), ref_txt),
                            )
                            return
                    self.core.run(target_layers, ref_layers, self._compose_snap_run_params())
                    return
                self.core.run(target_layers, [], self._compose_snap_run_params())
                return
            if not target_layers:
                QMessageBox.warning(self, self.tr('提示'), self.tr('请选择判断图层！'))
                return
            if not ref_layers:
                QMessageBox.warning(self, self.tr('提示'), self.tr('请选择参考图层！'))
                return
            if not ssm or ssm == '__special__':
                QMessageBox.warning(self, self.tr('提示'), self.tr('请选择空间命名模式'))
                return
            self.core.run(target_layers, ref_layers, self._compose_snap_run_params())
            return
        self._run_batch_scheme(self._active_snap_scheme)

    def _pick_batch_tasks_dialog(self, scheme_name, tasks):
        """按分组列出，弹出勾选树；默认全选、组节点折叠；返回所选任务列表，取消返回 None。"""
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr('选择批量子任务'))
        dlg.setMinimumSize(520, 460)
        layout = QVBoxLayout(dlg)
        layout.addWidget(
            QLabel(
                self.tr('方案「{0}」— 勾选要执行的子方法（本次运行有效，不保存）').format(scheme_name)
            )
        )

        tree = QTreeWidget()
        tree.setColumnCount(1)
        tree.setHeaderHidden(True)
        tree.setExpandsOnDoubleClick(False)
        tree.setRootIsDecorated(True)
        tree.setIndentation(18)
        tree.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(tree)

        order = self._scheme_group_order(scheme_name)
        order_set = set(order)
        buckets = {g: [] for g in order}
        for i, t in enumerate(tasks):
            gk = self._task_group(t)
            if gk not in order_set:
                gk = self.UNGROUPED_KEY
                buckets.setdefault(gk, [])
                if gk not in order:
                    order.append(gk)
                    order_set.add(gk)
            buckets.setdefault(gk, []).append(i)

        # 静默标记，避免 itemChanged 在批量勾选时反复触发
        state = {'silent': False}

        for g in order:
            child_idxs = buckets.get(g, [])
            if not child_idxs:
                continue
            g_item = QTreeWidgetItem(tree)
            g_item.setText(0, self.tr('{0}  ({1})').format(self._group_display_name(g), len(child_idxs)))
            g_item.setFlags(g_item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsAutoTristate)
            g_item.setCheckState(0, Qt.CheckState.Checked)
            font = g_item.font(0)
            font.setBold(True)
            g_item.setFont(0, font)
            g_item.setData(0, Qt.ItemDataRole.UserRole, ('group', g))
            for i in child_idxs:
                t = tasks[i]
                method_name = t.get('method_name', t.get('run_name', self.tr('子任务')))
                c_item = QTreeWidgetItem(g_item)
                c_item.setText(0, method_name)
                c_item.setFlags(c_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                c_item.setCheckState(0, Qt.CheckState.Checked)
                c_item.setData(0, Qt.ItemDataRole.UserRole, ('task', i))
            g_item.setExpanded(False)

        # 单击组名：切换展开/折叠；点击复选框区域不切换
        def _on_item_clicked(item, _col):
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if not data or data[0] != 'group':
                return
            try:
                from qgis.PyQt.QtGui import QCursor
                rect = tree.visualItemRect(item)
                pos = tree.viewport().mapFromGlobal(QCursor.pos())
                # 估算：复选框 + indicator 大约位于行左侧 36px 内
                if pos.x() <= rect.left() + 36:
                    return
            except Exception:  # nosec B110
                pass
            item.setExpanded(not item.isExpanded())

        tree.itemClicked.connect(_on_item_clicked)

        row_btn = QHBoxLayout()
        row_btn.setSpacing(6)
        btn_all = QPushButton(self.tr('全选'))
        btn_inv = QPushButton(self.tr('反选'))
        btn_expand = QPushButton(self.tr('全部展开'))
        btn_collapse = QPushButton(self.tr('全部折叠'))
        btn_ok = QPushButton(self.tr('确定'))
        btn_cancel = QPushButton(self.tr('取消'))
        _pick_ss_actions = (
            'QPushButton { background-color: #1565C0; color: #ffffff; border: 1px solid #0D47A1; '
            'border-radius: 4px; padding: 5px 12px; min-height: 22px; } '
            'QPushButton:hover { background-color: #1976D2; } '
            'QPushButton:pressed { background-color: #0D47A1; }'
        )
        _pick_ss_dialog = (
            'QPushButton { background-color: #455A64; color: #ffffff; border: 1px solid #37474F; '
            'border-radius: 4px; padding: 5px 16px; min-height: 22px; } '
            'QPushButton:hover { background-color: #546E7A; } '
            'QPushButton:pressed { background-color: #37474F; }'
        )
        _pick_ss_ok = (
            'QPushButton { background-color: #c62828; color: #ffffff; border: 1px solid #b71c1c; '
            'border-radius: 4px; padding: 5px 16px; min-height: 22px; font-weight: 600; } '
            'QPushButton:hover { background-color: #d32f2f; border-color: #c62828; } '
            'QPushButton:pressed { background-color: #b71c1c; } '
            'QPushButton:focus { outline: none; } '
            'QPushButton:disabled { background-color: #e0e0e0; color: #9e9e9e; border: 1px solid #bdbdbd; }'
        )
        for b in (btn_all, btn_inv, btn_expand, btn_collapse):
            b.setStyleSheet(_pick_ss_actions)
            b.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        btn_ok.setStyleSheet(_pick_ss_ok)
        btn_cancel.setStyleSheet(_pick_ss_dialog)
        btn_ok.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        btn_cancel.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        btn_ok.setDefault(True)
        btn_ok.setAutoDefault(True)
        row_btn.addWidget(btn_all)
        row_btn.addWidget(btn_inv)
        row_btn.addWidget(btn_expand)
        row_btn.addWidget(btn_collapse)
        row_btn.addStretch(1)
        row_btn.addWidget(btn_ok)
        row_btn.addWidget(btn_cancel)
        layout.addLayout(row_btn)

        def _iter_leaves():
            root = tree.invisibleRootItem()
            for gi in range(root.childCount()):
                g = root.child(gi)
                for ci in range(g.childCount()):
                    yield g.child(ci)

        def _set_all_checked(checked):
            state['silent'] = True
            try:
                cs = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
                for leaf in _iter_leaves():
                    leaf.setCheckState(0, cs)
            finally:
                state['silent'] = False

        def _invert():
            state['silent'] = True
            try:
                for leaf in _iter_leaves():
                    leaf.setCheckState(
                        0,
                        Qt.CheckState.Unchecked if leaf.checkState(0) == Qt.CheckState.Checked else Qt.CheckState.Checked,
                    )
            finally:
                state['silent'] = False

        def _expand_all(flag):
            root = tree.invisibleRootItem()
            for gi in range(root.childCount()):
                root.child(gi).setExpanded(flag)

        btn_all.clicked.connect(lambda: _set_all_checked(True))
        btn_inv.clicked.connect(_invert)
        btn_expand.clicked.connect(lambda: _expand_all(True))
        btn_collapse.clicked.connect(lambda: _expand_all(False))
        btn_ok.clicked.connect(dlg.accept)
        btn_cancel.clicked.connect(dlg.reject)
        if run_dialog(dlg) != QDialog.DialogCode.Accepted:
            return None
        picked = []
        for leaf in _iter_leaves():
            if leaf.checkState(0) == Qt.CheckState.Checked:
                data = leaf.data(0, Qt.ItemDataRole.UserRole)
                if data and data[0] == 'task':
                    picked.append(tasks[data[1]])
        return picked

    def _resolve_layers_by_names(self, names):
        layers = []
        missing = []
        for n in names or []:
            found = self.project.mapLayersByName(n)
            if found:
                layers.append(found[0])
            else:
                missing.append(n)
        return layers, missing

    def _layer_name_exists(self, name):
        name = (name or '').strip()
        if not name:
            return False
        return bool(self.project.mapLayersByName(name))

    def _layer_name_list_item(self, name):
        item = QListWidgetItem(name)
        if name and not self._layer_name_exists(name):
            item.setForeground(QBrush(QColor('#C62828')))
        return item

    def _task_missing_layer_names(self, task):
        missing = []
        seen = set()
        for n in task.get('target_names', []) or []:
            n = (n or '').strip()
            if not n or n in seen:
                continue
            if not self._layer_name_exists(n):
                missing.append(n)
                seen.add(n)
        sp = task.get('_snap_special') or ''
        if sp not in SPECIAL_KEYS_NO_REF:
            for n in task.get('ref_names', []) or []:
                n = (n or '').strip()
                if not n or n in seen:
                    continue
                if not self._layer_name_exists(n):
                    missing.append(n)
                    seen.add(n)
        return missing

    def _scheme_missing_layer_names(self, scheme_name=None):
        name = self._active_snap_scheme if scheme_name is None else scheme_name
        if name == self.SNAP_SCHEME_CUSTOM or name not in self._snap_schemes:
            return None
        missing = []
        seen = set()
        for task in self._snap_schemes.get(name, []) or []:
            for n in self._task_missing_layer_names(task):
                if n not in seen:
                    missing.append(n)
                    seen.add(n)
        return missing

    def _set_view_button_chrome(self, btn, default_tip_src, status_tip=None):
        if btn is None:
            return
        btn.setText(self.tr('查看'))
        btn.setProperty('msgid', '查看')
        if status_tip:
            btn.setToolTip(status_tip)
        else:
            btn.setToolTip(self.tr(default_tip_src))
            btn.setProperty('tip', default_tip_src)

    def _update_scheme_layer_match_label(self):
        btn = getattr(self, 'btn_scheme_view', None)
        default_tip = '查看、编辑、删除、调整当前方案里的子任务'
        if btn is not None:
            missing = self._scheme_missing_layer_names()
            if missing is None:
                self._set_view_button_chrome(btn, default_tip)
            elif missing:
                shown = ', '.join(missing[:8])
                extra = self.tr(' 等') if len(missing) > 8 else ''
                tip = self.tr(
                    '当前方案有 {0} 个图层在本工程中找不到，配置仍保留，不会自动删除。'
                    '点查看后，红色方法里再点编辑选中，红色图层名即为缺失项。\n{1}{2}'
                ).format(len(missing), shown, extra)
                self._set_view_button_chrome(btn, default_tip, status_tip=tip)
            else:
                self._set_view_button_chrome(
                    btn, default_tip,
                    status_tip=self.tr('当前方案里配置的判断图层、参考图层，在本工程中都能找到。'),
                )
        # Field / move have no status rewrite historically; keep the short title.
        self._set_view_button_chrome(
            getattr(self, 'btn_field_scheme_view', None),
            '查看、编辑、删除、调整当前方案里的子任务',
        )
        self._set_view_button_chrome(
            getattr(self, 'btn_move_scheme_view', None),
            '查看、编辑、删除、调整当前移动方案里的子任务',
        )

    def _on_project_layers_changed(self, *_args):
        self._update_scheme_layer_match_label()

    def sizeHint(self):
        return QSize(700, 650)

    def minimumSizeHint(self):
        return QSize(640, 560)

    def showEvent(self, event):
        super().showEvent(event)
        self._update_scheme_layer_match_label()
        first = not getattr(self, '_default_applied', False)
        self._settle_main_layout()
        if first:
            # Every QGIS start builds a new dialog, so this is the only size restore.
            # A later resize stays on this object and is not written to QSettings.
            self._default_applied = True
            self.setMinimumSize(640, 560)
            self.resize(700, 650)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if getattr(self, '_in_resize_settle', False):
            return
        self._in_resize_settle = True
        try:
            self._apply_tolerance_spin_compact_width()
        except Exception:  # nosec B110
            pass
        finally:
            self._in_resize_settle = False

    def _run_batch_scheme(self, scheme_name):
        tasks = self._snap_schemes.get(scheme_name, [])
        if not tasks:
            QMessageBox.information(self, self.tr('提示'), self.tr('该方案暂无子任务。'))
            return
        picked = self._pick_batch_tasks_dialog(scheme_name, tasks)
        if picked is None:
            return
        if not picked:
            QMessageBox.information(self, self.tr('提示'), self.tr('请至少勾选一个子任务。'))
            return
        tasks = picked
        continue_on_error = bool(self.chk_batch_continue.isChecked())
        success_out_cnt = 0
        success_no_out_cnt = 0
        fail_missing_cnt = 0
        fail_empty_cnt = 0
        fail_runtime_cnt = 0
        total_out = 0
        t0 = time.time()
        lines = []
        total_steps = 0
        task_total_features = []
        for task in tasks:
            t_layers, _ = self._resolve_layers_by_names(task.get('target_names', []))
            c = sum(layer.featureCount() for layer in t_layers) if t_layers else 0
            task_total_features.append(max(c, 1))
            total_steps += max(c, 1)
        batch_progress = QProgressDialog(self.tr('批量执行中...'), self.tr('取消'), 0, max(total_steps, 1), self)
        batch_progress.setWindowModality(Qt.WindowModality.WindowModal)
        batch_progress.setMinimumDuration(0)
        done_steps = 0
        batch_overlap_skipped = []
        for i, task in enumerate(tasks, 1):
            method_name = task.get('method_name', task.get('run_name', self.tr('子任务')))
            if batch_progress.wasCanceled():
                lines.append(self.tr('{0}. {1}：已取消').format(i, method_name))
                break
            is_special = (task.get('_snap_special') or '') in SPECIAL_KEYS
            sk_b = task.get('_snap_special') or ''
            t_layers, miss_t = self._resolve_layers_by_names(task.get('target_names', []))
            r_layers, miss_r = self._resolve_layers_by_names(task.get('ref_names', []))
            overlap_allow_partial = is_special and sk_b == 'overlap_grp'

            if miss_t and not t_layers:
                fail_missing_cnt += 1
                miss = ', '.join(miss_t + miss_r)
                lines.append(self.tr('{0}. {1}：失败-图层不存在（{2}）').format(i, method_name, miss))
                done_steps += task_total_features[i - 1]
                batch_progress.setValue(min(done_steps, total_steps))
                if not continue_on_error:
                    break
                continue
            if miss_t and t_layers and not overlap_allow_partial:
                fail_missing_cnt += 1
                miss = ', '.join(miss_t + miss_r)
                lines.append(self.tr('{0}. {1}：失败-图层不存在（{2}）').format(i, method_name, miss))
                done_steps += task_total_features[i - 1]
                batch_progress.setValue(min(done_steps, total_steps))
                if not continue_on_error:
                    break
                continue
            if (not is_special) and miss_r:
                fail_missing_cnt += 1
                miss = ', '.join(miss_t + miss_r)
                lines.append(self.tr('{0}. {1}：失败-图层不存在（{2}）').format(i, method_name, miss))
                done_steps += task_total_features[i - 1]
                batch_progress.setValue(min(done_steps, total_steps))
                if not continue_on_error:
                    break
                continue
            target_total = sum(max(0, int(layer.featureCount())) for layer in t_layers)
            ref_total = sum(max(0, int(layer.featureCount())) for layer in r_layers)
            if target_total <= 0:
                fail_empty_cnt += 1
                reason = self.tr('判断图层无要素')
                lines.append(self.tr('{0}. {1}：失败-图层无要素（{2}）').format(i, method_name, reason))
                done_steps += task_total_features[i - 1]
                batch_progress.setValue(min(done_steps, total_steps))
                if not continue_on_error:
                    break
                continue
            if not is_special and ref_total <= 0:
                fail_empty_cnt += 1
                reason = self.tr('参考图层无要素')
                lines.append(self.tr('{0}. {1}：失败-图层无要素（{2}）').format(i, method_name, reason))
                done_steps += task_total_features[i - 1]
                batch_progress.setValue(min(done_steps, total_steps))
                if not continue_on_error:
                    break
                continue
            task_total = task_total_features[i - 1]

            def _on_progress(processed, total, _layer_name):
                cur = done_steps + max(0, min(processed, task_total))
                batch_progress.setValue(min(cur, total_steps))
                batch_progress.setLabelText(
                    self.tr('{0}({1}/{2}) > {3}({4}/{5})').format(
                        scheme_name,
                        i,
                        len(tasks),
                        task.get('method_name', task.get('run_name', self.tr('子任务'))),
                        min(processed, task_total),
                        task_total,
                    )
                )

            params = {
                'snap_enabled': bool(task.get('snap_enabled', True)),
                'tolerance': float(task.get('tolerance', 0.00001)),
                'spatial_mode': task.get('spatial_mode'),
                '_show_messages': False,
                '_show_summary': False,
                '_confirm_crs': False,
                '_show_progress': False,
                '_progress_cb': _on_progress,
                '_output_tag': task.get('method_name', task.get('run_name', '')),
                '_category_target': filters_by_layer_id(t_layers, task.get('target_categories')),
                '_category_ref': filters_by_layer_id(r_layers, task.get('ref_categories')),
            }
            if is_special:
                params['_snap_special'] = task.get('_snap_special')
                po_task = task.get('_polygon_outputs')
                if isinstance(po_task, list) and po_task:
                    params['_polygon_outputs'] = list(po_task)
                elif task.get('_polygon_submode'):
                    params['_polygon_outputs'] = [str(task.get('_polygon_submode'))]
                params['_polygon_area_tol_m2'] = float(task.get('_polygon_area_tol_m2', 1.0))
                params['_polygon_overlap_area_tol_m2'] = float(
                    task.get('_polygon_overlap_area_tol_m2', task.get('_polygon_area_tol_m2', 1.0))
                )
                params['_line_length_rule'] = dict(
                    task.get('_line_length_rule') or {'kind': 'le', 'threshold': 0}
                )
                params['_snap_count_rule'] = dict(
                    task.get('_snap_count_rule') or {'kind': 'le', 'threshold': 0}
                )
                params['_count_attach'] = normalize_count_attach(task.get('_count_attach'))
                params['_count_output_mates'] = bool(task.get('_count_output_mates'))
                sk_b = task.get('_snap_special') or ''
                if sk_b == 'overlap_grp':
                    ok = str(task.get('_overlap_kind') or 'auto').strip()
                    if ok not in ('auto', 'point', 'line', 'polygon'):
                        ok = 'polygon'
                    params['_overlap_kind'] = ok
                elif task.get('_overlap_kind'):
                    params['_overlap_kind'] = task.get('_overlap_kind')
                params['_overlap_scope'] = normalize_overlap_scope(str(task.get('_overlap_scope') or 'per_layer'))
                params['_line_overlap_min_length'] = float(task.get('_line_overlap_min_length', 1.0))
                params['_point_line_chain_min_seg'] = int(task.get('_point_line_chain_min_seg', 3))
                params.update(normalize_special_values(task))
            elif task.get('mode_param') is not None:
                params['mode_param'] = task.get('mode_param')
            sk_exec = task.get('_snap_special') or ''
            exec_ref = [] if sk_exec in SPECIAL_KEYS_NO_REF else r_layers
            if overlap_allow_partial and miss_t:
                params['_missing_target_names'] = list(miss_t)
                batch_overlap_skipped.extend(miss_t)
            ret = self.core.run(t_layers, exec_ref, params) or {}
            done_steps += task_total
            batch_progress.setValue(min(done_steps, total_steps))
            if ret.get('ok'):
                out_names = ret.get('results', {}).get('layers_created', [])
                total_out += len(out_names)
                if out_names:
                    success_out_cnt += 1
                    ln = self.tr('{0}. {1}：成功已输出（{2} 个图层）').format(i, method_name, len(out_names))
                    if overlap_allow_partial and miss_t:
                        ln += self.tr('（已跳过缺失图层：{0}）').format(', '.join(miss_t))
                    lines.append(ln)
                else:
                    success_no_out_cnt += 1
                    ln = self.tr('{0}. {1}：成功未输出（无命中结果）').format(i, method_name)
                    if overlap_allow_partial and miss_t:
                        ln += self.tr('（已跳过缺失图层：{0}）').format(', '.join(miss_t))
                    lines.append(ln)
            else:
                err = str(ret.get('error', self.tr('未知错误')))
                if ret.get('error_code') in EMPTY_FEATURES:
                    fail_empty_cnt += 1
                    lines.append(self.tr('{0}. {1}：失败-图层无要素（{2}）').format(i, method_name, err))
                else:
                    fail_runtime_cnt += 1
                    lines.append(self.tr('{0}. {1}：失败-执行异常（{2}）').format(i, method_name, err))
                if not continue_on_error:
                    break
        batch_progress.close()
        elapsed = time.time() - t0
        fail_cnt = fail_missing_cnt + fail_empty_cnt + fail_runtime_cnt
        msg = self.tr(
            '批量方案：{0}\n子任务总数：{1}\n成功已输出：{2}\n成功未输出：{3}\n'
            '失败-图层不存在：{4}\n失败-图层无要素：{5}\n失败-执行异常：{6}\n失败合计：{7}\n输出图层数：{8}\n耗时：{9:.2f} 秒\n'
        ).format(
            scheme_name,
            len(tasks),
            success_out_cnt,
            success_no_out_cnt,
            fail_missing_cnt,
            fail_empty_cnt,
            fail_runtime_cnt,
            fail_cnt,
            total_out,
            elapsed,
        )
        if lines:
            msg += '\n' + self.tr('明细：\n') + '\n'.join(lines)
        if batch_overlap_skipped:
            mb = QMessageBox(self)
            mb.setIcon(QMessageBox.Icon.Information)
            mb.setWindowTitle(self.tr('批量监测结果'))
            mb.setTextFormat(Qt.TextFormat.RichText)
            uniq = sorted(set(batch_overlap_skipped))
            esc = html.escape(msg, quote=True)
            red_title = html.escape(self.tr('以下判断图层在项目中未找到，已从对应重叠检测中跳过：'), quote=True)
            red_list = html.escape(', '.join(uniq), quote=True)
            mb.setText(
                '<div>'
                '<pre style="white-space:pre-wrap;margin:0 0 8px 0;">' + esc + '</pre>'
                '<p style="margin:0;line-height:1.45;">'
                '<span style="color:#c62828;font-weight:bold;">' + red_title + '</span><br/>'
                '<span style="color:#c62828;">' + red_list + '</span>'
                '</p></div>'
            )
            run_dialog(mb)
        else:
            QMessageBox.information(self, self.tr('批量监测结果'), msg)
