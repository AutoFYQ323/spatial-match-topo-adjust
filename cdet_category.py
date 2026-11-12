# -*- coding: utf-8 -*-
"""读取 QGIS 分类/规则符号化，供图层列表筛选。不改图层符号化。"""

from qgis.core import (
    NULL,
    QgsCategorizedSymbolRenderer,
    QgsFeatureRequest,
    QgsRuleBasedRenderer,
)

try:
    from qgis.PyQt.QtCore import Qt
except Exception:
    Qt = None

ROLE_LAYER_ID = (Qt.UserRole + 21) if Qt is not None else 293
ROLE_LAYER_NAME = (Qt.UserRole + 22) if Qt is not None else 294
ROLE_HAS_CATS = (Qt.UserRole + 23) if Qt is not None else 295
ROLE_CATS = (Qt.UserRole + 24) if Qt is not None else 296
ROLE_FEATURE_COUNT = (Qt.UserRole + 25) if Qt is not None else 297

MAX_CATEGORIES = 400
CAT_MARK = '◆◆'


def format_layer_caption(name, labels):
    """FAT + [A,B] -> FAT(A&B)。没有分类名时只返回图层名。"""
    name = name or ''
    clean = []
    for label in labels or []:
        text = str(label).strip()
        if text:
            clean.append(text)
    if not clean:
        return name
    return '%s(%s)' % (name, '&'.join(clean))


def layer_item_display(name, has_categories, labels, feature_count=None):
    """列表文字：图层名、可选分类括号，再跟单独一对要素数括号。

    例：名、名(A&B)、名(12)、名(A&B)(12)。◆◆ 由委托绘制。
    要素数只作展示；不要从这段文字反解析图层名。
    """
    caption = format_layer_caption(name, labels)
    if feature_count is None:
        return caption
    try:
        n = int(feature_count)
    except (TypeError, ValueError):
        return caption
    if n < 0:
        n = 0
    return '%s(%s)' % (caption, n)


def safe_feature_count(layer):
    if layer is None:
        return 0
    try:
        n = layer.featureCount()
    except Exception:
        return 0
    try:
        n = int(n)
    except (TypeError, ValueError):
        return 0
    return n if n >= 0 else 0


def count_features_by_expr(layer, expr):
    """Count features matching filter_expr. Return None when it cannot be computed."""
    if layer is None:
        return None
    text = (expr or '').strip()
    if not text:
        return None
    try:
        req = QgsFeatureRequest()
        req.setFilterExpression(text)
        try:
            req.setFlags(QgsFeatureRequest.NoGeometry)
        except Exception:
            pass
        n = 0
        for _feat in layer.getFeatures(req):
            n += 1
        return n
    except Exception:
        return None


def layers_feature_count(layers):
    """组内矢量要素合计，不是图层个数。"""
    total = 0
    for layer in layers or []:
        total += safe_feature_count(layer)
    return total


def unwrap_renderer(renderer):
    wrappers = {
        'invertedPolygonRenderer',
        'pointCluster',
        'pointDisplacement',
        'mergedFeatureRenderer',
    }
    current = renderer
    for _ in range(3):
        if current is None:
            return None
        try:
            rtype = current.type()
        except Exception:
            break
        if rtype not in wrappers:
            break
        getter = getattr(current, 'embeddedRenderer', None)
        if not callable(getter):
            break
        try:
            inner = getter()
        except Exception:
            break
        if inner is None or inner is current:
            break
        current = inner
    return current


def _is_blank_value(value):
    if value is None or value == NULL:
        return True
    try:
        text = str(value).strip()
    except Exception:
        return True
    return text == '' or text.lower() == 'null'


def _sql_literal(value):
    if isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return repr(value) if value != int(value) else str(int(value))
    text = str(value).replace("'", "''")
    return "'%s'" % text


def _field_eq(field, value):
    name = (field or '').replace('"', '""')
    return '"%s" = %s' % (name, _sql_literal(value))


def _field_names(layer):
    names = set()
    try:
        for field in layer.fields():
            names.add(field.name())
    except Exception:
        pass
    return names


def _needs_paren(text):
    upper = (text or '').upper()
    return ' AND ' in upper or ' OR ' in upper


def layer_filter_categories(layer):
    """
    可筛选分类，顺序与符号化一致。
    每项 {label, filter_expr}。图例未勾选的类别也列出。
    没有过滤表达式的类（其它值/空类、ELSE）不返回。
    """
    if layer is None or not hasattr(layer, 'renderer'):
        return []
    try:
        renderer = unwrap_renderer(layer.renderer())
    except Exception:
        return []
    if renderer is None:
        return []
    try:
        if isinstance(renderer, QgsCategorizedSymbolRenderer):
            return _from_categorized(layer, renderer)
        if isinstance(renderer, QgsRuleBasedRenderer):
            return _from_rules(renderer)
    except Exception:
        return []
    return []


def _from_categorized(layer, renderer):
    attr = (renderer.classAttribute() or '').strip()
    if len(attr) >= 2 and attr[0] == '"' and attr[-1] == '"':
        attr = attr[1:-1]
    if not attr:
        return []
    is_field = attr in _field_names(layer)
    items = []
    try:
        categories = list(renderer.categories() or [])
    except Exception:
        return items
    for cat in categories:
        if len(items) >= MAX_CATEGORIES:
            break
        try:
            value = cat.value()
        except Exception:
            continue
        if _is_blank_value(value):
            continue
        if is_field:
            expr = _field_eq(attr, value)
        else:
            expr = '(%s) = %s' % (attr, _sql_literal(value))
        try:
            label = (cat.label() or '').strip()
        except Exception:
            label = ''
        if not label:
            label = str(value)
        items.append({'label': label, 'filter_expr': expr})
    return items


def _from_rules(renderer):
    items = []
    try:
        root = renderer.rootRule()
    except Exception:
        return items
    _walk_rules(root, items, [], set(), 0)
    return items


def _walk_rules(rule, items, inherited, seen, depth):
    if rule is None or depth > 30 or len(items) >= MAX_CATEGORIES:
        return
    marker = id(rule)
    if marker in seen:
        return
    seen.add(marker)
    try:
        if hasattr(rule, 'isElse') and rule.isElse():
            return
    except Exception:
        pass
    expr = ''
    try:
        expr = (rule.filterExpression() or '').strip()
    except Exception:
        expr = ''
    parts = list(inherited)
    if expr:
        parts.append(expr)
    children = []
    try:
        children = list(rule.children() or [])
    except Exception:
        children = []
    if children:
        for child in children:
            _walk_rules(child, items, parts, seen, depth + 1)
        return
    if not parts or len(items) >= MAX_CATEGORIES:
        return
    combined = ' AND '.join('(%s)' % p if _needs_paren(p) else p for p in parts)
    label = ''
    try:
        label = (rule.label() or '').strip()
    except Exception:
        label = ''
    if not label:
        label = combined
    items.append({'label': label, 'filter_expr': combined})


def normalize_category_map(raw):
    """方案里的分类：图层名 -> [{label, filter_expr}]。空映射返回 {}。"""
    if not isinstance(raw, dict):
        return {}
    out = {}
    for name, items in raw.items():
        if not isinstance(name, str) or not name or not isinstance(items, list):
            continue
        cleaned = []
        for it in items:
            if not isinstance(it, dict):
                continue
            expr = str(it.get('filter_expr') or '').strip()
            if not expr:
                continue
            label = str(it.get('label') or '').strip() or expr
            cleaned.append({'label': label, 'filter_expr': expr})
        if cleaned:
            out[name] = cleaned
    return out


def align_saved_categories(layer, saved):
    """按当前符号化顺序保留仍能对上的筛选条件，显示名用当前图例名。"""
    live = layer_filter_categories(layer)
    if not live:
        return [], []
    wanted = set()
    if isinstance(saved, list):
        for it in saved:
            if isinstance(it, dict):
                expr = str(it.get('filter_expr') or '').strip()
                if expr:
                    wanted.add(expr)
    picked = [dict(c) for c in live if c.get('filter_expr') in wanted]
    return live, picked


def filters_by_layer_id(layers, by_name):
    """图层 id -> 过滤表达式列表。没有分类项时返回空字典（整层）。"""
    mapping = normalize_category_map(by_name)
    out = {}
    if not mapping:
        return out
    for lyr in layers or []:
        items = mapping.get(lyr.name())
        if not items:
            continue
        exprs = [it['filter_expr'] for it in items if it.get('filter_expr')]
        if exprs:
            out[lyr.id()] = exprs
    return out


def iter_features(layer, filters_by_id=None):
    """有筛选表达式时只迭代命中分类；没有则整层。"""
    exprs = None
    if filters_by_id and layer is not None:
        exprs = filters_by_id.get(layer.id())
    if not exprs:
        return layer.getFeatures()
    req = QgsFeatureRequest()
    req.setFilterExpression(' OR '.join('(%s)' % e for e in exprs))
    return layer.getFeatures(req)
