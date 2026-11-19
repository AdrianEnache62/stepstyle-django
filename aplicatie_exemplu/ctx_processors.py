from django.conf import settings

def date_firma(request):
    return {
        'firma': settings.DATE_FIRMA,
        'copyright': f"© 2026 {settings.DATE_FIRMA['nume']}. Toate drepturile rezervate.",
    }