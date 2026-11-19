import random
import re
import string
from datetime import date
from django.core.exceptions import ValidationError
from .models import Departament, TipMesaj

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Profil
from datetime import date
from django import forms
from .models import Categorie, Brand, Marime, Material, Promotie, Produs


class FiltruProduseForm(forms.Form):
    nume = forms.CharField(
        required=False,
        label="Nume produs",
        widget=forms.TextInput(attrs={'placeholder': 'Caută după nume...'}),
    )
    cod_produs = forms.CharField(
        required=False,
        label="Cod produs",
        widget=forms.TextInput(attrs={'placeholder': 'Ex: NK-AM90'}),
    )
    pret_min = forms.DecimalField(
        required=False,
        label="Preț minim (RON)",
        widget=forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0'}),
    )
    pret_max = forms.DecimalField(
        required=False,
        label="Preț maxim (RON)",
        widget=forms.NumberInput(attrs={'step': '0.01', 'placeholder': '2000'}),
    )
    stoc_min_filtru = forms.IntegerField(
        required=False,
        label="Stoc minim",
        widget=forms.NumberInput(attrs={'placeholder': '0'}),
    )
    in_stoc = forms.ChoiceField(
        required=False,
        label="Disponibilitate",
        choices=[('', 'Toate'), ('da', 'În stoc'), ('nu', 'Epuizat')],
    )
    gen = forms.ChoiceField(
        required=False,
        label="Gen",
        choices=[('', 'Toate')] + list(Produs._meta.get_field('gen').choices),
    )
    categorie = forms.ModelChoiceField(
        queryset=Categorie.objects.all(),
        required=False,
        empty_label="Toate categoriile",
        label="Categorie",
    )
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all(),
        required=False,
        empty_label="Toate brandurile",
        label="Brand",
    )
    marime = forms.ModelChoiceField(
        queryset=Marime.objects.all(),
        required=False,
        empty_label="Orice mărime",
        label="Mărime",
    )
    material = forms.ModelChoiceField(
        queryset=Material.objects.all(),
        required=False,
        empty_label="Orice material",
        label="Material",
    )
    promotie = forms.ModelChoiceField(
        queryset=Promotie.objects.all(),
        required=False,
        empty_label="Orice promoție",
        label="Promoție",
    )
    data_dupa = forms.DateField(
        required=False,
        label="Adăugat după data",
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    tag_filtru = forms.CharField(
        required=False,
        label="Tag",
        widget=forms.TextInput(attrs={'placeholder': 'Ex: piele'}),
    )
    prod_per_pag = forms.ChoiceField(
        required=False,
        label="Produse / pagină",
        choices=[('6', '6'), ('12', '12'), ('18', '18')],
        initial='6',
    )
    coloane = forms.ChoiceField(
        required=False,
        label="Coloane afișare",
        choices=[('1', '1 coloană'), ('2', '2 coloane'), ('3', '3 coloane')],
        initial='3',
    )

    def __init__(self, *args, categorie_fixa=None, **kwargs):
        super().__init__(*args, **kwargs)
        if categorie_fixa is not None:
            self.fields['categorie'].initial = categorie_fixa.pk
            self.fields['categorie'].widget = forms.HiddenInput(
                attrs={'readonly': 'readonly'}
            )

    def clean_pret_min(self):
        val = self.cleaned_data.get('pret_min')
        if val is not None and val < 0:
            raise forms.ValidationError("Prețul minim nu poate fi un număr negativ.")
        return val

    def clean_pret_max(self):
        val = self.cleaned_data.get('pret_max')
        if val is not None and val < 0:
            raise forms.ValidationError("Prețul maxim nu poate fi un număr negativ.")
        return val


    def clean_stoc_min_filtru(self):
        val = self.cleaned_data.get('stoc_min_filtru')
        if val is not None and val < 0:
            raise forms.ValidationError("Stocul minim trebuie să fie cel puțin 0.")
        return val

    def clean_data_dupa(self):
        val = self.cleaned_data.get('data_dupa')
        if val is not None and val > date.today():
            raise forms.ValidationError("Nu poți filtra produse adăugate în viitor.")
        return val

    def clean(self):
        cleaned = super().clean()
        p_min = cleaned.get('pret_min')
        p_max = cleaned.get('pret_max')
        if p_min is not None and p_max is not None and p_min > p_max:
            raise forms.ValidationError(
                "Prețul minim nu poate fi mai mare decât prețul maxim."
            )
        return cleaned


def calculeaza_varsta_ani_luni(data_nasterii):
    """Calculează (ani, luni) trecuți complet de la data nașterii până azi."""
    azi = date.today()
    ani = azi.year - data_nasterii.year
    luni = azi.month - data_nasterii.month
    if azi.day < data_nasterii.day:
        luni -= 1
    if luni < 0:
        ani -= 1
        luni += 12
    return ani, luni


def genereaza_cod_cerere():
    """
    Algoritm propriu: 'SS-' + 3 cifre + '-' + 2 litere mari + 2 litere mici + 1 cifră de control
    (cifra de control = suma celor 3 cifre % 10).
    Exemplu: SS-482-ABcd4
    """
    cifre = [random.randint(0, 9) for _ in range(3)]
    control = sum(cifre) % 10
    cifre_str = ''.join(str(c) for c in cifre)
    mari = ''.join(random.choices(string.ascii_uppercase, k=2))
    mici = ''.join(random.choices(string.ascii_lowercase, k=2))
    return f"SS-{cifre_str}-{mari}{mici}{control}"


def valideaza_cod_cerere(value):
    m = re.fullmatch(r'SS-(\d{3})-([A-Z]{2})([a-z]{2})(\d)', value or '')
    if not m:
        raise ValidationError("Codul cererii este invalid sau a fost manipulat.")
    cifre_str, _, _, control_str = m.groups()
    if sum(int(c) for c in cifre_str) % 10 != int(control_str):
        raise ValidationError("Codul cererii nu respectă cifra de control a algoritmului.")


def valideaza_litera_mare_si_caractere(value):
    """Verifică dacă textul începe cu literă mare și conține doar litere, spații și cratime."""
    if not value:
        return
    if not value[0].isupper():
        raise ValidationError("Textul trebuie să înceapă cu literă mare.")
    if not re.fullmatch(r'[A-Za-zĂÂÎȘȚăâîșț\s\-]+', value):
        raise ValidationError("Sunt permise doar litere, spații și cratime.")


def valideaza_majuscula_dupa_separator(value):
    """Verifică dacă după fiecare spațiu sau cratimă urmează literă mare."""
    if not value:
        return
    for m in re.finditer(r'[\s\-](.)', value):
        if not m.group(1).isupper():
            raise ValidationError("După fiecare spațiu sau cratimă trebuie să urmeze o literă mare.")


def valideaza_fara_linkuri(value):
    """Respinge http://, https:// sau mai mult de 2 cuvinte separate prin puncte fără spații."""
    if not value:
        return
    if re.search(r'\bhttps?://', value, flags=re.IGNORECASE):
        raise ValidationError("Nu sunt permise linkuri (http:// sau https://).")
    if re.search(r'[A-Za-z0-9]+(?:\.[A-Za-z0-9]+){2,}', value):
        raise ValidationError("Nu sunt permise șiruri cu mai mult de 2 cuvinte separate prin puncte fără spații.")


class ContactForm(forms.Form):
    nume = forms.CharField(
        max_length=10,
        required=True,
        label="Nume",
        validators=[valideaza_litera_mare_si_caractere, valideaza_majuscula_dupa_separator],
        error_messages={
            'required': 'Numele este obligatoriu.',
            'max_length': 'Numele nu poate depăși 10 caractere.',
        },
    )
    prenume = forms.CharField(
        max_length=30,
        required=False,
        label="Prenume",
        help_text="Prenumele pot fi separate prin spațiu sau linioară.",
        validators=[valideaza_litera_mare_si_caractere, valideaza_majuscula_dupa_separator],
        error_messages={'max_length': 'Prenumele nu poate depăși 30 de caractere.'},
    )
    cnp = forms.CharField(
        required=False,
        min_length=13,
        max_length=13,
        label="CNP",
        widget=forms.TextInput(attrs={'id': 'id_cnp', 'maxlength': '13', 'placeholder': '13 cifre'}),
        error_messages={
            'min_length': 'CNP-ul trebuie să aibă exact 13 caractere.',
            'max_length': 'CNP-ul trebuie să aibă exact 13 caractere.',
        },
    )
    data_nasterii = forms.DateField(
        required=True,
        label="Data nașterii",
        widget=forms.DateInput(attrs={'type': 'date'}),
        error_messages={
            'required': 'Data nașterii este obligatorie.',
            'invalid': 'Introduceți o dată validă.',
        },
    )
    email = forms.EmailField(
        required=True,
        label="E-mail",
        error_messages={
            'required': 'Adresa de e-mail este obligatorie.',
            'invalid': 'Introduceți o adresă de e-mail validă.',
        },
    )
    confirm_email = forms.EmailField(
        required=True,
        label="Confirmare e-mail",
        error_messages={
            'required': 'Confirmarea e-mailului este obligatorie.',
            'invalid': 'Introduceți o adresă de e-mail validă.',
        },
    )
    telefon = forms.CharField(
        required=False,
        max_length=20,
        label="Telefon",
        help_text="Format acceptat: 07XXXXXXXX sau cu prefix de țară +407XXXXXXXX.",
    )
    tip_mesaj = forms.ChoiceField(
        required=True,
        label="Tip mesaj",
        initial="neselectat",
        choices=[('neselectat', 'neselectat')],
    )
    departament = forms.ChoiceField(
        required=True,
        label="Departament destinație",
        initial="neselectat",
        choices=[('neselectat', 'neselectat')],
    )
    subiect = forms.CharField(
        max_length=100,
        required=True,
        label="Subiect",
        validators=[valideaza_litera_mare_si_caractere, valideaza_fara_linkuri],
        error_messages={
            'required': 'Subiectul este obligatoriu.',
            'max_length': 'Subiectul nu poate depăși 100 de caractere.',
        },
    )
    min_zile_asteptare = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=30,
        label="Minim zile așteptare (Pentru review-uri/reclamații minimul de zile de așteptare trebuie setat de la 4 încolo, iar pentru cereri/întrebări/programări de la 2 încolo. Maximul e 30.)",
        error_messages={
            'required': 'Introduceți numărul minim de zile de așteptare.',
            'min_value': 'Numărul de zile trebuie să fie un număr natural pozitiv.',
            'max_value': 'Maximul permis este de 30 de zile.',
        },
    )
    mesaj = forms.CharField(
        required=True,
        label="Mesaj (vă rugăm să vă semnați la finalul mesajului cu numele dvs.)",
        widget=forms.Textarea(attrs={'rows': 5}),
        validators=[valideaza_fara_linkuri],
        error_messages={'required': 'Mesajul este obligatoriu.'},
    )
    imagine_1 = forms.ImageField(required=False, label="Imagine 1")
    imagine_2 = forms.ImageField(required=False, label="Imagine 2")
    imagine_3 = forms.ImageField(required=False, label="Imagine 3")
    acord_gdpr = forms.BooleanField(
        required=False,  
        initial=False,
        label="Sunt de acord cu prelucrarea datelor personale (GDPR)",
    )
    cod_cerere = forms.CharField(
        widget=forms.HiddenInput(),
        validators=[valideaza_cod_cerere],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tipuri = [(t.nume, t.nume.capitalize()) for t in TipMesaj.objects.all()]
        deps = [(d.nume, d.nume) for d in Departament.objects.all()]
        self.fields['tip_mesaj'].choices = [('neselectat', 'neselectat')] + tipuri
        self.fields['departament'].choices = [('neselectat', 'neselectat')] + deps

    def clean_data_nasterii(self):
        dn = self.cleaned_data.get('data_nasterii')
        if dn:
            ani, _ = calculeaza_varsta_ani_luni(dn)
            if ani < 18:
                raise ValidationError("Expeditorul trebuie să fie major (peste 18 ani).")
        return dn

    def clean_email(self):
        email = self.cleaned_data.get('email', '')
        domeniu = email.split('@')[-1].lower() if '@' in email else ''
        if domeniu in ('guerillamail.com', 'yopmail.com'):
            raise ValidationError("Nu sunt permise adresele de e-mail temporare (guerillamail.com / yopmail.com).")
        return email

    def clean_cnp(self):
        cnp = self.cleaned_data.get('cnp', '').strip()
        if not cnp:
            return ''
        if not cnp.isdigit():
            raise ValidationError("CNP-ul trebuie să conțină doar cifre.")
        if cnp[0] not in ('1', '2', '5', '6'):
            raise ValidationError("CNP-ul trebuie să înceapă cu 1, 2, 5 sau 6.")
        secol = 1900 if cnp[0] in ('1', '2') else 2000
        an = secol + int(cnp[1:3])
        luna = int(cnp[3:5])
        zi = int(cnp[5:7])
        try:
            date(an, luna, zi)
        except ValueError:
            raise ValidationError("Cele 6 cifre ale datei din CNP nu formează o dată calendaristică validă.")
        return cnp

    def clean_tip_mesaj(self):
        tip = self.cleaned_data.get('tip_mesaj')
        if not tip or tip == 'neselectat':
            raise ValidationError("Trebuie să selectați un tip de mesaj valid.")
        if not TipMesaj.objects.filter(nume=tip).exists():
            raise ValidationError("Tipul de mesaj selectat nu există în baza de date.")
        return tip

    def clean_departament(self):
        dep = self.cleaned_data.get('departament')
        if not dep or dep == 'neselectat':
            raise ValidationError("Trebuie să selectați un departament destinație.")
        if not Departament.objects.filter(nume=dep).exists():
            raise ValidationError("Departamentul selectat nu există în baza de date.")
        return dep

    def clean_mesaj(self):
        mesaj = self.cleaned_data.get('mesaj', '')
        cuvinte = re.findall(r'[A-Za-z0-9ĂÂÎȘȚăâîșț]+', mesaj)
        if not (5 <= len(cuvinte) <= 100):
            raise ValidationError(f"Mesajul trebuie să conțină între 5 și 100 de cuvinte (aveți {len(cuvinte)}).")
        for c in cuvinte:
            if len(c) > 15:
                raise ValidationError(f"Cuvântul «{c}» depășește lungimea maximă permisă de 15 caractere.")
        return mesaj

    def clean_acord_gdpr(self):
        acord = self.cleaned_data.get('acord_gdpr')
        if not acord:
            raise ValidationError("Trebuie să vă dați acordul pentru prelucrarea datelor personale (GDPR).")
        return acord

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get('email')
        confirm_email = cleaned.get('confirm_email')
        if email and confirm_email and email != confirm_email:
            self.add_error('confirm_email', "Adresele de e-mail nu coincid.")

        nume = cleaned.get('nume')
        mesaj = cleaned.get('mesaj')
        if nume and mesaj:
            cuvinte = re.findall(r'[A-Za-z0-9ĂÂÎȘȚăâîșț]+', mesaj)
            if not cuvinte or cuvinte[-1].lower() != nume.lower():
                self.add_error('mesaj', f"Mesajul trebuie să se încheie cu semnătura dvs. (ultimul cuvânt să fie «{nume}»).")

        cnp = cleaned.get('cnp')
        dn = cleaned.get('data_nasterii')
        if cnp and dn:
            secol = 1900 if cnp[0] in ('1', '2') else 2000
            data_cnp = date(secol + int(cnp[1:3]), int(cnp[3:5]), int(cnp[5:7]))
            if data_cnp != dn:
                self.add_error('cnp', "Data nașterii extrasă din CNP nu corespunde cu data nașterii introdusă.")

        tip_nume = cleaned.get('tip_mesaj')
        dep_nume = cleaned.get('departament')
        zile = cleaned.get('min_zile_asteptare')
        if tip_nume and tip_nume != 'neselectat':
            tip_obj = TipMesaj.objects.filter(nume=tip_nume).first()
            if tip_obj:
                if zile is not None and zile < tip_obj.min_zile_asteptare:
                    self.add_error(
                        'min_zile_asteptare',
                        f"Pentru tipul «{tip_nume}», minimul de zile de așteptare este {tip_obj.min_zile_asteptare}.",
                    )
                if dep_nume and dep_nume != 'neselectat':
                    if not tip_obj.departamente.filter(nume=dep_nume).exists():
                        self.add_error(
                            'departament',
                            f"Eroare de integritate: departamentul «{dep_nume}» nu poate primi mesaje de tipul «{tip_nume}».",
                        )
        return cleaned


from decimal import Decimal



def valideaza_fara_caractere_interzise(value):
    """Validator extern 1 (folosit pe două câmpuri: nume și descriere)."""
    if value and any(ch in value for ch in ('@', '#', '$', '%', '^')):
        raise ValidationError("Textul nu poate conține caractere speciale (@, #, $, %, ^).")


def valideaza_lungime_minima_3(value):
    """Validator extern 2 (aplicat împreună cu primul pe câmpul nume, în ordine specifică)."""
    if value and len(value.strip()) < 3:
        raise ValidationError("Valoarea trebuie să aibă cel puțin 3 caractere.")


class ProdusModelForm(forms.ModelForm):
    pret_achizitie = forms.DecimalField(
        label="Preț de achiziție de la furnizor (RON)",
        max_digits=8,
        decimal_places=2,
        help_text="Introduceți prețul de bază plătit furnizorului (fără adaos).",
        error_messages={
            'required': 'Prețul de achiziție este obligatoriu.',
            'invalid': 'Introduceți o sumă numerică validă pentru prețul de achiziție.',
        },
    )
    adaos_procent = forms.IntegerField(
        label="Adaos comercial (%)",
        help_text="Procentul de adaos adăugat la prețul de achiziție (între 5% și 200%).",
        error_messages={
            'required': 'Procentul de adaos comercial este obligatoriu.',
            'invalid': 'Introduceți un număr întreg valid pentru adaos.',
        },
    )

    class Meta:
        model = Produs
        fields = [
            'nume',
            'cod_produs',
            'descriere',
            'stoc',
            'gen',
            'categorie',
            'brand',
            'marimi',
            'materiale',
        ]
        labels = {
            'nume': 'Denumire produs încălțăminte',
            'cod_produs': 'Cod unic SKU',
            'stoc': 'Cantitate inițială în stoc',
        }
        help_texts = {
            'cod_produs': 'Format recomandat: XX-YYYY-001 (doar litere mari, cifre și cratimă).',
            'stoc': 'Dacă stocul este 0, produsul va fi marcat automat ca epuizat.',
        }
        error_messages = {
            'nume': {
                'required': 'Denumirea produsului este obligatorie.',
                'max_length': 'Denumirea produsului este prea lungă.',
            },
            'cod_produs': {
                'required': 'Codul unic al produsului este obligatoriu.',
                'unique': 'Există deja un produs cu acest cod unic în baza de date.',
            },
            'stoc': {
                'required': 'Introduceți cantitatea disponibilă în stoc.',
                'invalid': 'Stocul trebuie să fie un număr întreg.',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nume'].validators.extend([
            valideaza_fara_caractere_interzise,
            valideaza_lungime_minima_3,
        ])
        self.fields['descriere'].validators.append(valideaza_fara_caractere_interzise)

    def clean_pret_achizitie(self):
        val = self.cleaned_data.get('pret_achizitie')
        if val is not None and val <= 0:
            raise ValidationError("Prețul de achiziție trebuie să fie strict mai mare decât 0 RON.")
        return val

    def clean_adaos_procent(self):
        val = self.cleaned_data.get('adaos_procent')
        if val is not None and not (5 <= val <= 200):
            raise ValidationError("Adaosul comercial trebuie să fie cuprins între 5% și 200%.")
        return val

    def clean_cod_produs(self):
        cod = self.cleaned_data.get('cod_produs', '').strip()
        if not re.fullmatch(r'[A-Z0-9\-]+', cod):
            raise ValidationError("Codul produsului trebuie să conțină doar litere mari, cifre și cratimă.")
        return cod

    def clean(self):
        cleaned = super().clean()
        pret_ach = cleaned.get('pret_achizitie')
        adaos = cleaned.get('adaos_procent')
        if pret_ach is not None and adaos is not None:
            pret_final = pret_ach * (Decimal('1') + Decimal(adaos) / Decimal('100'))
            if pret_final > Decimal('5000'):
                raise ValidationError(
                    f"Prețul final calculat ({pret_final:.2f} RON) depășește plafonul maxim de 5000 RON al magazinului."
                )
        return cleaned


class InregistrareForm(UserCreationForm):
    # Câmpuri opționale din Profil
    data_nasterii = forms.DateField(
        required=False,
        label="Data nașterii (opțional)",
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    marime_preferata = forms.IntegerField(
        required=False,
        min_value=18,
        max_value=52,
        label="Mărime preferată EU (opțional)",
    )
    bio = forms.CharField(
        required=False,
        label="Despre mine / Bio (opțional)",
        widget=forms.Textarea(attrs={'rows': 3}),
    )

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'telefon',
            'tara',
            'judet',
            'localitate',
            'strada',
            'password1',
            'password2',
        ]
        labels = {
            'first_name': 'Prenume',
            'last_name': 'Nume',
            'email': 'E-mail',
            'telefon': 'Telefon',
            'tara': 'Țară',
            'judet': 'Județ',
            'localitate': 'Localitate',
            'strada': 'Stradă',
        }

    def clean_telefon(self):
        tel = (self.cleaned_data.get('telefon') or '').strip()
        if tel and not re.fullmatch(r'\+?\d{10,15}', tel):
            raise ValidationError("Telefonul trebuie să conțină 10-15 cifre (opțional cu '+' la început).")
        return tel

    def clean_tara(self):
        tara = (self.cleaned_data.get('tara') or '').strip()
        if len(tara) < 2 or not re.fullmatch(r'[A-Za-zĂÂÎȘȚăâîșț\s\-]+', tara):
            raise ValidationError("Țara trebuie să conțină doar litere (minim 2 caractere).")
        return tara

    def clean_judet(self):
        judet = (self.cleaned_data.get('judet') or '').strip()
        if judet:
            if not judet[0].isupper():
                raise ValidationError("Județul trebuie să înceapă cu literă mare.")
            if not re.fullmatch(r'[A-Za-zĂÂÎȘȚăâîșț\s\-]+', judet):
                raise ValidationError("Județul poate conține doar litere, spații și cratime.")
        return judet


class LoginPersonalizatForm(AuthenticationForm):
    tine_ma_minte = forms.BooleanField(
        required=False,
        label="Ține-mă logat timp de 1 zi",
    )


class EditareDateForm(forms.ModelForm):
    data_nasterii = forms.DateField(
        required=False,
        label="Data nașterii",
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    marime_preferata = forms.IntegerField(
        required=False,
        min_value=18,
        max_value=52,
        label="Mărime preferată EU",
    )
    bio = forms.CharField(
        required=False,
        label="Despre mine / Bio",
        widget=forms.Textarea(attrs={'rows': 3}),
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'telefon', 'tara', 'judet', 'localitate', 'strada']
        labels = {
            'first_name': 'Prenume',
            'last_name': 'Nume',
            'email': 'E-mail',
            'telefon': 'Telefon',
            'tara': 'Țară',
            'judet': 'Județ',
            'localitate': 'Localitate',
            'strada': 'Stradă',
        }