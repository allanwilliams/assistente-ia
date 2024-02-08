from django.urls import reverse
from django import template
from apps.core.encrypt_url_utils import encrypt

register = template.Library()


@register.filter('test')
def test(obj):
    try:
        print()
        print(obj.widget.__dict__)
    except:
        pass
    return ''


@register.filter('div_cols')
def div_cols(field):
    if not field.is_readonly:
        if 'cols' in field.field.form.Meta.model.__dict__ \
                and field.field.name in field.field.form.Meta.model.cols:
            return field.field.form.Meta.model.cols[field.field.name]
    else:
        if 'cols' in field.model_admin.model.__dict__ \
                and field.field['name'] in field.model_admin.model.cols:
            return field.model_admin.model.cols[field.field['name']]
    return 4


@register.filter('input_type')
def input_type(ob):
    '''
    Extract form field type
    :param ob: form field
    :return: string of form field widget type
    '''
    return ob.field.widget.__class__.__name__


@register.filter(name='add_classes')
def add_classes(value, arg):
    '''
    Add provided classes to form field
    :param value: form field
    :param arg: string of classes seperated by ' '
    :return: edited field
    '''
    css_classes = value.field.widget.attrs.get('class', '')
    # check if class is set or empty and split its content to list (or init list)
    if css_classes:
        css_classes = css_classes.split(' ')
    else:
        css_classes = []
    # prepare new classes to list
    args = arg.split(' ')
    for a in args:
        if a not in css_classes:
            css_classes.append(a)
    # join back to single string
    return value.as_widget(attrs={'class': ' '.join(css_classes)})

@register.filter
def sexo_str(value):
    result = ''
    if value == 1:
        result = 'Masculino'
    if value == 2:
        result = 'Feminino'
    if value == 3:
        result = 'Indefinido'
    return result

@register.filter
def label_status_edital(value):
    result = ''
    if value == 1:
        result = 'Em aberto'
    if value == 2:
        result = 'Publicado'
    return result

@register.filter
def get_number_edital(value):
    result = ''
    value = value.lower()
    value = value.split("-")
    result = value[0]

    return result

@register.filter
def get_description_edital(value):
    result = ''
    value = value.lower()
    if '-' in value:
        value = value.split("-")
        result = value[1]

    return result

@register.filter
def estar_inscrito_edital(value):
    result = ''
    if value == 1:
        result = 'sim'
    if value == 2:
        result = 'não'

    return result

@register.filter
def boolean_sim_ou_nao(value):
    result = ''
    if value or value == 1:
        result = 'Sim'
    if not value:
        result = 'Não'
    return result


@register.filter('to_str')
def to_str(int):
    return str(int)