from apps.core.mixins import GenericCrud
from apps.contrib.models import Estados

estados_views = GenericCrud(
    namespace='estados',
    model=Estados,
    label='Estados',
    parent_column=None,
    list_fields=('id','nome'),
    form_fields= {
        'id': {
            'class':'col-md-3'
        },
        'nome': {
            'class':'col-md-6'
        }
    },
    view_fields=('id','nome')
)