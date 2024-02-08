from django import template
from apps.core.encrypt_url_utils import encrypt

register = template.Library()

@register.filter
def encfile(src): # pragma: no cover
    if src:
        if 'media/' not in src:
            path = src.split('/')
            name = path.pop()
            path = '/'.join(path)
            return f'{path}/{encrypt(name)}'
        else:
            arr_media = src.split('/')
            media = arr_media[1]
            arr_media.pop(0)
            arr_media.pop(0)
            
            name = arr_media.pop()
            if arr_media:
                path = '/'.join(arr_media)
                return f'/{media}/{path}/{encrypt(name)}'
        
@register.filter
def dd(src): # pragma: no cover
    import json
    dicts = dir(src)
    object_data = {}
    for di in dicts:
        if not str(di).startswith('_'):
            try:
                object_rel = getattr(src,di)
                if hasattr(object_rel,'__dict__') and di not in ['DoesNotExist','Meta','MultipleObjectsReturned']:
                    object_data[di] = vars(object_rel)
                    if object_data[di]['_state']:
                        del object_data[di]['_state']
            except Exception: pass
    return convert_to_html_ul_li(object_data)

def convert_to_html_ul_li(obj, parent_key=''):
    html = '<ul>'
    for key, value in obj.items():
        current_key = f'{parent_key}.{key}' if parent_key else key
        if isinstance(value, dict):
            html += f'<li>{key}: {convert_to_html_ul_li(value, current_key)}</li>'
        else:
            html += f'<li>{key}: {value}</li>'
    html += '</ul>'
    return html

@register.filter(name='get_nested_attr')
def get_nested_attr(obj, key):
    keys = key.split('.')
    try:
        for k in keys:
            obj = obj[k]
        return obj
    except (TypeError, KeyError):
        return None
    
@register.filter
def get_field_from_instance(obj,field):
    return getattr(obj,field)