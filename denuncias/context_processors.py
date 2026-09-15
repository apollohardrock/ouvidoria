from django.conf import settings

def dados_cliente(request):
    """
    Injeta o nome e a logo do cliente de forma global em todos os templates HTML.
    """
    return {
        'CLIENT_NAME': settings.CLIENT_NAME,
        'CLIENT_LOGO_URL': settings.CLIENT_LOGO_URL
    }