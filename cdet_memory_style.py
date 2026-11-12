# -*- coding: utf-8 -*-
"""临时内存矢量图层符号：从 QgsSettings 读取，「临时样式」对话框写入。

与「20260503 V6」相同：`QgsMarkerSymbol.createSimple` 一次传入
size / fill / outline_width / outline_color。
「随机颜色」模式实为 **内置调色板按顺序循环**（非真随机），避免渲染管线对随机 RGB 不生效的问题；
仍沿用设置里保存描边的透明度（第四分量）。
"""
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsVectorLayer,
    QgsWkbTypes,
    QgsSettings,
    QgsMarkerSymbol,
    QgsLineSymbol,
    QgsFillSymbol,
    QgsSingleSymbolRenderer,
)
from .settings_compat import settings_value, settings_set

KEY_PT_SIZE = 'mem_point_size'
KEY_PT_FILL = 'mem_point_fill'
KEY_PT_OUTLINE = 'mem_point_outline'
KEY_PT_OUTLINE_W = 'mem_point_outline_w'
KEY_PT_OUTLINE_RANDOM = 'mem_point_outline_random'

KEY_LN_COLOR = 'mem_line_color'
KEY_LN_WIDTH = 'mem_line_width'
KEY_LN_STYLE = 'mem_line_style'

# 内置描边色（高区分度），按每次生成临时点图层的顺序循环使用
_OUTLINE_PALETTE_INDEX = 0
OUTLINE_PALETTE_RGB = [
    (228, 26, 28),
    (55, 126, 184),
    (77, 175, 74),
    (152, 78, 163),
    (255, 127, 0),
    (166, 86, 40),
    (247, 129, 191),
    (153, 153, 153),
    (23, 190, 207),
    (255, 187, 120),
]


def default_point_style():
    return {
        'size': 6.0,
        'fill': '0,0,0,0',
        'outline': '0,0,0',
        'outline_width': 1.0,
        'outline_random': True,
    }


def default_line_style():
    return {
        'color': '0,0,0',
        'width': 5.0,
        'line_style': 'dash',
    }


def _coerce_settings_bool(val, default=False):
    """避免 QgsSettings 读出字符串时 bool('false')==True。"""
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(int(val))
    if isinstance(val, str):
        t = val.strip().lower()
        if t in ('1', 'true', 'yes', 'on'):
            return True
        if t in ('0', 'false', 'no', 'off', ''):
            return False
    return default


def load_point_style(qgs=None):
    s = qgs if qgs is not None else QgsSettings()
    d = default_point_style()
    try:
        d['size'] = float(settings_value(s, KEY_PT_SIZE, d['size'], type=float))
    except (TypeError, ValueError):
        d['size'] = default_point_style()['size']
    fv = settings_value(s, KEY_PT_FILL, d['fill'])
    d['fill'] = str(fv) if fv is not None else d['fill']
    ov = settings_value(s, KEY_PT_OUTLINE, d['outline'])
    d['outline'] = str(ov) if ov is not None else d['outline']
    try:
        d['outline_width'] = float(settings_value(s, KEY_PT_OUTLINE_W, d['outline_width'], type=float))
    except (TypeError, ValueError):
        d['outline_width'] = default_point_style()['outline_width']
    try:
        rv = settings_value(s, KEY_PT_OUTLINE_RANDOM, d['outline_random'], type=bool)
    except Exception:
        rv = settings_value(s, KEY_PT_OUTLINE_RANDOM, d['outline_random'])
    d['outline_random'] = _coerce_settings_bool(rv, d['outline_random'])
    return d


def save_point_style(d, qgs=None):
    s = qgs if qgs is not None else QgsSettings()
    settings_set(s, KEY_PT_SIZE, float(d['size']))
    settings_set(s, KEY_PT_FILL, str(d['fill']))
    settings_set(s, KEY_PT_OUTLINE, str(d['outline']))
    settings_set(s, KEY_PT_OUTLINE_W, float(d['outline_width']))
    settings_set(s, KEY_PT_OUTLINE_RANDOM, bool(d.get('outline_random', False)))


def load_line_style(qgs=None):
    s = qgs if qgs is not None else QgsSettings()
    d = default_line_style()
    try:
        d['width'] = float(settings_value(s, KEY_LN_WIDTH, d['width'], type=float))
    except (TypeError, ValueError):
        d['width'] = default_line_style()['width']
    cv = settings_value(s, KEY_LN_COLOR, d['color'])
    d['color'] = str(cv) if cv is not None else d['color']
    sv = settings_value(s, KEY_LN_STYLE, d['line_style'])
    d['line_style'] = str(sv) if sv is not None else d['line_style']
    return d


def save_line_style(d, qgs=None):
    s = qgs if qgs is not None else QgsSettings()
    settings_set(s, KEY_LN_COLOR, str(d['color']))
    settings_set(s, KEY_LN_WIDTH, float(d['width']))
    settings_set(s, KEY_LN_STYLE, str(d['line_style']))


def _point_marker_props(pt, outline_color_csv):
    """与 V6 完全一致的一张属性表；outline_color_csv 为「指定」或「调色板下一色」得到的 CSV。"""
    return {
        'name': 'circle',
        'color': _rgb_csv(pt['fill']),
        'size': str(pt['size']),
        'outline_color': _rgb_csv(outline_color_csv),
        'outline_width': str(pt['outline_width']),
    }


def _qcolor_from_rgb_csv(s):
    if not s or not isinstance(s, str):
        return QColor(0, 0, 0)
    parts = [p.strip() for p in s.split(',') if p.strip() != '']
    try:
        nums = [int(float(p)) for p in parts]
    except (TypeError, ValueError):
        return QColor(0, 0, 0)
    if len(nums) >= 4:
        return QColor(nums[0], nums[1], nums[2], nums[3])
    if len(nums) == 3:
        return QColor(nums[0], nums[1], nums[2])
    return QColor(0, 0, 0)


def _force_symbol_outline_color(marker_symbol, outline_csv):
    """调色板模式下确保符号层描边色与 CSV 一致。"""
    if marker_symbol is None or marker_symbol.symbolLayerCount() < 1:
        return
    sl = marker_symbol.symbolLayer(0)
    qc = _qcolor_from_rgb_csv(_rgb_csv(outline_csv))
    try:
        if hasattr(sl, 'setStrokeColor'):
            sl.setStrokeColor(qc)
    except Exception:
        pass


def _palette_outline_rgb_csv(fallback_outline_csv):
    """从内置调色板取下一色（全局递增，按图层生成顺序循环）。"""
    global _OUTLINE_PALETTE_INDEX
    a = 255
    if fallback_outline_csv and isinstance(fallback_outline_csv, str):
        parts = [p.strip() for p in fallback_outline_csv.split(',') if p.strip() != '']
        if len(parts) >= 4:
            try:
                a = max(0, min(255, int(float(parts[3]))))
            except (TypeError, ValueError):
                pass
    r, g, b = OUTLINE_PALETTE_RGB[_OUTLINE_PALETTE_INDEX % len(OUTLINE_PALETTE_RGB)]
    _OUTLINE_PALETTE_INDEX += 1
    if a >= 255:
        return f'{r},{g},{b}'
    return f'{r},{g},{b},{a}'


def _apply_point_renderer(memory_layer, pt):
    """单一入口：先算描边 CSV，再 createSimple。"""
    use_palette = bool(pt.get('outline_random'))
    outline_csv = pt['outline']
    if use_palette:
        try:
            outline_csv = _palette_outline_rgb_csv(pt.get('outline'))
        except Exception:
            outline_csv = pt['outline']
            use_palette = False
    props = _point_marker_props(pt, outline_csv)
    sym = None
    try:
        sym = QgsMarkerSymbol.createSimple(props)
    except Exception:
        sym = None
    if sym is None:
        sym = QgsMarkerSymbol.createSimple(_point_marker_props(pt, pt['outline']))
    if use_palette and sym is not None:
        _force_symbol_outline_color(sym, outline_csv)
    memory_layer.setRenderer(QgsSingleSymbolRenderer(sym))


def apply_memory_output_style(memory_layer):
    """按 QgsSettings 中的「临时点/线」配置渲染内存图层（面仍为内置默认）。"""
    if not memory_layer or not isinstance(memory_layer, QgsVectorLayer):
        return
    s = QgsSettings()
    pt = load_point_style(s)
    ln = load_line_style(s)
    gt = memory_layer.geometryType()
    try:
        if gt == QgsWkbTypes.PointGeometry:
            _apply_point_renderer(memory_layer, pt)
        elif gt == QgsWkbTypes.LineGeometry:
            sym = QgsLineSymbol.createSimple({
                'color': _rgb_csv(ln['color']),
                'width': str(ln['width']),
                'line_style': str(ln['line_style']),
            })
            memory_layer.setRenderer(QgsSingleSymbolRenderer(sym))
        elif gt == QgsWkbTypes.PolygonGeometry:
            sym = QgsFillSymbol.createSimple({
                'color': '255,220,220,200',
                'outline_color': '255,0,0',
                'outline_width': '0.9',
                'style': 'solid',
            })
            memory_layer.setRenderer(QgsSingleSymbolRenderer(sym))
        memory_layer.triggerRepaint()
    except Exception:
        pass


def _rgb_csv(s):
    """保证 createSimple 收到逗号分隔的分量；若为非法字符串则退回黑色。"""
    if not s or not isinstance(s, str):
        return '0,0,0'
    parts = [p.strip() for p in s.split(',') if p.strip() != '']
    try:
        nums = [int(float(p)) for p in parts]
    except (TypeError, ValueError):
        return '0,0,0'
    if len(nums) == 3:
        return f'{nums[0]},{nums[1]},{nums[2]}'
    if len(nums) >= 4:
        return f'{nums[0]},{nums[1]},{nums[2]},{nums[3]}'
    return '0,0,0'
