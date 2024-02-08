from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from apps.django_sso_app.helpers import import_user
from datetime import datetime
import re

User = get_user_model()

def processar_usuarios_fusionauth(fusionauth_users,data): # pragma: no cover
    if len(fusionauth_users) > 0:
        result_import_fusion = import_user(fusionauth_users)
        if result_import_fusion:
            for result_error in result_import_fusion:
                for index, item in enumerate(data):
                    if item['email'] == result_error['user_email']:
                        data[index]['status'] = 'danger'
                        data[index]['status_mensagem'] = result_error['error']

    return data

def processar_linha_csv(row):
    nome = row[0]
    cpf = row[1]
    matricula = row[2]
    papel = row[3]
    username = row[4]
    email = row[5]
    grupo = row[6]
    staff = row[7]

    if not matricula:
        matricula: None
        
    result_data = {
        'nome': nome,
        'cpf': cpf,
        'matricula': matricula,
        'papel': papel,
        'username': username,
        'email': email,
        'grupo': grupo,
        'staff': True if staff == 'True' else False
    }

    cpf_clear = re.sub(r"\D", '', cpf)

    usuario_multi_existe = User.objects.filter(username=username.strip()).exists()
    email_existe = User.objects.filter(email=email.strip()).exists()
    
    matricula_multi_existe = False
    if matricula:
        matricula_multi_existe = User.objects.filter(matricula=matricula.strip()).exists()
    
    cpf_multi_existe = False
    if cpf_clear:    
        cpf_multi_existe =  User.objects.filter(cpf=cpf_clear.strip()).exists()

    if usuario_multi_existe or cpf_multi_existe or email_existe or matricula_multi_existe:
        result_data['status'] = 'danger'
        result_data['status_mensagem'] = 'Não importado. Já existe um usuário cadastrado com esse username, email, cpf ou matricula'
    else:
        password = '{}!U'.format(cpf_clear.strip()[:7])

        user_data = {
            'is_superuser': False,
            'username': username,
            'name': nome.title(),
            'first_name':  nome.split()[0] if len(nome.split()) > 0 else '',
            'last_name': nome.split()[-1] if len(nome.split()) > 1 else '',
            'email': email.strip(),
            'is_staff': staff,
            'is_active': True,
            'date_joined': datetime.now(),
            'password': password
        }
        
        if matricula:
            user_data['matricula'] = matricula
        
        if cpf_clear:
            user_data['cpf'] = cpf_clear

        user = User(**user_data)

        user.set_password(password)
        user.save()
        group = Group.objects.get(pk=grupo)
        user.groups.add(group)
        if grupo:
            user_data['grupo_id'] = grupo

        return {
            'user_data': user_data,
            'result_data': result_data
        }
    return {
        'user_data':{},
        'result_data':result_data
    }