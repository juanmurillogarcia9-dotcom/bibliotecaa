import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from .core.database import Base, SessionLocal
from .models import Autor, Categoria, Libro, Prestamo, Socio

logger = logging.getLogger(__name__)
ModelT = TypeVar("ModelT", bound=Base)

AUTHORS = (
    ("Andrea Rios", "Colombia", 1982),
    ("Mateo Soler", "Colombia", 1976),
    ("Lucia Campos", "Mexico", 1990),
    ("Elena Prado", "Argentina", 1985),
    ("Tomas Vega", "Chile", 1979),
    ("Camila Duarte", "Colombia", 1988),
    ("Daniel Luna", "Mexico", 1981),
    ("Sofia Beltran", "Argentina", 1992),
)

CATEGORIES = (
    ("literatura", "Novela, cuento y poesia"),
    ("ciencia", "Ideas para entender el mundo"),
    ("historia", "Relatos y estudios del pasado"),
    ("tecnologia", "Computacion e innovacion"),
    ("arte", "Creacion, diseno y cultura visual"),
    ("viajes", "Lugares, rutas y exploracion"),
)

MEMBERS = (
    ("Lectora Demo Uno", "lectora1@example.com", "+573000000001"),
    ("Lector Demo Dos", "lector2@example.com", "+573000000002"),
    ("Lectora Demo Tres", "lectora3@example.com", None),
    ("Lector Demo Cuatro", "lector4@example.com", "+573000000004"),
    ("Lectora Demo Cinco", "lectora5@example.com", "+573000000005"),
    ("Lector Demo Seis", "lector6@example.com", None),
    ("Lectora Demo Siete", "lectora7@example.com", "+573000000007"),
    ("Lector Demo Ocho", "lector8@example.com", "+573000000008"),
)

BOOKS = (
    ("La biblioteca de papel", "9780000000001", 2018, 4, "Andrea Rios", ("literatura", "historia")),
    ("Pequenos experimentos", "9780000000002", 2021, 3, "Mateo Soler", ("ciencia",)),
    ("Mapas de otros tiempos", "9780000000003", 2016, 2, "Lucia Campos", ("historia", "viajes")),
    ("Relatos del patio", "9780000000004", 2020, 5, "Andrea Rios", ("literatura",)),
    ("Preguntas para el cielo", "9780000000005", 2023, 3, "Mateo Soler", ("ciencia",)),
    ("La casa de los mapas", "9780000000006", 2019, 4, "Elena Prado", ("viajes", "literatura")),
    ("Inventario de estrellas", "9780000000007", 2017, 3, "Tomas Vega", ("ciencia",)),
    ("Un taller de ideas", "9780000000008", 2022, 5, "Camila Duarte", ("arte",)),
    ("Codigo para curiosos", "9780000000009", 2024, 4, "Daniel Luna", ("tecnologia", "ciencia")),
    ("La ruta de la lluvia", "9780000000010", 2015, 3, "Sofia Beltran", ("viajes",)),
    ("Retratos de domingo", "9780000000011", 2014, 2, "Elena Prado", ("literatura",)),
    ("El jardin invisible", "9780000000012", 2020, 4, "Camila Duarte", ("arte", "literatura")),
    ("Cronicas del puerto", "9780000000013", 2013, 3, "Tomas Vega", ("historia",)),
    ("Pequena guia digital", "9780000000014", 2025, 5, "Daniel Luna", ("tecnologia",)),
    ("Voces del camino", "9780000000015", 2021, 3, "Sofia Beltran", ("literatura", "viajes")),
)


def _get_or_add(
    db: Session,
    model: type[ModelT],
    field: str,
    value: str,
    create_values: dict[str, object],
) -> tuple[ModelT, bool]:
    instance = db.scalar(select(model).where(getattr(model, field) == value))
    if instance is not None:
        return instance, False
    instance = model(**create_values)
    db.add(instance)
    db.flush()
    return instance, True


def seed_demo_data() -> None:
    created = {"autores": 0, "categorias": 0, "socios": 0, "libros": 0, "prestamos": 0}
    with SessionLocal.begin() as db:
        authors: dict[str, Autor] = {}
        for name, nationality, birth_year in AUTHORS:
            author, was_created = _get_or_add(
                db,
                Autor,
                "nombre",
                name,
                {
                    "nombre": name,
                    "nacionalidad": nationality,
                    "anio_nacimiento": birth_year,
                },
            )
            authors[name] = author
            created["autores"] += was_created

        categories: dict[str, Categoria] = {}
        for name, description in CATEGORIES:
            category, was_created = _get_or_add(
                db,
                Categoria,
                "nombre",
                name,
                {"nombre": name, "descripcion": description},
            )
            categories[name] = category
            created["categorias"] += was_created

        members: dict[str, Socio] = {}
        for name, email, phone in MEMBERS:
            member, was_created = _get_or_add(
                db,
                Socio,
                "email",
                email,
                {"nombre": name, "email": email, "telefono": phone, "activo": True},
            )
            members[email] = member
            created["socios"] += was_created

        books: dict[str, Libro] = {}
        for title, isbn, year, copies, author_name, category_names in BOOKS:
            book = db.scalar(select(Libro).where(Libro.isbn == isbn))
            if book is None:
                book = Libro(
                    titulo=title,
                    isbn=isbn,
                    anio_publicacion=year,
                    ejemplares=copies,
                    autor=authors[author_name],
                    categorias=[categories[name] for name in category_names],
                )
                db.add(book)
                db.flush()
                created["libros"] += 1
            books[isbn] = book

        today = date.today()
        loan_seeds = (
            ("9780000000002", "lector2@example.com", today - timedelta(days=3), 14, None, Decimal("0.00"), False),
            ("9780000000006", "lector4@example.com", today - timedelta(days=2), 14, None, Decimal("0.00"), False),
            ("9780000000008", "lectora5@example.com", today - timedelta(days=1), 14, None, Decimal("0.00"), False),
            ("9780000000003", "lectora3@example.com", today - timedelta(days=35), 14, today - timedelta(days=16), Decimal("1.50"), True),
        )
        for isbn, email, loan_date, duration, returned, fine, fine_paid in loan_seeds:
            book = books[isbn]
            member = members[email]
            existing = db.scalar(
                select(Prestamo.id).where(
                    Prestamo.libro_id == book.id,
                    Prestamo.socio_id == member.id,
                )
            )
            if existing is not None:
                continue
            db.add(
                Prestamo(
                    libro=book,
                    socio=member,
                    fecha_prestamo=loan_date,
                    fecha_limite=loan_date + timedelta(days=duration),
                    fecha_devolucion=returned,
                    multa=fine,
                    multa_pagada=fine_paid,
                )
            )
            created["prestamos"] += 1

    logger.info(
        "Datos de demostracion verificados: %s autores, %s categorias, "
        "%s socios, %s libros y %s prestamos nuevos.",
        created["autores"],
        created["categorias"],
        created["socios"],
        created["libros"],
        created["prestamos"],
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_demo_data()
