from apps.core.mixins import GenericCrud
from apps.contrib.models import Municipios

municipio_views = GenericCrud(
    namespace='municipio',
    model=Municipios,
    label='Municipios',
    parent_column='estado',
    list_fields=('id','nome'),
    form_fields= {
        'id': {
            'class':'col-md-3'
        },
        'estado': {
            'class':'col-md-3'
        },
        'nome': {
            'class':'col-md-6'
        }
    },
    view_fields=('id','nome')
)