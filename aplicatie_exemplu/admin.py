import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from .models import (
    Departament,
    TipMesaj,
    Categorie,
    Brand,
    ImaginePrincipala,
    Marime,
    Material,
    Promotie,
    Produs,
)

admin.site.site_header = "Panou de Administrare – StepStyle Încălțăminte"
admin.site.site_title = "Admin StepStyle"
admin.site.index_title = "Administrare Magazin de Încălțăminte"
admin.site.site_url = "/aplicatie_exemplu/"


class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nume', 'culoare', 'icon', 'descriere')
    search_fields = ('nume', 'descriere')
    search_help_text = "Caută categorii după nume sau cuvinte din descriere."


class BrandAdmin(admin.ModelAdmin):
    list_display = ('nume', 'tara_origine', 'an_fondare', 'website')
    search_fields = ('nume', 'tara_origine')
    search_help_text = "Caută branduri după nume sau țara de origine."
    ordering = ('nume',)


class ImaginePrincipalaAdmin(admin.ModelAdmin):
    list_display = ('alt_text', 'imagine')
    search_fields = ('alt_text', 'imagine')
    search_help_text = "Caută imagini după textul alternativ (alt_text) sau numele fișierului."


class MarimeAdmin(admin.ModelAdmin):
    list_display = ('marime_eu', 'lungime_talpa_cm')
    search_fields = ('marime_eu', 'lungime_talpa_cm')
    search_help_text = "Caută mărimi după numărul EU sau lungimea tălpii în cm."
    ordering = ('marime_eu',)


class MaterialAdmin(admin.ModelAdmin):
    list_display = ('nume', 'rezistent_apa')
    search_fields = ('nume', 'rezistent_apa')
    search_help_text = "Caută materiale după nume sau rezistența la apă."
    list_filter = ('rezistent_apa',)


class PromotieAdmin(admin.ModelAdmin):
    list_display = ('nume', 'procent_reducere', 'data_inceput', 'data_sfarsit')
    search_fields = ('nume', 'procent_reducere')
    search_help_text = "Caută promoții după nume sau procentul de reducere."
    ordering = ('-data_inceput',)


class ProdusAdmin(admin.ModelAdmin):
    list_display = (
        'cod_produs',
        'nume',
        'pret_formatat',
        'categorie',
        'brand',
        'tara_brand',
        'gen',
        'in_stoc',
    )
    list_select_related = ('categorie', 'brand')
    list_filter = ('categorie', 'brand', 'gen', 'in_stoc')
    search_fields = ('nume', 'cod_produs')
    search_help_text = "Caută produse după nume sau codul unic al produsului (ex: NK-AM90-001)."
    ordering = ('-pret', 'nume')
    list_per_page = 5

    fieldsets = (
        ('Informații obligatorii produs', {
            'fields': (
                ('nume', 'cod_produs'),
                ('pret', 'gen', 'in_stoc', 'stoc'),
                ('categorie', 'brand'),
                ('marimi', 'materiale'),
            )
        }),
        ('Detalii opționale', {
            'fields': ('descriere', 'taguri', 'imagine_principala', 'promotii'),
            'classes': ('collapse',),
            'description': 'Câmpuri opționale care pot fi completate ulterior.',
        }),
    )

    actions = ['export_csv_produse', 'marcheaza_epuizat']

    @admin.display(description="Țară brand", ordering='brand__tara_origine')
    def tara_brand(self, obj):
        return obj.brand.tara_origine

    @admin.display(description="Preț", ordering='pret')
    def pret_formatat(self, obj):
        culoare = "#1b7a3d" if obj.in_stoc else "#c62828"
        return format_html('<b style="color: {};">{} RON</b>', culoare, obj.pret)

    @admin.action(description="Exportă produsele selectate în format CSV")
    def export_csv_produse(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="produse_stepstyle.csv"'
        writer = csv.writer(response)
        writer.writerow(['Cod produs', 'Nume', 'Preț (RON)', 'Categorie', 'Brand', 'Gen', 'În stoc'])
        for p in queryset:
            writer.writerow([
                p.cod_produs,
                p.nume,
                p.pret,
                p.categorie.nume,
                p.brand.nume,
                p.get_gen_display(),
                'Da' if p.in_stoc else 'Nu',
            ])
        return response

    @admin.action(description="Marchează produsele selectate ca epuizate (în stoc = Nu)")
    def marcheaza_epuizat(self, request, queryset):
        queryset.update(in_stoc=False)


admin.site.register(Categorie, CategorieAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(ImaginePrincipala, ImaginePrincipalaAdmin)
admin.site.register(Marime, MarimeAdmin)
admin.site.register(Material, MaterialAdmin)
admin.site.register(Promotie, PromotieAdmin)
admin.site.register(Produs, ProdusAdmin)
admin.site.register(Departament)
admin.site.register(TipMesaj)