from django.urls import path
from . import views
urlpatterns = [
    path("",views.index, name="index"),
    path("info", views.info, name="info"),
    path("despre", views.despre, name="despre"),
    path("istoric", views.in_lucru, name="istoric"),
    path("produse", views.lista_produse, name="produse"),
    path("produse/<int:pk>/", views.detaliu_produs, name="detaliu_produs"),
    path("categorii/<str:nume_categorie>/", views.produse_categorie, name="produse_categorie"),
    path("contact", views.contact_view, name="contact"),
    path("mesaje", views.mesaje_view, name="mesaje"),
    path("cos_virtual", views.in_lucru, name="cos_virtual"),
    path("ghid_marimi", views.in_lucru, name="ghid_marimi"),
    path("livrare_retur", views.in_lucru, name="livrare_retur"),
    path("log", views.in_lucru, name="log"),
    path("adauga-produs", views.adauga_produs, name="adauga_produs"),
    path("inregistrare", views.inregistrare_view, name="inregistrare"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("profil", views.profil_view, name="profil"),
    path("profil/editare", views.editare_profil_view, name="editare_profil"),
    path("profil/schimbare-parola", views.schimbare_parola_view, name="schimbare_parola"),
]

