# biblioteca-13

API asíncrona de biblioteca construida con FastAPI, Pydantic v2 y PostgreSQL mediante psycopg 3.

## Estructura

```text
backend/
  controllers/          # Lógica de negocio y consultas
  core/
    config.py           # Variables de entorno
    database.py         # Pool asíncrono psycopg y dependencias
  models/
    records.py          # Tipos de los registros devueltos por PostgreSQL
  routes/               # Endpoints FastAPI
    libros.py
    usuarios.py
    prestamos.py
  schemas/              # Esquemas Pydantic v2 por dominio
    libros.py
    usuarios.py
    prestamos.py
  main.py               # Aplicación, CORS y manejo común de errores
  sql/
    schema.sql          # Nueve tablas, restricciones e índices
    seed.sql            # Datos de demostración repetibles
frontend/
  index.html
  app.js
  styles.css
.env                  # Crear copiando .env.example; credenciales locales, ignorado por Git
.env.example
.gitignore
requirements.txt
```

## Puesta en marcha (Windows / PowerShell)

1. Instalar e iniciar PostgreSQL; crear una base llamada `biblioteca13`.
2. Activar el entorno virtual e instalar dependencias:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Configurar `.env` tomando `.env.example` como referencia. Define
   `ADMIN_EMAIL`, `ADMIN_PASSWORD` (mínimo 12 caracteres) y
   `SESSION_SECRET` (mínimo 32 bytes). No compartas ni subas `.env`.
4. Crear tablas y datos de demostración (comando repetible):

   ```powershell
   python -m backend.bootstrap
   ```

5. Iniciar la aplicación:

   ```powershell
   python -m backend.main
   ```

   Abre `http://127.0.0.1:8000`. Para detenerla, presiona `Ctrl+C`.
   `python -m backend.main` usa el puerto indicado por `PORT` y un event loop
   compatible con el pool asíncrono de psycopg 3 en Windows.

Uvicorn no carga `.env` por sí mismo; el arranque `python -m backend.main` utiliza
el puerto definido por la aplicación y `uvicorn backend.main:app` permite recarga.

La interfaz privada queda disponible en `/`, la documentación interactiva en
`/docs`, y la comprobación de salud en `/health`. Las rutas de datos se
encuentran bajo `/api` y requieren una sesión iniciada.

## Acceso privado

Hay una sola cuenta de administración, configurada en `.env`; no hay registro
público. El acceso usa una cookie `HttpOnly` firmada con vencimiento de 12 horas.
En producción, sirve la app por HTTPS y configura `COOKIE_SECURE=true`.

Validaciones de acceso:

- Correo con formato válido.
- Contraseña de 12 a 128 caracteres.
- Las credenciales incorrectas muestran un mensaje genérico.
- Las rutas privadas de la API responden `401` si no existe una sesión válida.

El esquema contiene `books`, `members`, `loans`, `authors`, `categories`,
`publishers`, `book_authors`, `book_categories` y `reservations`. La interfaz
permite consultar libros, lectores y préstamos, registrar libros y lectores,
crear préstamos y registrar devoluciones.

## Endpoints principales

- `GET/POST /api/libros`; `GET/PATCH/DELETE /api/libros/{id}`
- `GET/POST /api/usuarios`; `GET/PATCH/DELETE /api/usuarios/{id}`
- `POST /api/prestamos` para crear préstamos
- `GET /api/prestamos?status=active|overdue|all` (paginado con `page` y `page_size`)
- `POST /api/prestamos/{id}/devolucion` para registrar una devolución

Las búsquedas de libros aceptan `search` (título, autor o ISBN) y `category`.
Los usuarios aceptan `search` (nombre o correo) y `active`. La paginación de
libros y usuarios devuelve `items`, `total`, `page` y `page_size`.

La duración predeterminada de un préstamo es de 14 días. Los préstamos bloquean
la fila del libro durante la operación, de modo que préstamos concurrentes no
puedan reducir el stock por debajo de cero. El borrado de libros o usuarios
con préstamos asociados se rechaza por las claves foráneas. Las restricciones
de unicidad generan HTTP 409.
