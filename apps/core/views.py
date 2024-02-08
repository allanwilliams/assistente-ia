from django.shortcuts import redirect,render
from constance import config

def dash(request):
    return redirect(config.DASHBOARD)

def dash_blog(request):
    return render(request,'dash_blog.html')