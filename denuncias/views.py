import uuid
from datetime import datetime
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .models import Denuncia, AnexoDenuncia, Mensagem, AnexoMensagem
import os
from dotenv import load_dotenv

# 1. Carrega as variáveis do arquivo .env
load_dotenv()

CLIENT_NAME = os.getenv('CLIENT_NAME')

def inicio(request):
    if request.method == 'POST':
        # 1. Capturar os dados básicos do formulário
        anonimato = request.POST.get('anonimato')
        testemunhas = request.POST.get('testemunhas', 'Não informadas')
        descricao = request.POST.get('descricao', '')

        # 2. Gerar número de protocolo seguro (Ex: APL-20890615-A1B2C3D4E5)
        data_atual = datetime.now().strftime('%Y%m%d')
        codigo_unico = str(uuid.uuid4().hex)[:10].upper()
        protocolo = f"APL-{data_atual}-{codigo_unico}"

        # 3. Salvar a Denúncia no Banco de Dados
        nova_denuncia = Denuncia(
            protocolo=protocolo,
            anonimato=anonimato,
            testemunhas=testemunhas,
            descricao=descricao,
        )

        # Se não for anônimo, preenchemos os dados de identificação antes de salvar
        if anonimato == 'nao':
            nova_denuncia.nome = request.POST.get('nome', 'Não informado')
            nova_denuncia.setor = request.POST.get('setor', 'Não informado')
            nova_denuncia.telefone = request.POST.get('telefone', 'Não informado')
            nova_denuncia.email = request.POST.get('email', 'Não informado')

        nova_denuncia.save() # Salva definitivamente no banco (models)

        # 4. Salvar os Anexos no Banco de Dados (relacionados à denúncia)
        if request.FILES:
            arquivos = request.FILES.getlist('arquivo')
            
            # --- DEBUG ---
            print(f"QUANTIDADE DE ARQUIVOS RECEBIDOS: {len(arquivos)}") 
            # -------------
            
            for f in arquivos:
                # Cria um registro na tabela AnexoDenuncia para cada arquivo
                AnexoDenuncia.objects.create(denuncia=nova_denuncia, arquivo=f)

        # 5. Montar e Enviar E-mail de Notificação para a Advogada
        assunto = f'[NOVA DENÚNCIA] Protocolo gerado: {protocolo}'
        dominio_atual = request.get_host() 
        link_painel = f"http://{dominio_atual}/admin/"

        corpo_notificacao = f"""Olá,

            Uma nova denúncia foi registrada no Canal de Ouvidoria da {CLIENT_NAME}.

            Protocolo: {protocolo}
            Status: Recebida - Aguardando Análise

            Por questões de segurança e confidencialidade, os detalhes da denúncia e os anexos não são enviados por e-mail.

            Para visualizar o conteúdo completo, analisar os arquivos e responder ao denunciante, acesse o painel administrativo através do link abaixo:
            {link_painel}

            Atenciosamente,
            Sistema Automático - Projeto Canal de Ouvidoria
            """

        try:
            send_mail(
                assunto,
                corpo_notificacao,
                settings.EMAIL_HOST_USER,
                settings.DESTINATARIOS_ADMIN,  # <--- NOVA LISTA AQUI
                fail_silently=False,
            )
        except Exception as e:
            pass

        # 6. NOVA LÓGICA: Enviar recibo para o usuário se ele se identificou
        if anonimato == 'nao' and nova_denuncia.email and nova_denuncia.email != 'Não informado':
            assunto_usuario = f"Protocolo Seguro: {protocolo} - {CLIENT_NAME}"
            mensagem_usuario = (
                f"Olá {nova_denuncia.nome},\n\n"
                f"Recebemos sua denúncia em nosso Canal Seguro.\n"
                f"Seu número de protocolo para acompanhamento é: {protocolo}\n\n"
                f"Você será notificado por este e-mail sempre que houver uma movimentação ou "
                f"resposta da nossa equipe de análise independente.\n\n"
                f"Sua voz importa.\n"
                f"Equipe {CLIENT_NAME}"
            )
            try:
                # Dispara o e-mail para o usuário
                send_mail(
                    assunto_usuario, 
                    mensagem_usuario, 
                    settings.EMAIL_HOST_USER, 
                    [nova_denuncia.email], 
                    fail_silently=True
                )
            except Exception:
                pass

        # 7. Renderizar a tela de sucesso passando o protocolo
        return render(request, 'sucesso.html', {'protocolo': protocolo})
            
    # Se for GET, apenas mostra o form
    return render(request, 'index.html')


def acompanhar_protocolo(request):
    protocolo_digitado = request.POST.get('protocolo') or request.GET.get('protocolo')
    denuncia = None
    erro = None
    mensagens = []

    if protocolo_digitado:
        protocolo_digitado = protocolo_digitado.strip()
        denuncia = Denuncia.objects.filter(protocolo=protocolo_digitado).first()
        
        if not denuncia:
            erro = "Número de protocolo não encontrado. Verifique se digitou corretamente."
        else:
            # 1. TENTA SALVAR A NOVA MENSAGEM
            if request.method == "POST" and 'nova_mensagem' in request.POST:
                texto = request.POST.get('mensagem_texto', '').strip()
                arquivo_enviado = request.FILES.get('mensagem_arquivo')
                
                if texto or request.FILES:
                    nova_msg = Mensagem.objects.create(
                        denuncia=denuncia,
                        texto=texto
                    )
                    arquivos = request.FILES.getlist('mensagem_arquivos')
                    for f in arquivos:
                        AnexoMensagem.objects.create(mensagem=nova_msg, arquivo=f)

                    # --- NOVA LÓGICA DE E-MAIL: AVISAR A ADVOGADA SOBRE A NOVA MENSAGEM ---
                    dominio_atual = request.get_host() 
                    link_painel = f"https://{dominio_atual}/admin/" # Idealmente usando https em produção
                    assunto_chat = f"[ATUALIZAÇÃO DE PROTOCOLO] Nova mensagem: {denuncia.protocolo}"
                    
                    corpo_chat = f"""Olá,

                        O denunciante adicionou uma nova informação ou anexo ao protocolo {denuncia.protocolo}.

                            Acesse o painel de controle para visualizar a nova interação e responder:
                            {link_painel}

                            Atenciosamente,
                            Ouvidoria {CLIENT_NAME}
                            """
                    try:
                        send_mail(
                            assunto_chat,
                            corpo_chat,
                            settings.EMAIL_HOST_USER,
                            settings.DESTINATARIOS_ADMIN,  # <--- NOVA LISTA AQUI
                            fail_silently=True,
                        )
                    except Exception:
                        pass
                    # ----------------------------------------------------------------------

                    return redirect(f"/acompanhar/?protocolo={protocolo_digitado}")

            # 2. TENTA BUSCAR O HISTÓRICO PARA MOSTRAR NA TELA
            # Substituímos 'data_criacao' por 'criado_em'
            mensagens = Mensagem.objects.filter(denuncia=denuncia).order_by('criado_em')

    return render(request, 'acompanhar.html', {
        'denuncia': denuncia,
        'erro': erro,
        'protocolo': protocolo_digitado,
        'mensagens': mensagens
    })

def politica_confidencialidade(request):
    return render(request, 'politica.html')