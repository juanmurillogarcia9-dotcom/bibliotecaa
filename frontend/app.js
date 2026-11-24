const notice = document.querySelector("#notice");
const state = { books: [], members: [], loans: [] };

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

function todayISO() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
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
    const detail = Array.isArray(body.detail)
      ? body.detail.map((item) => item.msg).join(". ")
      : body.detail;
    const error = new Error(detail || `Error HTTP ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return response.status === 204 ? null : response.json();
}

function showLoginError(message = "") {
  const error = document.querySelector("#login-error");
  error.textContent = message;
  error.classList.toggle("visible", Boolean(message));
}

function showApp(email) {
  document.querySelector("#admin-name").textContent = email;
  document.querySelector("#login-screen").hidden = true;
  document.querySelector("#app-shell").hidden = false;
}

function tableMessage(target, message, columns) {
  target.innerHTML = `<tr><td class="empty" colspan="${columns}">${escapeHtml(message)}</td></tr>`;
}

function renderBooks() {
  const search = document.querySelector("#book-search").value.trim().toLocaleLowerCase("es");
  const category = document.querySelector("#category-filter").value;
  const visibleBooks = state.books.filter((book) => {
    const matchesSearch = [book.title, book.author, book.isbn]
      .some((value) => value.toLocaleLowerCase("es").includes(search));
    return matchesSearch && (!category || book.category === category);
  });
  const target = document.querySelector("#books-table");
  if (!visibleBooks.length) {
    tableMessage(target, state.books.length ? "No encontramos libros con esos filtros." : "Todavía no hay libros registrados.", 4);
  } else {
    target.innerHTML = visibleBooks.map((book, index) => {
      const stockClass = book.stock_available === 0
        ? "stock-out"
        : book.stock_available <= 1 ? "stock-low" : "stock-available";
      const stockText = book.stock_available === 0
        ? "Agotado"
        : `${book.stock_available} de ${book.stock_total} disponibles`;
      return `
      <tr>
        <td><div class="book-cell"><span class="book-cover-mini cover-${index % 4}">✦</span><span><span class="table-primary">${escapeHtml(book.title)}</span><span class="table-secondary">${escapeHtml(book.author)}</span></span></div></td>
        <td>${escapeHtml(book.isbn)}</td>
        <td><span class="category-pill">${escapeHtml(book.category || "Sin categoría")}</span></td>
        <td><span class="stock-pill ${stockClass}">${stockText}</span></td>
      </tr>`;
    }).join("");
  }

  const categories = [...new Set(state.books.map((book) => book.category).filter(Boolean))].sort();
  const categoryFilter = document.querySelector("#category-filter");
  const currentCategory = categoryFilter.value;
  categoryFilter.innerHTML = `<option value="">Todas</option>${categories.map((item) => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join("")}`;
  categoryFilter.value = categories.includes(currentCategory) ? currentCategory : "";

  document.querySelector("#loan-book").innerHTML = state.books
    .filter((book) => book.stock_available > 0)
    .map((book) => `<option value="${book.id}">${escapeHtml(book.title)} (${book.stock_available})</option>`)
    .join("") || `<option value="">No hay ejemplares disponibles</option>`;
  document.querySelector("#stat-titles").textContent = state.books.length;
  document.querySelector("#stat-copies").textContent = state.books.reduce((total, book) => total + book.stock_available, 0);
  document.querySelector("#book-nav-count").textContent = state.books.length;
}

function renderMembers() {
  const target = document.querySelector("#members-table");
  if (!state.members.length) {
    tableMessage(target, "Todavía no hay lectores registrados.", 4);
  } else {
    target.innerHTML = state.members.map((member) => `
      <tr>
        <td><div class="member-cell"><span class="member-avatar">${escapeHtml(member.name.trim().charAt(0).toLocaleUpperCase("es"))}</span><span class="table-primary">${escapeHtml(member.name)}</span></div></td>
        <td>${escapeHtml(member.email)}</td>
        <td>${escapeHtml(member.phone || "—")}</td>
        <td><span class="status-pill ${member.active ? "status-active" : "status-inactive"}">${member.active ? "Activo" : "Inactivo"}</span></td>
      </tr>`).join("");
  }
  const activeMembers = state.members.filter((member) => member.active);
  document.querySelector("#loan-member").innerHTML = activeMembers
    .map((member) => `<option value="${member.id}">${escapeHtml(member.name)}</option>`)
    .join("") || `<option value="">No hay lectores activos</option>`;
  document.querySelector("#stat-members").textContent = activeMembers.length;
  document.querySelector("#member-count-label").textContent = `${state.members.length} lectores`;
}

function renderDashboard() {
  const activeLoans = state.loans.filter((loan) => !loan.returned_at);
  const overdueLoans = activeLoans.filter((loan) => loan.due_date < todayISO());
  document.querySelector("#stat-loans").textContent = activeLoans.length;
  document.querySelector("#stat-overdue").textContent = overdueLoans.length
    ? `${overdueLoans.length} requieren atención`
    : "En circulación";
  document.querySelector("#loan-nav-count").textContent = activeLoans.length;

  const bookNames = new Map(state.books.map((book) => [book.id, book.title]));
  const memberNames = new Map(state.members.map((member) => [member.id, member.name]));
  const target = document.querySelector("#dashboard-loans");
  const recent = [...activeLoans].sort((a, b) => a.due_date.localeCompare(b.due_date)).slice(0, 5);
  if (!recent.length) {
    tableMessage(target, "Todavía no hay préstamos activos.", 4);
  } else {
    target.innerHTML = recent.map((loan) => {
      const overdue = loan.due_date < todayISO();
      return `<tr>
        <td><span class="table-primary">${escapeHtml(bookNames.get(loan.book_id) || `Libro #${loan.book_id}`)}</span></td>
        <td>${escapeHtml(memberNames.get(loan.member_id) || `Lector #${loan.member_id}`)}</td>
        <td>${escapeHtml(loan.due_date)}</td>
        <td><span class="status-pill ${overdue ? "status-overdue" : "status-active"}">${overdue ? "Vencido" : "En curso"}</span></td>
      </tr>`;
    }).join("");
  }

  const counts = new Map();
  state.books.forEach((book) => {
    const category = book.category || "Sin categoría";
    counts.set(category, (counts.get(category) || 0) + 1);
  });
  const topCategories = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 4);
  document.querySelector("#category-list").innerHTML = topCategories.length
    ? topCategories.map(([name, count]) => `<div class="category-row"><span class="category-dot"></span><span class="category-name">${escapeHtml(name)}</span><span class="category-total">${count} ${count === 1 ? "libro" : "libros"}</span></div>`).join("")
    : `<p class="empty">Las categorías aparecerán al agregar libros.</p>`;
}

function renderLoans() {
  const filter = document.querySelector("#loan-status-filter").value;
  const today = todayISO();
  const loans = state.loans.filter((loan) => {
    if (filter === "active") return !loan.returned_at;
    if (filter === "overdue") return !loan.returned_at && loan.due_date < today;
    return true;
  });
  const target = document.querySelector("#loans-table");
  if (!loans.length) {
    const message = filter === "overdue" ? "No hay préstamos vencidos." : "No hay préstamos para mostrar.";
    tableMessage(target, message, 6);
    return;
  }
  const bookNames = new Map(state.books.map((book) => [book.id, book.title]));
  const memberNames = new Map(state.members.map((member) => [member.id, member.name]));
  target.innerHTML = loans.map((loan) => {
    const overdue = !loan.returned_at && loan.due_date < today;
    const status = loan.returned_at ? "Devuelto" : overdue ? "Vencido" : "En curso";
    const statusClass = loan.returned_at ? "status-returned" : overdue ? "status-overdue" : "status-active";
    const action = loan.returned_at
      ? "—"
      : `<button class="small-button" data-return-loan="${loan.id}">Registrar devolución</button>`;
    return `<tr>
      <td><span class="table-primary">${escapeHtml(bookNames.get(loan.book_id) || `Libro #${loan.book_id}`)}</span></td>
      <td>${escapeHtml(memberNames.get(loan.member_id) || `Lector #${loan.member_id}`)}</td>
      <td>${escapeHtml(loan.loan_date)}</td>
      <td>${escapeHtml(loan.due_date)}</td>
      <td><span class="status-pill ${statusClass}">${status}</span></td>
      <td>${action}</td>
    </tr>`;
  }).join("");
}

async function refreshData() {
  const [bookResult, memberResult, loanResult] = await Promise.all([
    request("/api/libros?page_size=100"),
    request("/api/usuarios?page_size=100"),
    request("/api/prestamos?status=all&page_size=100"),
  ]);
  state.books = bookResult.items;
  state.members = memberResult.items;
  state.loans = loanResult;
  renderBooks();
  renderMembers();
  renderDashboard();
  renderLoans();
}

function showPanel(panelId) {
  document.querySelectorAll(".nav-link, .panel").forEach((element) => element.classList.remove("active"));
  const activeLink = document.querySelector(`.nav-link[data-panel="${panelId}"]`);
  activeLink.classList.add("active");
  document.querySelector(`#${panelId}`).classList.add("active");
  document.querySelector("#current-section").textContent = activeLink.querySelector("span:nth-child(2)").textContent;
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
    document.querySelector('#book-form input[name="title"]').focus({ preventScroll: true });
  });
});

document.querySelector("#show-book-form").addEventListener("click", () => {
  document.querySelector("#book-form").classList.toggle("hidden");
});
document.querySelector("#show-member-form").addEventListener("click", () => {
  document.querySelector("#member-form").classList.toggle("hidden");
});
document.querySelector("#book-search").addEventListener("input", renderBooks);
document.querySelector("#category-filter").addEventListener("change", renderBooks);
document.querySelector("#loan-status-filter").addEventListener("change", renderLoans);

document.querySelector("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const credentials = Object.fromEntries(new FormData(form));
  showLoginError();
  try {
    const session = await request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
    form.reset();
    showApp(session.email);
    await refreshData().catch((error) => showNotice(`No se pudo cargar la biblioteca: ${error.message}`, true));
  } catch (error) {
    showLoginError(error.message);
  }
});

document.querySelector("#logout-button").addEventListener("click", async () => {
  try {
    await request("/api/auth/logout", { method: "POST" });
    document.querySelector("#app-shell").hidden = true;
    document.querySelector("#login-screen").hidden = false;
    showLoginError();
    document.querySelector('#login-form input[name="email"]').focus();
  } catch (error) {
    showNotice(`No se pudo cerrar la sesión: ${error.message}`, true);
  }
});

document.querySelector("#book-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form));
  values.stock_total = Number(values.stock_total);
  values.category = values.category || null;
  try {
    await request("/api/libros", { method: "POST", body: JSON.stringify(values) });
    form.reset();
    form.classList.add("hidden");
    await refreshData();
    showNotice("Libro registrado.");
  } catch (error) {
    showNotice(error.message, true);
  }
});

document.querySelector("#member-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form));
  values.phone = values.phone || null;
  try {
    await request("/api/usuarios", { method: "POST", body: JSON.stringify(values) });
    form.reset();
    form.classList.add("hidden");
    await refreshData();
    showNotice("Lector registrado.");
  } catch (error) {
    showNotice(error.message, true);
  }
});

document.querySelector("#loan-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(event.currentTarget));
  values.book_id = Number(values.book_id);
  values.member_id = Number(values.member_id);
  if (!values.due_date) delete values.due_date;
  try {
    await request("/api/prestamos", { method: "POST", body: JSON.stringify(values) });
    event.currentTarget.reset();
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
    await request(`/api/prestamos/${button.dataset.returnLoan}/devolucion`, { method: "POST" });
    await refreshData();
    showNotice("Devolución registrada.");
  } catch (error) {
    showNotice(error.message, true);
  }
});

document.querySelector("#today-label").textContent = new Intl.DateTimeFormat("es-CO", {
  day: "numeric",
  month: "short",
  year: "numeric",
}).format(new Date());

async function initialize() {
  let session;
  try {
    session = await request("/api/auth/session");
  } catch (error) {
    document.querySelector("#app-shell").hidden = true;
    document.querySelector("#login-screen").hidden = false;
    if (error.status !== 401) {
      showLoginError(`No se pudo validar la sesión: ${error.message}`);
    }
    return;
  }
  showApp(session.email);
  await refreshData().catch((error) => showNotice(`No se pudo cargar la biblioteca: ${error.message}`, true));
}

initialize();
