"""
Script para crear la base de datos latinforce_db en PostgreSQL.
Ejecutar: python scripts/create_db.py

Requiere PostgreSQL instalado y en ejecución.
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os

DB_NAME = os.environ.get('DB_NAME', 'latinforce_db')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')

def main():
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute(f'CREATE DATABASE {DB_NAME};')
        print(f'Base de datos "{DB_NAME}" creada correctamente.')
        cur.close()
        conn.close()
    except psycopg2.Error as e:
        if 'already exists' in str(e):
            print(f'La base de datos "{DB_NAME}" ya existe.')
        else:
            print(f'Error: {e}')
            raise

if __name__ == '__main__':
    main()
