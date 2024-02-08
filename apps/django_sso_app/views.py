from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.views.decorators.http import require_http_methods
from apps.django_sso_app.forms import AdminPasswordChangeForm

@require_http_methods(["GET","POST"])
def change_password(request):
    form = AdminPasswordChangeForm(request.user)
    
    if request.method == 'POST':
        form = AdminPasswordChangeForm(request.user,request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Senha atualizada com sucesso')
            return redirect('/admin/')

    context = {
        'form': form
    }

    return render(request,'django_sso_app/sso_change_password.html',context)

@require_http_methods(["GET"])
def login(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            if request.user.is_staff:
                return redirect('/admin/')
            else:
                return redirect('django_sso_unauthorized')
        return redirect('oidc_authentication_init')
    
@require_http_methods(["GET"])
def unauthorized(request):
    if request.method == 'GET':
        auth.logout(request)
        return render(request,'django_sso_app/unauthorized.html')