from django.core.exceptions import PermissionDenied
from django.http import Http404

def permission_required_for_user_view(view_func): 
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser and request.user.papel.titulo != 'RH':
            terceirizado_id = kwargs.get('terceirizado_id') # pragma no cover

            if terceirizado_id != str(request.user.id): # pragma no cover
                raise PermissionDenied()

        return view_func(request, *args, **kwargs)

    return wrapper

def permission_required_for_model_view(model_instance,attr_id):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_superuser and request.user.papel.titulo != 'RH': # pragma no cover
                object_id = kwargs.get(attr_id)
                
                object = model_instance.objects.filter(id=object_id) # pragma no cover
                if object:
                    if object[0].user != request.user:
                        raise PermissionDenied('teste')
                else: # pragma no cover
                    raise Http404

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator