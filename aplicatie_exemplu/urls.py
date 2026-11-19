from django.urls import path
from . import views
urlpatterns = [
    path("",views.index, name="index"),
    path("info", views.info, name="info"),
    path("despre", views.despre, name="despre"),
    path("istoric", views.in_lucru, name="istoric"),
    path("produse", views.in_lucru, name="produse"),
    path("contact", views.in_lucru, name="contact"),
    path("cos_virtual", views.in_lucru, name="cos_virtual"),
    path("ghid_marimi", views.in_lucru, name="ghid_marimi"),
    path("livrare_retur", views.in_lucru, name="livrare_retur"),
    path("log", views.in_lucru, name="log"),
]

