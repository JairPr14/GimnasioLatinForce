# LatinForce - Sistema de Gestión de Gimnasio

Sistema web local para gestión administrativa de un gimnasio. Django + PostgreSQL.

## Requisitos

- Python 3.10+
- PostgreSQL
- pip

## Configuración inicial

### 1. Crear entorno virtual (recomendado)

```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar base de datos PostgreSQL

**Opción A - Script Python (recomendado):**
```bash
python scripts/create_db.py
```

**Opción B - Manualmente con psql o pgAdmin:**
```sql
CREATE DATABASE latinforce_db;
```

Por defecto usa: usuario `postgres`, contraseña `postgres`, host `localhost`, puerto `5432`.

### 4. Variables de entorno (opcional)

Crear archivo `.env` o definir variables:
- DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

Si no se definen, se usan: latinforce_db, postgres, postgres, localhost, 5432

### 5. Migraciones

```bash
python manage.py migrate
```

### 6. Crear superusuario

```bash
python manage.py createsuperuser
```

### 7. Ejecutar servidor

```bash
python manage.py runserver
```

Abrir http://127.0.0.1:8000/

## Estructura del proyecto

- **config/**: Configuración del proyecto
- **core/**: Utilidades y plantilla base
- **usuarios/**: Autenticación (login/logout)
- **dashboard/**: Panel principal
- **socios, membresias, pagos, asistencias, gastos, inventario, reportes/**: Módulos (por implementar)
