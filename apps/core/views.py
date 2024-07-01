from django.shortcuts import redirect,render
from constance import config
from django.conf import settings

def dash(request):
    return redirect(settings.DASHBOARD)

def dash_blog(request):
    return render(request,'dash_blog.html')