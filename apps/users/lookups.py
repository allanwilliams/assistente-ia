from ajax_select import register, LookupChannel
from apps.users.models import User

@register('users_lembretes')
class UserLembreteLookup(LookupChannel): # pragma: no cover
    model = User

    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q, is_staff=True).order_by('name')[:20]

    def format_item_display(self, item):
        return "{} - {}".format(item.name.upper(), item.papel)    
    
    def format_match(self, item):
        return "{} - {}".format(item.name.upper(), item.papel)