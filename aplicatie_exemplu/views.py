import json
import os
import re
import time
from datetime import datetime
from django.core.files.storage import FileSystemStorage
from .models import Departament, TipMesaj
from .forms import ContactForm, calculeaza_varsta_ani_luni, genereaza_cod_cerere

import random
from urllib.parse import urlencode
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from .models import Produs, Categorie

from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from .models import Profil
from .forms import InregistrareForm, LoginPersonalizatForm, EditareDateForm
from decimal import Decimal
from django.shortcuts import redirect
from .forms import ProdusModelForm
from .forms import FiltruProduseForm
from django.contrib import messages
from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime

ZILE_RO = ["Luni", "Marți", "Miercuri", "Joi", "Vineri", "Sâmbătă", "Duminică"]
LUNI_RO = ["", "Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie", "Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"]

def _randare_lista_produse(request, queryset, categorie_curenta=None):
    if request.GET:
        form = FiltruProduseForm(request.GET, categorie_fixa=categorie_curenta)
    else:
        initial = {'prod_per_pag': '6', 'coloane': '3'}
        if categorie_curenta:
            initial['categorie'] = categorie_curenta.pk
        form = FiltruProduseForm(initial=initial, categorie_fixa=categorie_curenta)

    if categorie_curenta and 'categorie' in request.GET:
        cat_trimisa = request.GET.get('categorie')
        if str(cat_trimisa) != str(categorie_curenta.pk):
            messages.error(
                request,
                "Eroare de securitate: valoarea categoriei a fost modificată ilegal! Filtrarea a fost păstrată pe categoria curentă.",
            )

    prod_per_pag = settings.PROD_PER_PAG
    coloane = 3

    if request.GET and form.is_valid():
        cd = form.cleaned_data
        if cd.get('nume'):
            queryset = queryset.filter(nume__icontains=cd['nume'])
        if cd.get('cod_produs'):
            queryset = queryset.filter(cod_produs__icontains=cd['cod_produs'])
        if cd.get('pret_min') is not None:
            queryset = queryset.filter(pret__gte=cd['pret_min'])
        if cd.get('pret_max') is not None:
            queryset = queryset.filter(pret__lte=cd['pret_max'])
        if cd.get('stoc_min_filtru') is not None:
            queryset = queryset.filter(stoc__gte=cd['stoc_min_filtru'])
        if cd.get('in_stoc') == 'da':
            queryset = queryset.filter(in_stoc=True)
        elif cd.get('in_stoc') == 'nu':
            queryset = queryset.filter(in_stoc=False)
        if cd.get('gen'):
            queryset = queryset.filter(gen=cd['gen'])
        if not categorie_curenta and cd.get('categorie'):
            queryset = queryset.filter(categorie=cd['categorie'])
        if cd.get('brand'):
            queryset = queryset.filter(brand=cd['brand'])
        if cd.get('marime'):
            queryset = queryset.filter(marimi=cd['marime'])
        if cd.get('material'):
            queryset = queryset.filter(materiale=cd['material'])
        if cd.get('promotie'):
            queryset = queryset.filter(promotii=cd['promotie'])
        if cd.get('data_dupa'):
            queryset = queryset.filter(data_adaugarii__date__gte=cd['data_dupa'])
        if cd.get('tag_filtru'):
            queryset = queryset.filter(taguri__contains=[cd['tag_filtru'].strip()])

        if cd.get('coloane'):
            coloane = int(cd['coloane'])

        if cd.get('prod_per_pag'):
            noua_paginare = int(cd['prod_per_pag'])
            vechea_paginare = request.session.get('ultima_paginare', settings.PROD_PER_PAG)
            if noua_paginare != vechea_paginare:
                messages.warning(
                    request,
                    "Ai schimbat numărul de produse pe pagină: în urma repaginării este posibil să fi sărit peste unele produse sau să le vezi din nou pe cele deja vizualizate.",
                )
                request.session['ultima_paginare'] = noua_paginare
            prod_per_pag = noua_paginare

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

    queryset = queryset.distinct()

    total_produse = queryset.count()
    if total_produse == 0:
        messages.warning(request, "Nu a fost găsit niciun produs pentru filtrele selectate.")
    elif taguri_active or sort:
        messages.success(request, f"Filtrarea/sortarea a fost aplicată cu succes ({total_produse} produse găsite).")

    paginator = Paginator(queryset, prod_per_pag)
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
        'form': form,
        'coloane': coloane,
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
    messages.debug(request, f"[DEBUG] Catalog încărcat: {produse.count()} produse în baza de date.")
    messages.info(request, "Poți sorta produsele sau filtra după taguri direct din această pagină.")
    return _randare_lista_produse(request, produse)


def produse_categorie(request, nume_categorie):
    try:
        categorie = Categorie.objects.get(nume=nume_categorie)
    except Categorie.DoesNotExist:
        messages.error(request, f"Categoria «{nume_categorie}» nu există.")
        return render(request, 'aplicatie_exemplu/eroare_produs.html', {'id_cautat': nume_categorie}, status=404)

    produse = Produs.objects.select_related('categorie', 'brand', 'imagine_principala').filter(categorie=categorie)
    messages.debug(request, f"[DEBUG] Filtru categorie aplicat: {categorie.nume} (ID={categorie.pk}).")
    messages.info(request, f"Vizualizezi produsele din categoria {categorie.nume}.")
    return _randare_lista_produse(request, produse, categorie_curenta=categorie)


def detaliu_produs(request, pk):
    try:
        produs = (
            Produs.objects.select_related('categorie', 'brand', 'imagine_principala')
            .prefetch_related('marimi', 'materiale', 'promotii')
            .get(pk=pk)
        )
    except Produs.DoesNotExist:
        messages.error(request, f"Eroare: produsul cu ID-ul {pk} nu există în magazin.")
        return render(request, 'aplicatie_exemplu/eroare_produs.html', {'id_cautat': pk}, status=404)

    if produs.stoc < settings.STOC_MIN:
        messages.warning(request, f"Atenție! Stoc limitat pentru {produs.nume}: doar {produs.stoc} bucăți rămase.")
    else:
        messages.success(request, f"Produsul {produs.nume} este disponibil în stoc ({produs.stoc} buc.).")

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

def _preproceseaza_mesaj_html(text):
    linii = [re.sub(r'[ \t]+', ' ', l).strip() for l in text.splitlines() if l.strip()]
    text_curat = '\n'.join(linii)

    def _cap(match):
        return match.group(1) + match.group(2).upper()

    text_curat = re.sub(r'(\.{3}\s*|[.?!]\s+)([a-zǎăâîșț])', _cap, text_curat)
    paragrafe = [f"<p>{linie}</p>" for linie in text_curat.splitlines() if linie]
    return ''.join(paragrafe)


def _obtine_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'necunoscut')


def contact_view(request):
    harta_departamente = {
        tm.nume: list(tm.departamente.values_list('nume', flat=True))
        for tm in TipMesaj.objects.prefetch_related('departamente').all()
    }

    if request.method == 'POST':
        form = ContactForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            tip_obj = TipMesaj.objects.get(nume=cd['tip_mesaj'])

            ani, luni = calculeaza_varsta_ani_luni(cd['data_nasterii'])
            varsta_str = f"{ani} de ani și {luni} luni"
            mesaj_html = _preproceseaza_mesaj_html(cd['mesaj'])
            este_urgent = (cd['min_zile_asteptare'] == tip_obj.min_zile_asteptare)

            baza_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Mesaje_nerezolvate')
            try:
                os.mkdir(baza_dir)
            except FileExistsError:
                pass

            for dep in Departament.objects.all():
                dep_dir = os.path.join(baza_dir, dep.nume)
                try:
                    os.mkdir(dep_dir)
                except FileExistsError:
                    pass

            folder_dest = os.path.join(baza_dir, cd['departament'])
            try:
                os.mkdir(folder_dest)
            except FileExistsError:
                pass

            imagini_salvate = []
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'contact_imagini'))
            for cheie in ('imagine_1', 'imagine_2', 'imagine_3'):
                fisier = cd.get(cheie)
                if fisier:
                    nume_salvat = fs.save(fisier.name, fisier)
                    imagini_salvate.append(nume_salvat)

            acum = datetime.now()
            ts = int(time.time())
            sufix_urgent = '_urgent' if este_urgent else ''
            nume_fisier = f"mesaj_{ts}{sufix_urgent}.json"

            date_json = {
                'nume': cd['nume'],
                'prenume': cd['prenume'],
                'cnp': cd['cnp'],
                'varsta': varsta_str,
                'email': cd['email'],
                'telefon': cd['telefon'],
                'tip_mesaj': cd['tip_mesaj'],
                'departament': cd['departament'],
                'subiect': cd['subiect'],
                'min_zile_asteptare': cd['min_zile_asteptare'],
                'mesaj': mesaj_html,
                'imagini': imagini_salvate,
                'acord_gdpr': cd['acord_gdpr'],
                'cod_cerere': cd['cod_cerere'],
                'urgent': este_urgent,
                'ip': _obtine_ip(request),
                'data_sosire': acum.strftime('%Y-%m-%d'),
                'ora_sosire': acum.strftime('%H:%M:%S'),
            }

            cale_fisier = os.path.join(folder_dest, nume_fisier)
            with open(cale_fisier, 'w', encoding='utf-8') as f:
                json.dump(date_json, f, ensure_ascii=False, indent=4)

            messages.success(request, f"Mesajul tău a fost trimis cu succes către {cd['departament']}! (Fișier: {nume_fisier})")
            form = ContactForm(initial={'cod_cerere': genereaza_cod_cerere()})
        else:
            messages.error(request, "Formularul conține erori. Verifică câmpurile marcate cu roșu.")
    else:
        form = ContactForm(initial={'cod_cerere': genereaza_cod_cerere()})

    return render(request, 'aplicatie_exemplu/contact.html', {
        'form': form,
        'harta_departamente_json': json.dumps(harta_departamente),
    })


def mesaje_view(request):
    departamente = list(Departament.objects.values_list('nume', flat=True))
    dep_selectat = request.GET.get('departament', '')
    data_filtru = request.GET.get('data', '').strip()  # accepta YYYY, YYYY-MM sau YYYY-MM-DD

    baza_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Mesaje_nerezolvate')
    mesaje_gasite = []

    if dep_selectat:
        folder_dep = os.path.join(baza_dir, dep_selectat)
        if os.path.isdir(folder_dep):
            for nume_fis in sorted(os.listdir(folder_dep), reverse=True):
                if not nume_fis.endswith('.json'):
                    continue
                with open(os.path.join(folder_dep, nume_fis), 'r', encoding='utf-8') as f:
                    obj = json.load(f)
                data_msg = obj.get('data_sosire', '')
                if not data_filtru or data_msg.startswith(data_filtru):
                    mesaje_gasite.append({
                        'fisier': nume_fis,
                        'urgent': obj.get('urgent', False),
                        'tip_mesaj': obj.get('tip_mesaj', ''),
                        'campuri': list(obj.items()),
                    })

    return render(request, 'aplicatie_exemplu/mesaje.html', {
        'departamente': departamente,
        'dep_selectat': dep_selectat,
        'data_filtru': data_filtru,
        'mesaje_gasite': mesaje_gasite,
    })

def adauga_produs(request):
    if request.method == 'POST':
        form = ProdusModelForm(request.POST)
        if form.is_valid():
            produs = form.save(commit=False)
            pret_ach = form.cleaned_data['pret_achizitie']
            adaos = form.cleaned_data['adaos_procent']
            produs.pret = (pret_ach * (Decimal('1') + Decimal(adaos) / Decimal('100'))).quantize(Decimal('0.01'))
            produs.in_stoc = produs.stoc > 0
            produs.save()
            form.save_m2m()
            messages.success(
                request,
                f"Produsul «{produs.nume}» a fost adăugat cu succes la prețul calculat de {produs.pret} RON!",
            )
            return redirect(produs.get_absolute_url())
        else:
            messages.error(request, "Nu s-a putut salva produsul. Corectați erorile din formular.")
    else:
        form = ProdusModelForm()

    return render(request, 'aplicatie_exemplu/adauga_produs.html', {'form': form})


def _salveaza_date_user_in_sesiune(request, user):
    """Salvează datele utilizatorului (și ale profilului, dacă există) în sesiune."""
    date_user = {
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'telefon': user.telefon,
        'tara': user.tara,
        'judet': user.judet,
        'localitate': user.localitate,
        'strada': user.strada,
    }
    date_profil = None
    try:
        p = user.profil
        date_profil = {
            'data_nasterii': str(p.data_nasterii) if p.data_nasterii else '',
            'marime_preferata': p.marime_preferata if p.marime_preferata is not None else '',
            'bio': p.bio,
        }
    except Profil.DoesNotExist:
        date_profil = None

    request.session['date_user'] = date_user
    request.session['date_profil'] = date_profil


def inregistrare_view(request):
    if request.method == 'POST':
        form = InregistrareForm(request.POST)
        if form.is_valid():
            user = form.save()
            dn = form.cleaned_data.get('data_nasterii')
            marime = form.cleaned_data.get('marime_preferata')
            bio = (form.cleaned_data.get('bio') or '').strip()
            if dn or marime is not None or bio:
                Profil.objects.create(
                    utilizator=user,
                    data_nasterii=dn,
                    marime_preferata=marime,
                    bio=bio,
                )
            messages.success(request, "Contul a fost creat cu succes! Te poți autentifica acum.")
            return redirect('login')
        else:
            messages.error(request, "Formularul de înregistrare conține erori.")
    else:
        form = InregistrareForm()
    return render(request, 'aplicatie_exemplu/inregistrare.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginPersonalizatForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if form.cleaned_data.get('tine_ma_minte'):
                request.session.set_expiry(86400)
            else:
                request.session.set_expiry(0)

            _salveaza_date_user_in_sesiune(request, user)
            messages.success(request, f"Bine ai revenit, {user.username}!")
            return redirect('profil')
        else:
            messages.error(request, "Username sau parolă incorectă.")
    else:
        form = LoginPersonalizatForm()
    return render(request, 'aplicatie_exemplu/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "Te-ai deconectat cu succes.")
    return redirect('index')


@login_required(login_url='login')
def profil_view(request):
    if 'date_user' not in request.session:
        _salveaza_date_user_in_sesiune(request, request.user)
    return render(request, 'aplicatie_exemplu/profil.html', {
        'date_user': request.session.get('date_user'),
        'date_profil': request.session.get('date_profil'),
    })


@login_required(login_url='login')
def editare_profil_view(request):
    user = request.user
    try:
        profil_existent = user.profil
    except Profil.DoesNotExist:
        profil_existent = None

    if request.method == 'POST':
        form = EditareDateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            dn = form.cleaned_data.get('data_nasterii')
            marime = form.cleaned_data.get('marime_preferata')
            bio = (form.cleaned_data.get('bio') or '').strip()

            if profil_existent:
                profil_existent.data_nasterii = dn
                profil_existent.marime_preferata = marime
                profil_existent.bio = bio
                profil_existent.save()
            elif dn or marime is not None or bio:
                Profil.objects.create(
                    utilizator=user,
                    data_nasterii=dn,
                    marime_preferata=marime,
                    bio=bio,
                )

            _salveaza_date_user_in_sesiune(request, user)
            messages.success(request, "Datele tale au fost actualizate cu succes!")
            return redirect('profil')
        else:
            messages.error(request, "Verifică erorile din formular.")
    else:
        initial_profil = {}
        if profil_existent:
            initial_profil = {
                'data_nasterii': profil_existent.data_nasterii,
                'marime_preferata': profil_existent.marime_preferata,
                'bio': profil_existent.bio,
            }
        form = EditareDateForm(instance=user, initial=initial_profil)

    return render(request, 'aplicatie_exemplu/editare_profil.html', {'form': form})


@login_required(login_url='login')
def schimbare_parola_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Parola a fost schimbată cu succes!")
            return redirect('profil')
        else:
            messages.error(request, "Nu s-a putut schimba parola. Verifică erorile.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'aplicatie_exemplu/schimbare_parola.html', {'form': form})