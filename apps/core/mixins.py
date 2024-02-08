from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.decorators import login_required, permission_required
from django.db import models
from django.forms import Textarea
from django.utils import timezone
from django.shortcuts import render, redirect
from django_currentuser.middleware import get_current_user, get_current_authenticated_user
from django.http import HttpResponse,HttpResponseRedirect
from django.urls import reverse, path
from reversion.admin import VersionAdmin
from apps.core.encrypt_url_utils import encrypt
from apps.core.utils import core_decrypt, core_encrypt,format
from apps.core.permission_functions import permission_required_for_model_view,permission_required_for_user_view
from reversion import register
from reversion.revisions import is_active, set_comment
import reversion
import json
import decimal
import inspect

LIST_PER_PAGE = 10

@register
class BaseModel(models.Model):
    criado_em = models.DateTimeField(blank=True, null=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.DO_NOTHING,
                                   related_name='%(class)s_criado_por',
                                   blank=True,
                                   null=True,
                                   default=get_current_user())
    modificado_em = models.DateTimeField(blank=True, null=True)
    modificado_por = models.ForeignKey(settings.AUTH_USER_MODEL,
                                       on_delete=models.DO_NOTHING,
                                       related_name='%(class)s_modificado_por',
                                       blank=True,
                                       null=True)

    crypted_fields = []
    masked_fields = []

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        original = self._meta.model.objects.filter(pk=self.pk).first()
            
        if get_current_authenticated_user():
            if self.pk is None:
                if not self.criado_por or not self.criado_em:
                    self.criado_por = get_current_authenticated_user()
                    self.criado_em = timezone.now()
            elif original:
                    self.modificado_por = get_current_authenticated_user()
                    self.modificado_em = timezone.now()
                    self.criado_em = original.criado_em
                    self.criado_por = original.criado_por
        
        for crypted_field in self.crypted_fields:
            new_value = core_encrypt(getattr(self, crypted_field))
            setattr(self, crypted_field, new_value)
        
        with reversion.create_revision():
            comment = []
            if original and self._meta.model_name not in ['userpage','usersession']:
                try:
                    changed_fields = []
                    for field in self._meta.fields:
                        field_name = f'{field.name}_id' if isinstance(field, models.ForeignKey) else field.name
                        if field_name not in ['criado_por_id','criado_por','criado_em','modificado_por','modificado_por_id','modificado_em']:
                            field_value = getattr(self, field_name)
                            original_value = getattr(original, field_name)
                            if field_value != original_value:
                                changed_fields.append(field_name)
                    if len(changed_fields) > 0:
                        comment = [{"changed": {"fields": changed_fields}}]
                except Exception: pass                
            
            reversion.set_comment(json.dumps(comment))
            reversion.set_user(get_current_authenticated_user())
            super(BaseModel, self).save(*args, **kwargs)
    
    def get_encrypt_id(self):
        return encrypt(self.id)
    
    @classmethod
    def from_db(cls, db, field_names, values):
        for crypted_field in cls.crypted_fields:
            index = field_names.index(crypted_field)
            new_value = core_decrypt(values[index])
            new_values = list(values)
            new_values[index] = new_value
            values = tuple(new_values)
        return super().from_db(db, field_names, values)


class BaseModelDRF(models.Model):
    criado_em = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.DO_NOTHING,
                                   related_name='%(class)s_criado_por',
                                   blank=True,
                                   null=True)
    modificado_em = models.DateTimeField(blank=True, null=True, auto_now=True)
    modificado_por = models.ForeignKey(settings.AUTH_USER_MODEL,
                                       on_delete=models.DO_NOTHING,
                                       related_name='%(class)s_modificado_por',
                                       blank=True,
                                       null=True)

    class Meta:
        abstract = True


class AuditoriaAdmin(VersionAdmin):
    # def changelist_view(self, request, extra_context=None):
    #     response = super().changelist_view(request, extra_context=extra_context)
    #     result_list = response.context_data['cl'].result_list
    #     if self.model.masked_fields:
    #         for obj in result_list:
    #             for field in self.model.masked_fields:
    #                 setattr(obj,field,eval(self.model.masked_fields[field]['function'])(getattr(obj,field),''))
        
    #     response.context_data['cl'].result_list = result_list

    #     return response

    def log_change(self, request, object, message):
        entry = super().log_change(request, object, message)
        if is_active():
            set_comment(entry.change_message)
        return entry


    def log_addition(self, request, object, message):
        change_message = message or ("Initial version.")
        entry = super().log_addition(request, object, change_message)
        if is_active():
            set_comment(entry.change_message)
        return entry

    readonly_fields = (
        'criado_em',
        'criado_por',
        'modificado_em',
        'modificado_por',
    )
    list_per_page = LIST_PER_PAGE


class AuditoriaAdminInline(admin.TabularInline):
    readonly_fields = (
        'criado_em',
        'criado_por',
        'modificado_em',
        'modificado_por',
    )
    list_per_page = LIST_PER_PAGE
    formfield_overrides = {
        models.TextField: {
            'widget': Textarea(attrs={
                'rows': 8,
                'cols': 40
            })
        },
        models.ForeignKey: {
            # 'widget': Select(attrs={'style': 'max-width: 150px'})
        },
        models.CharField: {
            # 'widget': TextInput(attrs={'style': 'max-width: 150px'})
        },
    }

class AuditoriaAdminStackedInlineInline(admin.StackedInline):
    readonly_fields = (
        'criado_em',
        'criado_por',
        'modificado_em',
        'modificado_por',
    )
    list_per_page = LIST_PER_PAGE


class BooleanDefaultNoFilter(SimpleListFilter):

    def lookups(self, request, model_admin):
        return (
            ('tudo', 'Tudo'),
            ('sim', 'Sim'),
            ('nao', 'Não'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'nao':
            dic = {self.parameter_name: False}
            return queryset.filter(**dic)
        elif self.value() == 'sim':
            dic = {self.parameter_name: False}
            return queryset.exclude(**dic)
        return queryset

class DecimalEncoder(json.JSONEncoder):
    def default(self, item):
        if isinstance(item, decimal.Decimal):
            return float(item)
        return super(DecimalEncoder, self).default(item)

def compact(*names):
    caller = inspect.stack()[1][0]
    result = {}

    for n in names:
        if n in caller.f_locals:
            result[n] = caller.f_locals[n]
        elif n in caller.f_globals:
            result[n] = caller.f_globals[n]
    return result

class GenericCrud:
    def __init__(self,namespace, model, label, parent_column, list_fields, form_fields, view_fields):
        self.namespace = namespace
        self.model = model
        self.label = label
        self.list_fields = list_fields
        self.form_fields = form_fields
        self.view_fields = view_fields
        self.parent_column = parent_column
        self.form = self.get_form()

        self.CRIADO_SUCESSO = f'{self.label} criada com sucesso!'
        self.ERRO_INTERNO = f'Erro interno ao criar {self.label}!'
        self.EDITADO_SUCESSO = f'{self.label} editada com sucesso!'
        self.ERRO_EDITAR = f'Erro ao editar {self.label}!'
        self.VINCULO_INEXISTENTE = "Usuário sem vinculo contratual!"
    
    def visualizar(self,request, pk, parent_id=None):
        if pk:
            instance_object = self.model.objects.filter(pk=pk).first()
            
        context = {
            'instance_object': instance_object,
            'crud': self
        }
        
        if parent_id:
            context['parent_id'] = parent_id

        return render(request, 'generic_crud/visualizar.html', context)
    
    def criar(self,request,parent_id=None):
        form = self.form

        if request.method == 'POST':
            form = self.form(request.POST, request.FILES)
            
            if form.is_valid():
                try:
                    instance_object = form.save()
                    if request.is_ajax(): # pragma: no cover
                        return HttpResponse(json.dumps({'mensagem': self.CRIADO_SUCESSO}), status=200, content_type="application/json")
                except Exception: # pragma: no cover
                    return HttpResponse(json.dumps({'mensagem': self.ERRO_INTERNO}), status=500, content_type="application/json")
                
                messages.success(request, self.CRIADO_SUCESSO)
                return redirect(f'/{self.model._meta.app_label}/{self.namespace}-visualizar/{instance_object.id}')
            else:
                if request.is_ajax(): # pragma: no cover
                    errors = dict(form.errors.items())
                    return HttpResponse(json.dumps(errors), status=400, content_type="application/json")
        
        context = {
            'form': form,
            'parent_id': parent_id,
            'crud': self
        }

        if parent_id:
            context['parent_id'] = parent_id

        return render(request, 'generic_crud/criar.html', context)

    def editar(self,request, pk,parent_id=None):
        instance_object = self.model.objects.filter(pk=pk).first()
        
        form = self.form(request.POST or None, request.FILES or None, instance=instance_object)
        
        if request.method == 'POST' and form.is_valid():
            try:
                form.save()
                messages.success(request, self.EDITADO_SUCESSO)
            except Exception: # pragma: no cover
                if request.is_ajax(): # pragma: no cover
                    return HttpResponse(json.dumps(dict(form.errors.items())), status=400, content_type='application/json')        
                messages.error(request, self.ERRO_EDITAR)

            return redirect(f'/{self.model._meta.app_label}/{self.namespace}-visualizar/{instance_object.id}')
        else:
            if request.is_ajax():# pragma: no cover
                errors = dict(form.errors.items())
                return HttpResponse(json.dumps(errors), status=400, content_type="application/json")

        context = {
            'parent_id': parent_id,
            'form': form,
            'instance_object': instance_object,
            'crud': self
        }

        if parent_id:
            context['parent_id'] = parent_id

        return render(request, 'generic_crud/editar.html', context)

    def excluir(self, request, pk, parent_id=None):
        
        instance_object = self.model.objects.filter(pk=pk).first()
        
        if instance_object:
            try:
                instance_object.delete()
                messages.success(request, f'{self.label} removido com sucesso!')
            except Exception: # pragma: no cover
                messages.error(request, f'Não foi possivel remover a {self.label}!')


        return HttpResponseRedirect(reverse('terceirizados:visualizar_terceirizado', args=[parent_id]))
    

    def get_urls(self):
        return [
            path(f"{self.namespace}-criar/", self.criar, name=f'{self.namespace}_criar'),
            path(f"{self.namespace}-criar/<parent_id>/", self.criar, name=f'{self.namespace}_criar'),

            path(f"{self.namespace}-visualizar/<pk>/<parent_id>/", self.visualizar, name=f'{self.namespace}_visualizar'),
            path(f"{self.namespace}-visualizar/<pk>/", self.visualizar, name=f'{self.namespace}_visualizar'),

            path(f"{self.namespace}-editar/<pk>/<parent_id>/", self.editar, name=f'{self.namespace}_editar'),
            path(f"{self.namespace}-editar/<pk>/", self.editar, name=f'{self.namespace}_editar'),

            path(f"{self.namespace}-excluir/<pk>/<parent_id>/", self.excluir, name=f'{self.namespace}_excluir'),
            path(f"{self.namespace}-excluir/<pk>/", self.excluir, name=f'{self.namespace}_excluir'),
        ]

    def get_form(self):
        class Meta:
            model = self.model
            fields = self.get_form_fields()
            label_form = self.label

        def __init__(self, *args, **kwargs):
            super(GenericForm, self).__init__(*args, **kwargs)
            for field in self.fields:
                self.fields[field].widget.attrs['class'] = 'vTextField'

        # Cria uma nova classe de formulário usando type
        GenericForm = type('GenericForm', (forms.ModelForm,), {'Meta': Meta,'__init__': __init__})

        return GenericForm

    def get_form_fields(self):
        return list(self.form_fields.keys())