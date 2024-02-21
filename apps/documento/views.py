from django.shortcuts import render
from apps.documento.models import Chat


def chat(request):
    documento = request.GET.get('documento')
    context = {}
    if documento:
        chat = Chat.objects.filter(pk=documento).first()
        context = {
            'chat':chat
        }
        return render(request, 'chat.html',context=context)
    
    return render(request, 'chat.html',context=context)


def dashboard(request):
    chats = Chat.objects.filter(criado_por=request.user, ativo=True)
    context = {
        'chats': chats
    }

    return render(request, 'dashboard.html', context)