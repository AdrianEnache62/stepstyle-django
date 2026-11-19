from django.db import models
from django.urls import reverse
from django.contrib.postgres.fields import ArrayField
from django.db import models


class Categorie(models.Model):
    nume = models.CharField(
        max_length=100,
        unique=True,
        error_messages={
            'unique': "Există deja o categorie cu acest nume.",
            'blank': "Numele categoriei nu poate fi gol.",
            'max_length': "Numele categoriei nu poate depăși 100 de caractere.",
        },
    )
    icon = models.CharField(
        max_length=50,
        default='fa-shoe-prints',
        help_text="Clasă FontAwesome (ex: fa-running, fa-socks, fa-shoe-prints).",
    )
    descriere = models.TextField(null=True, blank=True)
    culoare = models.CharField(
        max_length=20,
        default='#333333',
        blank=True,
        help_text="Cod hex pentru eticheta categoriei (ex: #1a2b3c).",
    )

    class Meta:
        ordering = ['nume']
        verbose_name = "Categorie"
        verbose_name_plural = "Categorii"

    def __str__(self):
        return self.nume


class Brand(models.Model):
    nume = models.CharField(
        max_length=100,
        unique=True,
        error_messages={
            'unique': "Acest brand este deja înregistrat.",
            'blank': "Numele brandului este obligatoriu.",
        },
    )
    tara_origine = models.CharField(max_length=100)
    an_fondare = models.PositiveIntegerField(null=True, blank=True)
    website = models.URLField(
        null=True,
        blank=True,
        error_messages={
            'invalid': "Introduceți un URL valid (ex: https://www.exemplu.ro).",
        },
    )
    logo = models.ImageField(upload_to='branduri/', null=True, blank=True)

    class Meta:
        ordering = ['nume']
        verbose_name = "Brand"
        verbose_name_plural = "Branduri"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(an_fondare__gte=1800) | models.Q(an_fondare__isnull=True),
                name='an_fondare_valid',
                violation_error_message="Anul fondării trebuie să fie cel puțin 1800.",
            ),
        ]

    def __str__(self):
        return f"{self.nume} ({self.tara_origine})"


class ImaginePrincipala(models.Model):
    imagine = models.ImageField(upload_to='produse/')
    alt_text = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        verbose_name = "Imagine principală"
        verbose_name_plural = "Imagini principale"

    def __str__(self):
        return self.alt_text if self.alt_text else self.imagine.name


class Marime(models.Model):
    marime_eu = models.PositiveIntegerField(unique=True)
    lungime_talpa_cm = models.FloatField(
        help_text="Lungimea interioară a tălpii în centimetri (ex: 26.5).",
    )

    class Meta:
        ordering = ['marime_eu']
        verbose_name = "Mărime"
        verbose_name_plural = "Mărimi"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(marime_eu__gte=16) & models.Q(marime_eu__lte=52),
                name='marime_eu_valida',
                violation_error_message="Mărimea EU trebuie să fie între 16 și 52.",
            ),
            models.CheckConstraint(
                condition=models.Q(lungime_talpa_cm__gt=0),
                name='lungime_talpa_pozitiva',
                violation_error_message="Lungimea tălpii trebuie să fie un număr pozitiv.",
            ),
        ]

    def __str__(self):
        return f"EU {self.marime_eu} ({self.lungime_talpa_cm} cm)"


class Material(models.Model):
    nume = models.CharField(max_length=100, unique=True)
    rezistent_apa = models.BooleanField(default=False)

    class Meta:
        ordering = ['nume']
        verbose_name = "Material"
        verbose_name_plural = "Materiale"

    def __str__(self):
        return self.nume


class Promotie(models.Model):
    nume = models.CharField(max_length=120)
    procent_reducere = models.PositiveIntegerField(
        default=10,
        help_text="Procentul de reducere aplicat, între 1 și 90.",
        error_messages={
            'invalid': "Introduceți un număr întreg valid pentru procentul de reducere.",
        },
    )
    data_inceput = models.DateField()
    data_sfarsit = models.DateField()

    class Meta:
        ordering = ['-data_inceput']
        verbose_name = "Promoție"
        verbose_name_plural = "Promoții"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(procent_reducere__gte=1) & models.Q(procent_reducere__lte=90),
                name='procent_reducere_valid',
                violation_error_message="Procentul de reducere trebuie să fie între 1% și 90%.",
            ),
        ]

    def __str__(self):
        return f"{self.nume} (-{self.procent_reducere}%)"


class Produs(models.Model):
    class GenChoices(models.TextChoices):
        BARBATI = 'barbati', 'Bărbați'
        FEMEI = 'femei', 'Femei'
        COPII = 'copii', 'Copii'
        UNISEX = 'unisex', 'Unisex'

    nume = models.CharField(max_length=100)
    stoc = models.PositiveIntegerField(default=10)
    taguri = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text="Cuvinte cheie separate prin virgulă (ex: sport, piele, vara).",
    )
    cod_produs = models.CharField(
        max_length=50,
        unique=True,
        help_text="Cod unic intern al produsului (ex: NK-AIR-001).",
        error_messages={
            'unique': "Există deja un produs cu acest cod.",
            'blank': "Codul produsului este obligatoriu.",
            'max_length': "Codul produsului nu poate depăși 50 de caractere.",
        },
    )
    descriere = models.TextField(null=True, blank=True)
    pret = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Prețul de vânzare în RON (valoare pozitivă).",
        error_messages={
            'invalid': "Introduceți un preț valid (ex: 249.99).",
            'max_digits': "Prețul nu poate depăși 8 cifre în total.",
            'max_decimal_places': "Prețul poate avea maxim 2 zecimale.",
        },
    )
    in_stoc = models.BooleanField(default=True)
    gen = models.CharField(
        max_length=15,
        choices=GenChoices.choices,
        default=GenChoices.UNISEX,
    )
    data_adaugarii = models.DateTimeField(auto_now_add=True)

    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name='produse')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='produse')
    imagine_principala = models.OneToOneField(
        ImaginePrincipala,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produs',
    )
    marimi = models.ManyToManyField(Marime, related_name='produse')
    materiale = models.ManyToManyField(Material, related_name='produse')
    promotii = models.ManyToManyField(Promotie, blank=True, related_name='produse')

    class Meta:
        ordering = ['-data_adaugarii', 'nume']
        verbose_name = "Produs"
        verbose_name_plural = "Produse"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(pret__gt=0),
                name='pret_pozitiv',
                violation_error_message="Prețul produsului trebuie să fie strict pozitiv.",
            ),
        ]
        indexes = [
            models.Index(fields=['nume'], name='produs_nume_idx'),
            models.Index(fields=['pret'], name='produs_pret_idx'),
            models.Index(fields=['gen', 'in_stoc'], name='produs_gen_stoc_idx'),
        ]

    def __str__(self):
        return f"{self.nume} ({self.cod_produs}) - {self.pret} RON"
    
    def get_absolute_url(self):
        return reverse('detaliu_produs', kwargs={'pk': self.pk})

class Departament(models.Model):
    nume = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Departament"
        verbose_name_plural = "Departamente"

    def __str__(self):
        return self.nume


class TipMesaj(models.Model):
    nume = models.CharField(max_length=50, unique=True)
    min_zile_asteptare = models.PositiveIntegerField(default=2)
    departamente = models.ManyToManyField(Departament, related_name='tipuri_mesaje')

    class Meta:
        verbose_name = "Tip mesaj"
        verbose_name_plural = "Tipuri mesaje"

    def __str__(self):
        return f"{self.nume} (min {self.min_zile_asteptare} zile)"