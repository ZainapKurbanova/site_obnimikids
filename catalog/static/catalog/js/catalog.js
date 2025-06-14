document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const suggestionsContainer = document.getElementById('suggestions');
    let debounceTimer;

    searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const query = this.value.trim();
            if (query.length < 2) {
                suggestionsContainer.innerHTML = '';
                suggestionsContainer.style.display = 'none';
                return;
            }

            fetch(`/catalog/?search=${encodeURIComponent(query)}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const products = doc.querySelectorAll('.product-name');
                const suggestions = new Set();

                products.forEach(product => {
                    const name = product.textContent.trim();
                    if (name.toLowerCase().includes(query.toLowerCase()) && suggestions.size < 5) {
                        suggestions.add(name);
                    }
                });

                suggestionsContainer.innerHTML = '';
                if (suggestions.size === 0) {
                    suggestionsContainer.style.display = 'none';
                    return;
                }

                suggestions.forEach(suggestion => {
                    const div = document.createElement('div');
                    div.classList.add('suggestion-item');
                    div.textContent = suggestion;
                    div.addEventListener('click', () => {
                        searchInput.value = suggestion;
                        suggestionsContainer.innerHTML = '';
                        suggestionsContainer.style.display = 'none';
                        searchInput.closest('form').submit();
                    });
                    suggestionsContainer.appendChild(div);
                });

                suggestionsContainer.style.display = 'block';
            })
            .catch(error => console.error('Ошибка:', error));
        }, 300);
    });

    searchInput.addEventListener('blur', function() {
        setTimeout(() => {
            suggestionsContainer.style.display = 'none';
        }, 200);
    });

    searchInput.addEventListener('focus', function() {
        if (suggestionsContainer.children.length > 0) {
            suggestionsContainer.style.display = 'block';
        }
    });

    searchInput.addEventListener('keydown', function(e) {
        const suggestionItems = suggestionsContainer.querySelectorAll('.suggestion-item');
        let activeIndex = -1;

        suggestionItems.forEach((item, index) => {
            if (item.classList.contains('active')) {
                activeIndex = index;
            }
        });

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (activeIndex < suggestionItems.length - 1) {
                suggestionItems.forEach(item => item.classList.remove('active'));
                suggestionItems[activeIndex + 1].classList.add('active');
                suggestionItems[activeIndex + 1].scrollIntoView({ block: 'nearest' });
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (activeIndex > 0) {
                suggestionItems.forEach(item => item.classList.remove('active'));
                suggestionItems[activeIndex - 1].classList.add('active');
                suggestionItems[activeIndex - 1].scrollIntoView({ block: 'nearest' });
            }
        } else if (e.key === 'Enter' && activeIndex >= 0) {
            e.preventDefault();
            searchInput.value = suggestionItems[activeIndex].textContent;
            suggestionsContainer.style.display = 'none';
            searchInput.closest('form').submit();
        }
    });
});