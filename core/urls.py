# core/urls.py
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from denuncias.views import inicio, acompanhar_protocolo, politica_confidencialidade
from django.contrib.auth import views as auth_views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', RedirectView.as_view(url='/admin/denuncias/denuncia/', permanent=False)),
    path('', inicio, name='inicio'),
    path('acompanhar/', acompanhar_protocolo, name='acompanhar'),
    path('politica/', politica_confidencialidade, name='politica'),

    # Rotas oficiais de recuperação de senha do Django (Obrigatórias para o botão funcionar)
    path('admin/password_reset/', auth_views.PasswordResetView.as_view(
        success_url='/admin/password_reset/done/'
    ), name='admin_password_reset'),
    
    path('admin/password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Rota do admin deve vir por último
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)