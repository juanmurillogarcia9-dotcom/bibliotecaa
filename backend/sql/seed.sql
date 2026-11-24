INSERT INTO publishers (name, country)
VALUES
    ('Editorial Demo Norte', 'Colombia'),
    ('Ediciones de Prueba', 'Colombia'),
    ('Editorial Horizonte', 'Mexico'),
    ('Prensa Central', 'Argentina')
ON CONFLICT (name) DO NOTHING;

INSERT INTO authors (name, biography)
VALUES
    ('Andrea Rios', 'Autora ficticia para datos de demostracion.'),
    ('Mateo Soler', 'Autor ficticio para datos de demostracion.'),
    ('Lucia Campos', 'Autora ficticia para datos de demostracion.'),
    ('Elena Prado', 'Autora ficticia para datos de demostracion.'),
    ('Tomas Vega', 'Autor ficticio para datos de demostracion.'),
    ('Camila Duarte', 'Autora ficticia para datos de demostracion.'),
    ('Daniel Luna', 'Autor ficticio para datos de demostracion.'),
    ('Sofia Beltran', 'Autora ficticia para datos de demostracion.')
ON CONFLICT (name) DO NOTHING;

INSERT INTO categories (name)
VALUES
    ('Literatura'),
    ('Ciencia'),
    ('Historia'),
    ('Tecnologia'),
    ('Arte'),
    ('Viajes')
ON CONFLICT (name) DO NOTHING;

INSERT INTO books (title, author, isbn, category, stock_total, stock_available, publisher_id)
SELECT seed.title, seed.author, seed.isbn, seed.category, seed.stock_total,
       seed.stock_total, publishers.id
FROM (
    VALUES
        ('La biblioteca de papel', 'Andrea Rios', 'ISBN-DEMO-0001', 'Literatura', 4, 'Editorial Demo Norte'),
        ('Pequenos experimentos', 'Mateo Soler', 'ISBN-DEMO-0002', 'Ciencia', 3, 'Ediciones de Prueba'),
        ('Mapas de otros tiempos', 'Lucia Campos', 'ISBN-DEMO-0003', 'Historia', 2, 'Editorial Demo Norte'),
        ('Relatos del patio', 'Andrea Rios', 'ISBN-DEMO-0004', 'Literatura', 5, 'Ediciones de Prueba'),
        ('Preguntas para el cielo', 'Mateo Soler', 'ISBN-DEMO-0005', 'Ciencia', 3, 'Editorial Demo Norte'),
        ('La casa de los mapas', 'Elena Prado', 'ISBN-DEMO-0006', 'Viajes', 4, 'Editorial Horizonte'),
        ('Inventario de estrellas', 'Tomas Vega', 'ISBN-DEMO-0007', 'Ciencia', 3, 'Prensa Central'),
        ('Un taller de ideas', 'Camila Duarte', 'ISBN-DEMO-0008', 'Arte', 5, 'Editorial Demo Norte'),
        ('Codigo para curiosos', 'Daniel Luna', 'ISBN-DEMO-0009', 'Tecnologia', 4, 'Ediciones de Prueba'),
        ('La ruta de la lluvia', 'Sofia Beltran', 'ISBN-DEMO-0010', 'Viajes', 3, 'Editorial Horizonte'),
        ('Retratos de domingo', 'Elena Prado', 'ISBN-DEMO-0011', 'Literatura', 2, 'Prensa Central'),
        ('El jardin invisible', 'Camila Duarte', 'ISBN-DEMO-0012', 'Arte', 4, 'Editorial Demo Norte'),
        ('Cronicas del puerto', 'Tomas Vega', 'ISBN-DEMO-0013', 'Historia', 3, 'Editorial Horizonte'),
        ('Pequena guia digital', 'Daniel Luna', 'ISBN-DEMO-0014', 'Tecnologia', 5, 'Prensa Central'),
        ('Voces del camino', 'Sofia Beltran', 'ISBN-DEMO-0015', 'Literatura', 3, 'Ediciones de Prueba')
) AS seed(title, author, isbn, category, stock_total, publisher_name)
JOIN publishers ON publishers.name = seed.publisher_name
ON CONFLICT (isbn) DO NOTHING;

INSERT INTO members (name, email, phone, active)
VALUES
    ('Lectora Demo Uno', 'lectora1@example.com', '3000000001', TRUE),
    ('Lector Demo Dos', 'lector2@example.com', '3000000002', TRUE),
    ('Lectora Demo Tres', 'lectora3@example.com', NULL, TRUE),
    ('Lector Demo Cuatro', 'lector4@example.com', '3000000004', TRUE),
    ('Lectora Demo Cinco', 'lectora5@example.com', '3000000005', TRUE),
    ('Lector Demo Seis', 'lector6@example.com', NULL, TRUE),
    ('Lectora Demo Siete', 'lectora7@example.com', '3000000007', TRUE),
    ('Lector Demo Ocho', 'lector8@example.com', '3000000008', FALSE)
ON CONFLICT (email) DO NOTHING;

INSERT INTO book_authors (book_id, author_id)
SELECT books.id, authors.id
FROM books
JOIN authors ON authors.name = books.author
WHERE books.isbn LIKE 'ISBN-DEMO-%'
ON CONFLICT DO NOTHING;

INSERT INTO book_categories (book_id, category_id)
SELECT books.id, categories.id
FROM books
JOIN categories ON categories.name = books.category
WHERE books.isbn LIKE 'ISBN-DEMO-%'
ON CONFLICT DO NOTHING;

INSERT INTO loans (book_id, member_id, loan_date, due_date, returned_at)
SELECT books.id, members.id, DATE '2024-01-15', DATE '2024-01-29', DATE '2024-01-28'
FROM books
CROSS JOIN members
WHERE books.isbn = 'ISBN-DEMO-0001'
  AND members.email = 'lectora1@example.com'
  AND NOT EXISTS (
      SELECT 1
      FROM loans
      WHERE loans.book_id = books.id
        AND loans.member_id = members.id
        AND loans.loan_date = DATE '2024-01-15'
  );

WITH requested(isbn, email, loan_date, due_date) AS (
    VALUES
        ('ISBN-DEMO-0002', 'lector2@example.com', DATE '2026-11-23', DATE '2026-12-07'),
        ('ISBN-DEMO-0006', 'lector4@example.com', DATE '2026-11-22', DATE '2026-12-06'),
        ('ISBN-DEMO-0008', 'lectora5@example.com', DATE '2026-11-21', DATE '2026-12-05')
),
inserted AS (
    INSERT INTO loans (book_id, member_id, loan_date, due_date)
    SELECT books.id, members.id, requested.loan_date, requested.due_date
    FROM requested
    JOIN books ON books.isbn = requested.isbn AND books.stock_available > 0
    JOIN members ON members.email = requested.email
    WHERE NOT EXISTS (
        SELECT 1
        FROM loans
        WHERE loans.book_id = books.id
          AND loans.member_id = members.id
          AND loans.loan_date = requested.loan_date
    )
    RETURNING book_id
)
UPDATE books
SET stock_available = stock_available - 1
FROM inserted
WHERE books.id = inserted.book_id;

WITH requested(isbn, email, reservation_date, status) AS (
    VALUES
        ('ISBN-DEMO-0003', 'lectora3@example.com', DATE '2026-11-21', 'pending'),
        ('ISBN-DEMO-0007', 'lector6@example.com', DATE '2026-11-22', 'pending'),
        ('ISBN-DEMO-0010', 'lectora7@example.com', DATE '2026-11-23', 'pending'),
        ('ISBN-DEMO-0002', 'lector2@example.com', DATE '2024-01-16', 'cancelled')
)
INSERT INTO reservations (book_id, member_id, reservation_date, status)
SELECT books.id, members.id, requested.reservation_date, requested.status
FROM requested
JOIN books ON books.isbn = requested.isbn
JOIN members ON members.email = requested.email
WHERE NOT EXISTS (
    SELECT 1
    FROM reservations
    WHERE reservations.book_id = books.id
      AND reservations.member_id = members.id
      AND reservations.reservation_date = requested.reservation_date
);
