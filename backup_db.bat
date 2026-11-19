@echo off
set PGPASSWORD=parola_stepstyle
set DB_NAME=stepstyle_db
set DB_USER=stepstyle_user
set BACKUP_FILE=backup_inserts.sql

echo Se creeaza backup-ul cu comenzi INSERT pentru tabelele aplicatiei...

pg_dump -U %DB_USER% -h localhost -p 5432 -d %DB_NAME% ^
  --data-only --inserts ^
  -t django.aplicatie_exemplu_categorie ^
  -t django.aplicatie_exemplu_brand ^
  -t django.aplicatie_exemplu_imagineprincipala ^
  -t django.aplicatie_exemplu_marime ^
  -t django.aplicatie_exemplu_material ^
  -t django.aplicatie_exemplu_promotie ^
  -t django.aplicatie_exemplu_produs ^
  -t django.aplicatie_exemplu_produs_marimi ^
  -t django.aplicatie_exemplu_produs_materiale ^
  -t django.aplicatie_exemplu_produs_promotii ^
  -t django.aplicatie_exemplu_departament ^
  -t django.aplicatie_exemplu_tipmesaj ^
  -t django.aplicatie_exemplu_tipmesaj_departamente ^
  -f %BACKUP_FILE%

if %errorlevel% equ 0 (
    echo Backup creat cu succes in %BACKUP_FILE%!
) else (
    echo Eroare la crearea backup-ului. Verifica daca pg_dump este in PATH.
)
pause