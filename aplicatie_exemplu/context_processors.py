from django.db.models import Count
from .models import Categorie


def categorii_meniu(request):
    categorii = Categorie.objects.annotate(nr_produse=Count('produse')).filter(nr_produse__gt=0)
    return {'categorii_meniu': categorii}