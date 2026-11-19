from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime

ZILE_RO = ["Luni", "Marți", "Miercuri", "Joi", "Vineri", "Sâmbătă", "Duminică"]
LUNI_RO = ["", "Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie", "Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"]

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