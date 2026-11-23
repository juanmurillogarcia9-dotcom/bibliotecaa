const notice = document.querySelector("#notice");
const state = {
  books: [],
  authors: [],
  categories: [],
  members: [],
  loans: [],
  summary: {},
};

function showNotice(message, isError = false) {
  notice.textContent = message;
  notice.className = `notice visible ${isError ? "error" : "success"}`;
  window.clearTimeout(showNotice.timeout);
  showNotice.timeout = window.setTimeout(() => {
    notice.className = "notice";
  }, 4500);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

function formatDate(value) {
  if (!value) return "—";
  const [year, month, day] = value.split("-").map(Number);
  return new Intl.DateTimeFormat("es-CO", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(year, month - 1, day));
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: options.body
      ? { "Content-Type": "application/json", ...options.headers }
      : options.headers,
  });
  if (!response.ok) {
    const body = response.headers.get("content-type")?.includes("application/json")
      ? await response.json()
      : { detail: response.statusText };
    throw new Error(body.detail || `Error HTTP ${response.status}`);
  }
  return response.status === 204 ? null : response.json();
}

function emptyRow(target, message, columns) {
  target.innerHTML = `<tr><td class="empty" colspan="${columns}">${escapeHtml(message)}</td></tr>`;
}

function renderReferenceFields() {
  document.querySelector("#book-author").innerHTML = state.authors
    .map((author) => `<option value="${author.id}">${escapeHtml(author.nombre)}</option>`)
    .join("") || `<option value="">Primero agrega un autor</option>`;

  document.querySelector("#book-categories").innerHTML = state.categories
    .map((category) => `<option value="${category.id}">${escapeHtml(category.nombre)}</option>`)
    .join("");

  const categoryFilter = document.querySelector("#category-filter");
  const currentCategory = categoryFilter.value;
  categoryFilter.innerHTML = `<option value="">Todas</option>${state.categories
    .map((category) => `<option value="${category.id}">${escapeHtml(category.nombre)}</option>`)
    .join("")}`;
  categoryFilter.value = state.categories.some((category) => String(category.id) === currentCategory)
    ? currentCategory
    : "";
}

function renderBooks() {
  const search = document.querySelector("#book-search").value.trim().toLocaleLowerCase("es");
  const categoryId = document.querySelector("#category-filter").value;
  const visibleBooks = state.books.filter((book) => {
    const matchesSearch = [book.titulo, book.autor.nombre, book.isbn]
      .some((value) => value.toLocaleLowerCase("es").includes(search));
    const matchesCategory = !categoryId
      || book.categorias.some((category) => String(category.id) === categoryId);
    return matchesSearch && matchesCategory;
  });
  const target = document.querySelector("#books-table");
  if (!visibleBooks.length) {
    emptyRow(target, state.books.length ? "No encontramos libros con esos filtros." : "Todavía no hay libros registrados.", 4);
  } else {
    target.innerHTML = visibleBooks.map((book, index) => {
      const stockClass = book.disponibles === 0
        ? "stock-out"
        : book.disponibles <= 1 ? "stock-low" : "stock-available";
      const stockText = book.disponibles === 0
        ? "Agotado"
        : `${book.disponibles} de ${book.ejemplares} disponibles`;
      const categories = book.categorias.map((category) => category.nombre).join(", ");
      return `<tr>
        <td><div class="book-cell"><span class="book-cover-mini cover-${index % 4}">✦</span><span><span class="table-primary">${escapeHtml(book.titulo)}</span><span class="table-secondary">${escapeHtml(book.autor.nombre)}</span></span></div></td>
        <td>${escapeHtml(book.anio_publicacion)}</td>
        <td><span class="category-pill">${escapeHtml(categories)}</span></td>
        <td><span class="stock-pill ${stockClass}">${stockText}</span></td>
      </tr>`;
    }).join("");
  }

  const availableBooks = state.books.filter((book) => book.disponibles > 0);
  document.querySelector("#loan-book").innerHTML = availableBooks
    .map((book) => `<option value="${book.id}">${escapeHtml(book.titulo)} (${book.disponibles})</option>`)
    .join("") || `<option value="">No hay ejemplares disponibles</option>`;

  document.querySelector("#stat-titles").textContent = state.summary.total_libros ?? state.books.length;
  document.querySelector("#stat-copies").textContent =
    (state.summary.total_ejemplares ?? 0) - (state.summary.total_prestados ?? 0);
  document.querySelector("#book-nav-count").textContent = state.books.length;
}

function renderMembers() {
  const target = document.querySelector("#members-table");
  if (!state.members.length) {
    emptyRow(target, "Todavía no hay socios registrados.", 4);
  } else {
    target.innerHTML = state.members.map((member) => `
      <tr>
        <td><div class="member-cell"><span class="member-avatar">${escapeHtml(member.nombre.trim().charAt(0).toLocaleUpperCase("es"))}</span><span class="table-primary">${escapeHtml(member.nombre)}</span></div></td>
        <td>${escapeHtml(member.email)}</td>
        <td>${escapeHtml(member.telefono || "—")}</td>
        <td><span class="status-pill ${member.activo ? "status-activo" : "status-inactive"}">${member.activo ? "Activo" : "Inactivo"}</span></td>
      </tr>`).join("");
  }

  const activeMembers = state.members.filter((member) => member.activo);
  document.querySelector("#loan-member").innerHTML = activeMembers
    .map((member) => `<option value="${member.id}">${escapeHtml(member.nombre)}</option>`)
    .join("") || `<option value="">No hay socios activos</option>`;
  document.querySelector("#stat-members").textContent = state.summary.socios_activos ?? activeMembers.length;
  document.querySelector("#member-count-label").textContent = `${state.members.length} socios`;
}

function renderDashboard() {
  const overdue = state.summary.prestamos_vencidos ?? 0;
  document.querySelector("#stat-loans").textContent = state.summary.total_prestados ?? 0;
  document.querySelector("#stat-overdue").textContent = overdue
    ? `${overdue} requieren atención`
    : "En circulación";
  document.querySelector("#loan-nav-count").textContent = state.summary.total_prestados ?? 0;

  const books = new Map(state.books.map((book) => [book.id, book.titulo]));
  const members = new Map(state.members.map((member) => [member.id, member.nombre]));
  const activeLoans = state.loans
    .filter((loan) => loan.estado !== "devuelto")
    .sort((a, b) => a.fecha_limite.localeCompare(b.fecha_limite))
    .slice(0, 5);
  const target = document.querySelector("#dashboard-loans");
  if (!activeLoans.length) {
    emptyRow(target, "Todavía no hay préstamos activos.", 4);
  } else {
    target.innerHTML = activeLoans.map((loan) => `
      <tr>
        <td><span class="table-primary">${escapeHtml(books.get(loan.libro_id) || `Libro #${loan.libro_id}`)}</span></td>
        <td>${escapeHtml(members.get(loan.socio_id) || `Socio #${loan.socio_id}`)}</td>
        <td>${formatDate(loan.fecha_limite)}</td>
        <td><span class="status-pill status-${loan.estado}">${loan.estado === "vencido" ? "Vencido" : "En curso"}</span></td>
      </tr>`).join("");
  }

  const targetCategories = document.querySelector("#category-list");
  targetCategories.innerHTML = state.categories.length
    ? state.categories.slice(0, 5).map((category) => {
      const total = state.books.filter((book) =>
        book.categorias.some((item) => item.id === category.id)).length;
      return `<div class="category-row"><span class="category-dot"></span><span class="category-name">${escapeHtml(category.nombre)}</span><span class="category-total">${total} ${total === 1 ? "libro" : "libros"}</span></div>`;
    }).join("")
    : `<p class="empty">Las categorías aparecerán al agregarlas.</p>`;
}

function renderLoans() {
  const filter = document.querySelector("#loan-status-filter").value;
  const loans = state.loans.filter((loan) => !filter || loan.estado === filter);
  const target = document.querySelector("#loans-table");
  if (!loans.length) {
    const message = filter === "vencido" ? "No hay préstamos vencidos." : "No hay préstamos para mostrar.";
    emptyRow(target, message, 6);
    return;
  }

  const books = new Map(state.books.map((book) => [book.id, book.titulo]));
  const members = new Map(state.members.map((member) => [member.id, member.nombre]));
  target.innerHTML = loans.map((loan) => {
    const status = loan.estado === "devuelto" ? "Devuelto" : loan.estado === "vencido" ? "Vencido" : "En curso";
    const action = loan.estado === "devuelto"
      ? "—"
      : `<button class="small-button" data-return-loan="${loan.id}">Registrar devolución</button>`;
    return `<tr>
      <td><span class="table-primary">${escapeHtml(books.get(loan.libro_id) || `Libro #${loan.libro_id}`)}</span></td>
      <td>${escapeHtml(members.get(loan.socio_id) || `Socio #${loan.socio_id}`)}</td>
      <td>${formatDate(loan.fecha_prestamo)}</td>
      <td>${formatDate(loan.fecha_limite)}</td>
      <td><span class="status-pill status-${loan.estado}">${status}</span></td>
      <td>${action}</td>
    </tr>`;
  }).join("");
}

async function refreshData() {
  const [bookPage, authorPage, categoryPage, memberPage, loanPage, summary] = await Promise.all([
    request("/api/v1/libros?limit=100"),
    request("/api/v1/autores?limit=100"),
    request("/api/v1/categorias?limit=100"),
    request("/api/v1/socios?limit=100"),
    request("/api/v1/prestamos?limit=100"),
    request("/api/v1/reportes/resumen"),
  ]);
  state.books = bookPage.items;
  state.authors = authorPage.items;
  state.categories = categoryPage.items;
  state.members = memberPage.items;
  state.loans = loanPage.items;
  state.summary = summary;
  renderReferenceFields();
  renderBooks();
  renderMembers();
  renderDashboard();
  renderLoans();
}

function showPanel(panelId) {
  document.querySelectorAll(".nav-link, .panel").forEach((element) => element.classList.remove("active"));
  const link = document.querySelector(`.nav-link[data-panel="${panelId}"]`);
  link.classList.add("active");
  document.querySelector(`#${panelId}`).classList.add("active");
  document.querySelector("#current-section").textContent = link.querySelector("span:nth-child(2)").textContent;
}

function toggleForm(formId) {
  document.querySelector(`#${formId}`).classList.toggle("hidden");
}

document.querySelectorAll(".nav-link").forEach((link) => {
  link.addEventListener("click", () => showPanel(link.dataset.panel));
});
document.querySelectorAll('[data-action="view-loans"]').forEach((button) => {
  button.addEventListener("click", () => showPanel("loans-panel"));
});
document.querySelectorAll('[data-action="view-books"]').forEach((button) => {
  button.addEventListener("click", () => showPanel("books-panel"));
});
document.querySelectorAll('[data-action="new-book"]').forEach((button) => {
  button.addEventListener("click", () => {
    showPanel("books-panel");
    document.querySelector("#book-form").classList.remove("hidden");
    document.querySelector("#book-form").scrollIntoView({ behavior: "smooth", block: "center" });
    document.querySelector('#book-form input[name="titulo"]').focus({ preventScroll: true });
  });
});

document.querySelector("#show-book-form").addEventListener("click", () => toggleForm("book-form"));
document.querySelector("#show-author-form").addEventListener("click", () => toggleForm("author-form"));
document.querySelector("#show-category-form").addEventListener("click", () => toggleForm("category-form"));
document.querySelector("#show-member-form").addEventListener("click", () => toggleForm("member-form"));
document.querySelector("#book-search").addEventListener("input", renderBooks);
document.querySelector("#category-filter").addEventListener("change", renderBooks);
document.querySelector("#loan-status-filter").addEventListener("change", renderLoans);

document.querySelector("#book-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form));
  values.anio_publicacion = Number(values.anio_publicacion);
  values.ejemplares = Number(values.ejemplares);
  values.autor_id = Number(values.autor_id);
  values.categoria_ids = new FormData(form).getAll("categoria_ids").map(Number);
  try {
    await request("/api/v1/libros", { method: "POST", body: JSON.stringify(values) });
    form.reset();
    form.classList.add("hidden");
    await refreshData();
    showNotice("Libro registrado.");
  } catch (error) {
    showNotice(error.message, true);
  }
});

document.querySelector("#author-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form));
  values.anio_nacimiento = values.anio_nacimiento ? Number(values.anio_nacimiento) : null;
  values.nacionalidad = values.nacionalidad || null;
  try {
    await request("/api/v1/autores", { method: "POST", body: JSON.stringify(values) });
    form.reset();
    form.classList.add("hidden");
    await refreshData();
    showNotice("Autor registrado.");
  } catch (error) {
    showNotice(error.message, true);
  }
});

document.querySelector("#category-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form));
  values.descripcion = values.descripcion || null;
  try {
    await request("/api/v1/categorias", { method: "POST", body: JSON.stringify(values) });
    form.reset();
    form.classList.add("hidden");
    await refreshData();
    showNotice("Categoría registrada.");
  } catch (error) {
    showNotice(error.message, true);
  }
});

document.querySelector("#member-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form));
  values.telefono = values.telefono || null;
  try {
    await request("/api/v1/socios", { method: "POST", body: JSON.stringify(values) });
    form.reset();
    form.classList.add("hidden");
    await refreshData();
    showNotice("Socio registrado.");
  } catch (error) {
    showNotice(error.message, true);
  }
});

document.querySelector("#loan-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form));
  values.libro_id = Number(values.libro_id);
  values.socio_id = Number(values.socio_id);
  values.dias = Number(values.dias);
  try {
    await request("/api/v1/prestamos", { method: "POST", body: JSON.stringify(values) });
    form.reset();
    await refreshData();
    showNotice("Préstamo registrado.");
  } catch (error) {
    showNotice(error.message, true);
  }
});

document.querySelector("#loans-table").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-return-loan]");
  if (!button) return;
  try {
    await request(`/api/v1/prestamos/${button.dataset.returnLoan}/devolucion`, {
      method: "POST",
      body: JSON.stringify({ fecha_devolucion: new Date().toISOString().slice(0, 10) }),
    });
    await refreshData();
    showNotice("Devolución registrada.");
  } catch (error) {
    showNotice(error.message, true);
  }
});

document.querySelector('#book-form input[name="anio_publicacion"]').max = new Date().getFullYear();
document.querySelector('#author-form input[name="anio_nacimiento"]').max = new Date().getFullYear();
document.querySelector("#today-label").textContent = new Intl.DateTimeFormat("es-CO", {
  day: "numeric",
  month: "short",
  year: "numeric",
}).format(new Date());

refreshData().catch((error) => showNotice(`No se pudo cargar la biblioteca: ${error.message}`, true));
