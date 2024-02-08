from ajax_select import register, LookupChannel
from apps.contrib.models import Municipios

@register('municipios')
class MunicipiosLookup(LookupChannel): # pragma: no cover
    model = Municipios

    def get_query(self, q, request):
        return self.model.objects.\
            filter(municipio_estado__icontains=q).\
            order_by('municipio_estado')[:50]

    def format_item_display(self, item):
        return "{}".format(item.municipio_estado)