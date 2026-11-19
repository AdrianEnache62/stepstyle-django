from django.contrib import admin
from .models import (
    Categorie,
    Brand,
    ImaginePrincipala,
    Marime,
    Material,
    Promotie,
    Produs,
)

admin.site.register(Categorie)
admin.site.register(Brand)
admin.site.register(ImaginePrincipala)
admin.site.register(Marime)
admin.site.register(Material)
admin.site.register(Promotie)
admin.site.register(Produs)