from .models import Sifaris, Kateqoriya, Firma, Avtomobil, Header_Message
from django.http import Http404
from django.conf import settings
from .views import custom_404
from django.shortcuts import render

class GlobalDataMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Bütün aktiv mesajları əldə et
        request.header_messages = Header_Message.objects.filter(aktiv=True).order_by('id')

        if request.user.is_authenticated:
            # Ümumi borcu əldə edirik
            statistics = Sifaris.get_order_statistics(request.user)
            request.statistics = statistics

            # Axtarış üçün lazım olan məlumatları əldə edirik
            request.categories = Kateqoriya.objects.all()
            request.brands = Firma.objects.all()
            request.models = Avtomobil.objects.all()

        response = self.get_response(request)
        return response 

class Custom404Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 404 and settings.DEBUG:
            return custom_404(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, Http404) and settings.DEBUG:
            return custom_404(request)
        return None 
    

from django.utils.deprecation import MiddlewareMixin

class AdminFaviconMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # yalnız admin HTML response-lara tətbiq et
        if request.path.startswith('/admin/') and getattr(response, 'get', None):
            content_type = response.get('Content-Type', '')
            if 'text/html' in content_type:
                try:
                    content = response.content.decode('utf-8')
                except Exception:
                    return response

                if '</head>' in content:
                    favicon_tag = '<link rel="icon" type="image/png" href="/static/images/favicon.png">'
                    if favicon_tag not in content:
                        content = content.replace('</head>', f'{favicon_tag}</head>')
                        response.content = content.encode('utf-8')

        return response