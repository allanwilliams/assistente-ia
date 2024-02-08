from django.contrib.admin import site

def custom_context(request):
    return {"available_apps": site.each_context(request).get("available_apps")}