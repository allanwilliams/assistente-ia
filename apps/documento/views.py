from django.shortcuts import render
from apps.documento.models import Chat


# Create your views here.


def chat(request):
    chats = Chat.objects.filter(criado_por=request.user, ativo=True)
    context = {
        'chats': chats
    }

    return render(request, 'documento.html', context)