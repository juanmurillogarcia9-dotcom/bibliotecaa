# Biblioteca

API de gestión de biblioteca con FastAPI, PostgreSQL, SQLAlchemy y Alembic.
Incluye una interfaz web servida desde la misma aplicación.

## Puesta en marcha

1. Instala las dependencias con `pip install -r requirements.txt`.
2. Copia `.env.example` a `.env` y configura `DATABASE_URL` y `SECRET_KEY`.
3. Aplica las migraciones con `alembic upgrade head`.
4. Carga los datos de demostración con `python -m app.seed_demo`.
5. Inicia el servidor con `uvicorn app.main:app --reload`.
6. Abre `http://127.0.0.1:8000`.

La interfaz web está en `/`; la documentación de la API está disponible en
`/docs`. El script de datos de demostración se puede ejecutar varias veces:
agrega los registros que falten sin reemplazar los existentes.

## API

Los endpoints de gestión están bajo `/api/v1`: autores, categorías, libros,
socios, préstamos y reportes. La base de datos se crea y actualiza mediante
Alembic; no se deben crear las tablas manualmente.
