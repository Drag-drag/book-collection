const API_URL = window.location.origin;

async function loadStats() {
    try {
        const res = await fetch(`${API_URL}/books/stats/`);
        const stats = await res.json();
        const section = document.getElementById('statsSection');
        section.classList.remove('d-none');

        let genresHtml = '';
        for (const [genre, count] of Object.entries(stats.genres_count)) {
            genresHtml += `<li>${genre || 'Не указан'}: <strong>${count}</strong></li>`;
        }

        document.getElementById('statsContent').innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <p><strong>Всего книг:</strong> ${stats.total_books}</p>
                    <p><strong>По жанрам:</strong></p>
                    <ul>${genresHtml || '<li>Нет данных</li>'}</ul>
                </div>
            </div>
        `;
    } catch (err) {
        console.error(err);
        alert("Не удалось загрузить статистику");
    }
}

async function addBook(e) {
    e.preventDefault();
    const book = {
        title: document.getElementById('title').value,
        author: document.getElementById('author').value,
        genre: document.getElementById('genre').value || null,
        image: document.getElementById('image').value || null,
        status: document.getElementById('status').value,
        description: "" // Добавляем пустое описание по умолчанию
    };

    try {
        const res = await fetch(`${API_URL}/books/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(book)
        });
        if (!res.ok) throw new Error('Ошибка при добавлении');
        bootstrap.Modal.getInstance(document.getElementById('addBookModal')).hide();
        window.location.reload();
    } catch (err) {
        alert('Ошибка: ' + err.message);
    }
}

async function addBookByISBN(e) {
    e.preventDefault();
    const isbn = document.getElementById('isbn').value.trim();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Ищем...';

    try {
        const res = await fetch(`${API_URL}/books/from-isbn`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ isbn })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Книга не найдена');
        }

        bootstrap.Modal.getInstance(document.getElementById('isbnModal')).hide();
        window.location.reload();
    } catch (err) {
        alert('Ошибка: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Поиск и добавление';
    }
}

function openEditModal(bookId, title, author, genre, status) {
    document.getElementById('edit-book-id').value = bookId;
    document.getElementById('edit-title').value = title;
    document.getElementById('edit-author').value = author;
    document.getElementById('edit-genre').value = genre || '';
    document.getElementById('edit-status').value = status;

    new bootstrap.Modal(document.getElementById('editBookModal')).show();
}

document.getElementById('editBookForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const bookId = document.getElementById('edit-book-id').value;
    const updatedBook = {
        title: document.getElementById('edit-title').value,
        author: document.getElementById('edit-author').value,
        genre: document.getElementById('edit-genre').value || null,
        status: document.getElementById('edit-status').value
    };

    try {
        const res = await fetch(`${API_URL}/books/${bookId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedBook)
        });
        if (!res.ok) throw new Error('Не удалось обновить');
        window.location.reload();
    } catch (err) {
        alert('Ошибка: ' + err.message);
    }
});

async function showSimilarBooks(bookId) {
    const container = document.getElementById("similar-books-list");
    container.innerHTML = '<div class="text-center"><div class="spinner-border text-primary"></div></div>';
    new bootstrap.Modal(document.getElementById("similarBooksModal")).show();

    try {
        const res = await fetch(`${API_URL}/books/${bookId}/similar/`);
        const books = await res.json();
        container.innerHTML = "";

        if (books.length === 0) {
            container.innerHTML = "<p class='text-center'>Похожих книг не найдено</p>";
            return;
        }

        let html = '<div class="row row-cols-1 row-cols-md-2 g-3">';
        books.forEach(b => {
            html += `
                <div class="col">
                    <div class="card h-100 shadow-sm">
                        <img src="${b.image || 'https://via.placeholder.com/150x200?text=No+Cover'}" class="card-img-top p-2" style="height:150px; object-fit:contain;">
                        <div class="card-body">
                            <h6 class="card-title">${b.title}</h6>
                            <p class="small text-muted mb-0">${b.author}</p>
                        </div>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        container.innerHTML = html;
    } catch (err) {
        container.innerHTML = "<p class='text-danger'>Ошибка загрузки рекомендаций</p>";
    }
}

async function deleteBook(id) {
    if (!confirm('Вы уверены, что хотите удалить эту книгу?')) return;
    try {
        const res = await fetch(`${API_URL}/books/${id}`, { method: 'DELETE' });
        if (res.ok) window.location.reload();
    } catch (err) {
        alert('Ошибка при удалении');
    }
}
