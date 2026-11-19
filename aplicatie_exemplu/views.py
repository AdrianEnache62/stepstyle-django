import random
from urllib.parse import urlencode
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from .models import Produs, Categorie

from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime

ZILE_RO = ["Luni", "Marți", "Miercuri", "Joi", "Vineri", "Sâmbătă", "Duminică"]
LUNI_RO = ["", "Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie", "Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"]

def _randare_lista_produse(request, queryset, categorie_curenta=None):
    taguri_active = request.GET.getlist('tag')
    for tag in taguri_active:
        queryset = queryset.filter(taguri__contains=[tag])

    sort = request.GET.get('sort', '')
    coloana = request.GET.get('coloana', 'nume')
    coloane_permise = ['nume', 'pret', 'data_adaugarii', 'stoc']
    if coloana not in coloane_permise:
        coloana = 'nume'

    if sort == 'a':
        queryset = queryset.order_by(coloana)
    elif sort == 'd':
        queryset = queryset.order_by(f'-{coloana}')

    total_produse = queryset.count()
    paginator = Paginator(queryset, settings.PROD_PER_PAG)
    nr_pagina = request.GET.get('pagina', 1)

    try:
        pagina = paginator.page(nr_pagina)
    except PageNotAnInteger:
        pagina = paginator.page(1)
    except EmptyPage:
        pagina = paginator.page(paginator.num_pages)

    params_fara_pagina = request.GET.copy()
    params_fara_pagina.pop('pagina', None)
    qs_baza = params_fara_pagina.urlencode()

    taguri_cu_link_eliminare = []
    for t in taguri_active:
        params = request.GET.copy()
        params.pop('pagina', None)
        lista_noua = [x for x in taguri_active if x != t]
        params.setlist('tag', lista_noua)
        taguri_cu_link_eliminare.append((t, params.urlencode()))

    return render(request, 'aplicatie_exemplu/produse.html', {
        'pagina': pagina,
        'total_produse': total_produse,
        'stoc_min': settings.STOC_MIN,
        'categorie_curenta': categorie_curenta,
        'sort': sort,
        'coloana': coloana,
        'taguri_active': taguri_active,
        'taguri_cu_link_eliminare': taguri_cu_link_eliminare,
        'qs_baza': qs_baza,
    })


def lista_produse(request):
    produse = Produs.objects.select_related('categorie', 'brand', 'imagine_principala').all()
    return _randare_lista_produse(request, produse)


def produse_categorie(request, nume_categorie):
    categorie = get_object_or_404(Categorie, nume=nume_categorie)
    produse = Produs.objects.select_related('categorie', 'brand', 'imagine_principala').filter(categorie=categorie)
    return _randare_lista_produse(request, produse, categorie_curenta=categorie)


def detaliu_produs(request, pk):
    try:
        produs = Produs.objects.select_related('categorie', 'brand', 'imagine_principala').prefetch_related('marimi', 'materiale', 'promotii').get(pk=pk)
    except Produs.DoesNotExist:
        return render(request, 'aplicatie_exemplu/eroare_produs.html', {'id_cautat': pk}, status=404)

    similare_qs = list(
        Produs.objects.select_related('imagine_principala')
        .filter(categorie=produs.categorie)
        .exclude(pk=produs.pk)
    )
    k = min(settings.K_PRODUSE_SIMILARE, len(similare_qs))
    produse_similare = random.sample(similare_qs, k) if k > 0 else []

    return render(request, 'aplicatie_exemplu/detaliu_produs.html', {
        'produs': produs,
        'stoc_min': settings.STOC_MIN,
        'produse_similare': produse_similare,
    })

class Accesare:
    contor_id = 0
    
    def __init__(self, ip_client, url, cale, parametri={}):
        Accesare.contor_id += 1
        self.id = Accesare.contor_id
        self.ip_client = ip_client
        self.url = url
        self.cale = cale
        self.parametri = dict(parametri)
        self.data = datetime.now()
    
    def lista_parametri(self):
        rezultat = []
        for cheie, valoare in self.parametri.items():
            if valoare == "" or valoare is None:
                rezultat.append((cheie,None))
            else:
                rezultat.append((cheie,valoare))
        return rezultat
    
    def string_url(self):
        return self.url
    
    def pagina(self):
        return self.cale
    
    def calculeaza_data(self, tip=""):
        zi_sapt = ZILE_RO[self.data.weekday()]
        luna = LUNI_RO[self.data.month]
        
        if tip == "zi":
            rezultat = f"{self.data.day} {luna} {self.data.year}"
        elif tip == "timp":
            rezultat = self.data.strftime("%H:%M:%S")
        else:
            rezultat = f"{zi_sapt}, {self.data.day} {luna} {self.data.year}"
            
        return f"<section><h2>Data si ora </h2><p>{rezultat}</p></section>"
    
    def __str__(self):
        return (
            f"id: {self.id} | "
            f"ip_client: {self.ip_client} | "
            f"string_url: {self.string_url()} | "
            f"pagina: {self.pagina()} | "
            f"calculeaza_data: {self.calculeaza_data()} | "
            f"lista_parametri: {self.lista_parametri()}"
        )

def index(request):
    accesare = Accesare(
        ip_client=request.ip_client,
        url=request.get_full_path(),
        cale=request.path,
        parametri=request.GET.dict()
    )
    print(accesare)
    return render(request, "aplicatie_exemplu/index.html")

def info(request):
    accesare = Accesare(
        ip_client=request.ip_client,
        url=request.get_full_path(),
        cale=request.path,
        parametri=request.GET.dict()
    )
    print(accesare)

    tip_data = request.GET.get("data", "")
    sectiune_data = accesare.calculeaza_data(tip_data)
    
    return render(request, "aplicatie_exemplu/info.html", {"sectiune_data": sectiune_data})

def despre(request):
    accesare = Accesare(
        ip_client=request.ip_client,
        url=request.get_full_path(),
        cale=request.path,
        parametri=request.GET.dict()
    )
    print(accesare)
    return render(request, "aplicatie_exemplu/despre.html")
    

def in_lucru(request):
    accesare = Accesare(
        ip_client=request.ip_client,
        url=request.get_full_path(),
        cale=request.path,
        parametri=request.GET.dict()
    )
    print(accesare)
    return render(request, "aplicatie_exemplu/in_lucru.html")