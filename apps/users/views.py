from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required,permission_required
from django.contrib.auth.models import Group
from django.contrib import messages
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from apps.users.forms import ImportarUsuariosForm, PerfilForm
from apps.users.models import Papeis
from apps.users.helpers import processar_usuarios_fusionauth
import os
import csv

User = get_user_model()

@login_required
@permission_required("users.add_user", raise_exception=True)
def importar_usuarios(request):
    result_context = return_context(request)    

    context = result_context['context']
    template = result_context['template']

    return render(request, template, context)

def return_context(request):
    mensagem = ''
    if request.method == "POST":
        form = ImportarUsuariosForm(request.POST, request.FILES)
        if form.is_valid():
            arquivo = request.FILES['file']
            fs = FileSystemStorage()
            filename = fs.save(arquivo.name, arquivo )
            uploaded_file_url = fs.url(filename)
            diretorio = os.path.dirname(os.path.dirname(filename))
            diretorio_arquivo = '{}{}{}'.format(settings.BASE_DIR,diretorio,uploaded_file_url)

            csv_data = processar_csv(diretorio_arquivo)
            data = csv_data['data']
            fusionauth_users = csv_data['fusionauth_users']

            if len(fusionauth_users) > 0: # pragma: no cover
                data = processar_usuarios_fusionauth(fusionauth_users,data)

            fs.delete(arquivo.name)
            mensagem = 'Upload realizado com sucesso!'
            
    papeis = Papeis.objects.all()
    grupos = Group.objects.all()

    context = {
        'texto': mensagem,
        'planilha': data,
        'papeis': papeis,
        'grupos': grupos,
    }

    return {
        'context': context,
        'template': 'importar_usuarios.html'
    }

def processar_csv(diretorio_arquivo):
    from apps.users.helpers import processar_linha_csv
    data = []
    fusionauth_users = []
    with open(diretorio_arquivo, encoding='utf-8') as f:
        csv_reader = csv.reader(f, delimiter=';')
        csv_reader.__next__()
        for row in csv_reader:
            result = processar_linha_csv(row)
            if result:
                if settings.USE_FUSIONAUTH: # pragma: no cover
                    if result['user_data']:
                        fusionauth_users.append(result['user_data'])

                result_data = result['result_data']
                data.append(result_data)
    return {
        'data':data,
        'fusionauth_users': fusionauth_users
    }

@login_required
def user_perfil(request, id):
    user =  User.objects.filter(pk=request.user.id).first()
    if id and id != 0:
        user = User.objects.filter(pk=id).first()
    if user:
        form = PerfilForm(request.POST or None, request.FILES or None, instance=user)
        
        if request.method == 'POST':
            if form.is_valid():
                try:
                    form.save()
                    messages.success(request, 'Usuário atualizado com sucesso!')
                except Exception: # pragma: no cover
                    messages.error(request, 'Erro ao atualizar Usuário!')

                return redirect(f'/users/perfil/{id}')

        context = {
            'form': form,
            'user': user,
            'editavel': request.user.id == user.id or request.user.is_superuser,
        }
        
        return render(request, 'perfil/user_perfil.html', context)
    messages.error(request, 'Usuário não localizado!') # pragma: no cover
    return redirect('/') # pragma: no cover