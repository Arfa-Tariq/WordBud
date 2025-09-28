from django.utils.timezone import now

def current_year(request):
    return {'now': now()}