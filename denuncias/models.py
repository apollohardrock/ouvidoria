from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
import os

# Lista de formatos permitidos para todos os arquivos do sistema
FORMATOS_VALIDOS = ['pdf', 'jpg', 'jpeg', 'png', 'docx', 'mp4', 'wav', 'mp3', 'm4a', 'aac', 'ogg']

def caminho_anexos_cliente(instance, filename):
    # Puxa o nome do cliente do .env e formata tirando os espaços
    nome_cliente = settings.CLIENT_NAME.replace(" ", "_").lower()
    
    # Organiza em subpastas: se for da denúncia principal ou do chat
    if hasattr(instance, 'denuncia'):
        subpasta = 'provas_iniciais'
    else:
        subpasta = 'chat_interacoes'
        
    # O caminho final ficará: skyglass_canela/provas_iniciais/arquivo.pdf
    return f'{nome_cliente}/{subpasta}/{filename}'

class Denuncia(models.Model):
    STATUS_CHOICES = [
        ('Em Análise', 'Em Análise'),
        ('Determinado o processamento de sindicância interna','Determinado o processamento de sindicância interna'),
        ('Determinado o arquivamento sumário por falta de informações ou ausência de objeto passível de sindicância','Determinado o arquivamento sumário por falta de informações ou ausência de objeto passível de sindicância'),
        ('Pendente de Diligência', 'Pendente de Diligência'),
        ('Abertura de Sindicância', 'Abertura de Sindicância'),
        ('Concluída / Finalizada', 'Concluída / Finalizada'),
        ('Encerrada', 'Encerrada'),
    ]

    protocolo = models.CharField(max_length=30, unique=True, verbose_name="Número do Protocolo")
    anonimato = models.CharField(max_length=3, choices=[('sim', 'Sim'), ('nao', 'Não')], default='sim')
    testemunhas = models.TextField(blank=True, null=True, verbose_name="Testemunhas")
    descricao = models.TextField(verbose_name="Descrição do Ocorrido")
    
    nome = models.CharField(max_length=150, blank=True, null=True, verbose_name="Nome do Denunciante")
    setor = models.CharField(max_length=100, blank=True, null=True, verbose_name="Setor")
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail")
    
    status = models.CharField(max_length=150, choices=STATUS_CHOICES, default='RECEBIDA', verbose_name="Status da Denúncia")
    resposta_advogada = models.TextField(blank=True, null=True, verbose_name="Atualização / Parecer para o Denunciante")
    
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Envio")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    class Meta:
        ordering = ['-criado_em']
        verbose_name = "Denúncia"
        verbose_name_plural = "Denúncias"

    def __str__(self):
        return f"Protocolo: {self.protocolo} - Status: {self.get_status_display()}"

class AnexoDenuncia(models.Model):
    denuncia = models.ForeignKey(Denuncia, related_name='anexos', on_delete=models.CASCADE)
    arquivo = models.FileField(upload_to=caminho_anexos_cliente)
    enviado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Anexo da Denúncia {self.denuncia.protocolo} ({self.arquivo.name})"
    
class Mensagem(models.Model):
    denuncia = models.ForeignKey(Denuncia, related_name='mensagens', on_delete=models.CASCADE)
    usuario_admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    texto = models.TextField('Mensagem/Anotação', blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    # Substitui o antigo anexo_visivel_denunciante. Agora controla a MENSAGEM INTEIRA
    visivel_denunciante = models.BooleanField(
        default=True, 
        verbose_name="Visível para o Denunciante?"
    )

    class Meta:
        verbose_name = 'Mensagem do Chat'
        verbose_name_plural = 'Mensagens do Chat'
        ordering = ['criado_em']

    def __str__(self):
        try:
            if self.usuario_admin:
                return f"Equipe ({self.usuario_admin.username}) - {self.criado_em.strftime('%d/%m')}"
            return f"Denunciante - {self.criado_em.strftime('%d/%m')}"
        except:
            return "Mensagem"


class AnexoMensagem(models.Model):
    mensagem = models.ForeignKey(Mensagem, related_name='anexos', on_delete=models.CASCADE)
    arquivo = models.FileField(upload_to=caminho_anexos_cliente)

@receiver(post_save, sender=Mensagem)
def notificar_denunciante_resposta(sender, instance, created, **kwargs):
    """
    Este gatilho dispara automaticamente sempre que uma nova Mensagem é guardada.
    Se a mensagem for nova e for enviada por um Administrador (Advogada/Diretor),
    ele dispara um e-mail para o Denunciante.
    """
    if created and instance.usuario_admin:
        denuncia = instance.denuncia
        
        # Só envia e-mail se o denunciante não for anónimo e tiver preenchido e-mail
        if denuncia.anonimato == 'nao' and denuncia.email and denuncia.email != 'Não informado':
            assunto = f"[ATUALIZAÇÃO] Nova resposta no seu Protocolo {denuncia.protocolo}"
            mensagem = (
                f"Olá {denuncia.nome},\n\n"
                f"A equipe de Análise & Compliance da Skyglass Canela acabou de enviar uma nova mensagem "
                f"no seu protocolo: {denuncia.protocolo}.\n\n"
                f"Para ler a resposta, baixar eventuais anexos e continuar a interagir com a equipa, aceda ao nosso portal seguro:\n"
                f"https://ouvidoria.skyglasscanela.com.br/acompanhar\n\n"
                f"A sua voz importa e estamos a cuidar do seu relato com total confidencialidade.\n\n"
                f"Atenciosamente,\n"
                f"Equipa Skyglass Canela"
            )
            try:
                send_mail(
                    assunto,
                    mensagem,
                    settings.EMAIL_HOST_USER,
                    [denuncia.email],
                    fail_silently=True
                )
            except Exception:
                pass