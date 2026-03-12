"""
Script de configuración: crear BD, migrar y crear superusuario.
Ejecutar: python scripts/setup_postgres.py

Ajusta DB_PASSWORD en .env con la contraseña real de PostgreSQL.
Para superusuario: DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD
"""
import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run(cmd, check=True):
    result = subprocess.run(cmd, shell=True)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result.returncode

print("1. Creando base de datos...")
run("python scripts/create_db.py")

print("\n2. Ejecutando migraciones...")
run("python manage.py migrate")

print("\n3. Creando superusuario...")
# Usar variables de entorno para creación no interactiva
username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@latinforce.local")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin123")
os.environ.setdefault("DJANGO_SUPERUSER_USERNAME", username)
os.environ.setdefault("DJANGO_SUPERUSER_EMAIL", email)
os.environ.setdefault("DJANGO_SUPERUSER_PASSWORD", password)
run("python manage.py createsuperuser --noinput")

print("\nListo. Superusuario:", username, "| Email:", email)
print("Inicia el servidor: python manage.py runserver")
