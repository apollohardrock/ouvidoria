from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .models import Denuncia, AnexoDenuncia, Mensagem
from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Denuncia, AnexoDenuncia, Mensagem, AnexoMensagem
import os
from dotenv import load_dotenv

# 0. Carrega as variáveis do arquivo .env
load_dotenv()

CLIENT_NAME = os.getenv('CLIENT_NAME')

# =========================================================================
# 1. CONFIGURAÇÃO DOS INLINES
# =========================================================================
class AnexoDenunciaInline(admin.TabularInline):
    model = AnexoDenuncia
    extra = 0
    can_delete = False
    readonly_fields = ('link_download', 'enviado_em')
    fields = ('link_download', 'enviado_em')

    def link_download(self, obj):
        if obj.arquivo:
            return format_html(
                '<a href="{}" target="_blank" style="background-color: #F26522; color: white; padding: 6px 12px; border-radius: 20px; text-decoration: none; font-weight: bold; font-size: 12px; display: inline-block;">⬇ Baixar Anexo</a>',
                obj.arquivo.url
            )
        return "Sem arquivo"
    link_download.short_description = 'Arquivo Anexado'

# Componente para contornar a restrição de múltiplos arquivos nativa do Django
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        if isinstance(data, (list, tuple)):
            return [super(MultipleFileField, self).clean(d, initial) for d in data]
        return super(MultipleFileField, self).clean(data, initial)

class MensagemForm(forms.ModelForm):
    arquivos_multiplos = MultipleFileField(
        widget=MultipleFileInput(attrs={'multiple': True}),
        label='Adicionar Anexos',
        required=False
    )
    
    class Meta:
        model = Mensagem
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Verifica se é uma mensagem antiga (já salva no banco)
        if self.instance and self.instance.pk:
            # Se a mensagem foi enviada pelo DENUNCIANTE (usuario_admin é nulo)
            if not self.instance.usuario_admin:
                # Aplica o CSS invisível diretamente no HTML deste checkbox específico!
                self.fields['visivel_denunciante'].widget.attrs['style'] = 'display: none !important;'

class MensagemInline(admin.TabularInline):
    model = Mensagem
    form = MensagemForm
    extra = 1
    fields = ('exibir_remetente', 'texto', 'arquivos_multiplos', 'exibir_anexos_salvos', 'visivel_denunciante')
    readonly_fields = ('exibir_remetente', 'exibir_anexos_salvos')
    can_delete = False

    def exibir_remetente(self, obj):
        if obj and obj.pk:
            return "Equipe de Análise" if obj.usuario_admin else "Denunciante"
        return "Nova Anotação/Mensagem"
    exibir_remetente.short_description = "Remetente"

    def exibir_anexos_salvos(self, obj):
        if obj and obj.pk:
            anexos = obj.anexos.all()
            if anexos:
                links = [
                    format_html('<a href="{}" target="_blank" style="color: #0d47a1;">📎 Baixar Anexo {}</a>', a.arquivo.url, i+1) 
                    for i, a in enumerate(anexos)
                ]
                return mark_safe('<br>'.join(links))
        return "-"
    exibir_anexos_salvos.short_description = "Anexos Salvos"

# =========================================================================
# 2. CONFIGURAÇÃO DA DENÚNCIA PRINCIPAL
# =========================================================================
@admin.register(Denuncia)
class DenunciaAdmin(admin.ModelAdmin):
    change_form_template = 'admin/denuncias_change_form.html'
    
    list_display = ('protocolo', 'exibir_data_hora', 'exibir_identificacao', 'status')
    list_filter = ('status', 'anonimato', 'criado_em')
    search_fields = ('protocolo', 'descricao', 'nome')
    
    readonly_fields = (
        'protocolo', 'criado_em', 'atualizado_em', 'anonimato', 
        'testemunhas', 'descricao', 'nome', 'setor', 'telefone', 'email'
    )
    
    inlines = [AnexoDenunciaInline, MensagemInline] 
    
    fieldsets = (
        ('1. Controle da Advogada', {
            'fields': ('protocolo', 'status'),
            'description': 'Altere o status. Utilize o Chat abaixo para interagir com o denunciante.'
        }),
        ('2. Relato do Denunciante (Imutável)', {
            'fields': ('criado_em', 'descricao', 'testemunhas')
        }),
        ('3. Identificação', {
            'fields': ('anonimato', 'nome', 'setor', 'telefone', 'email'),
        }),
    )

    # Captura automática do usuário logado ao salvar mensagens
    def save_formset(self, request, form, formset, change):
        if formset.model == Mensagem:
            instancias = formset.save(commit=False)
            for instancia in instancias:
                if not instancia.pk:
                    instancia.usuario_admin = request.user
                instancia.save()
            formset.save_m2m()

            # MÁGICA: Captura múltiplos arquivos subidos no Admin
            for f_form in formset.forms:
                if f_form.is_valid() and f_form.instance.pk:
                    # O Django usa o prefixo do formset para capturar os arquivos corretos da linha
                    arquivos = request.FILES.getlist(f"{f_form.prefix}-arquivos_multiplos")
                    for f in arquivos:
                        AnexoMensagem.objects.create(mensagem=f_form.instance, arquivo=f)
        else:
            super().save_formset(request, form, formset, change)

    def save_model(self, request, obj, form, change):
        if change and obj.anonimato == 'nao' and obj.email and obj.email != 'Não informado':
            assunto = f"Atualização de Protocolo [{obj.protocolo}] - {CLIENT_NAME}"
            mensagem = "Olá, a sua manifestação teve uma nova movimentação. Acesse o canal para visualizar."
            try:
                send_mail(assunto, mensagem, settings.EMAIL_HOST_USER, [obj.email], fail_silently=True)
            except Exception:
                pass
        super().save_model(request, obj, form, change)

    # Utilitários de visualização
    def exibir_data_hora(self, obj):
        return obj.criado_em.strftime('%d/%m/%Y %H:%M')
    exibir_data_hora.short_description = 'Data e Hora'

    def exibir_identificacao(self, obj):
        return "Anônimo" if obj.anonimato == 'sim' else "Identificado"
    exibir_identificacao.short_description = 'Identificação'

    # Botão Voltar
    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        url_lista = reverse('admin:denuncias_denuncia_changelist')
        context['botao_voltar_inferior'] = format_html(
            '<a href="{}" class="button" style="background-color: #79aec8; color: white; padding: 0 15px; border-radius: 4px; text-decoration: none; text-transform: uppercase; font-size: 13px; font-weight: 500; display: inline-flex; align-items: center; justify-content: center; height: 35px; box-sizing: border-box; border: none; cursor: pointer;">⬅ Voltar para a Lista</a>',
            url_lista
        )
        return super().render_change_form(request, context, add, change, form_url, obj)

    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False

# =========================================================================
# 3. SEGURANÇA E LIMPEZA
# =========================================================================
admin.site.enable_nav_sidebar = False

# =========================================================================
# 4. GESTÃO DE ACESSOS (PROXY)
# =========================================================================
# Cria "atalhos" visuais para os modelos nativos do Django
class GestorUsuario(User):
    class Meta:
        proxy = True
        verbose_name = 'Usuário do Sistema'
        verbose_name_plural = '1. Usuários do Sistema'

class GestorGrupo(Group):
    class Meta:
        proxy = True
        verbose_name = 'Grupo de Permissão'
        verbose_name_plural = '2. Grupos de Permissão'

# Remove os antigos (se existirem) e regista os novos no nosso menu
try:
    admin.site.unregister(User)
    admin.site.unregister(Group)
except Exception:
    pass

admin.site.register(GestorUsuario, UserAdmin)
admin.site.register(GestorGrupo, GroupAdmin)