function updateQuantity(change) {
    let quantityInput = document.getElementById('quantity');
    let currentValue = parseInt(quantityInput.value);
    let newValue = currentValue + change;
    if (newValue >= 1) {
        quantityInput.value = newValue;
    }
}

function toggleDetails() {
    let details = document.getElementById('details-content');
    details.style.display = details.style.display === 'block' ? 'none' : 'block';
}

document.addEventListener('DOMContentLoaded', function() {
    let addToCartBtn = document.getElementById('add-to-cart-btn');
    let form = document.getElementById('add-to-cart-form');
    let productId = form.getAttribute('data-product-id');
    let isInCart = false;

    addToCartBtn.addEventListener('click', function() {
        if (!isInCart) {
            let size = form.querySelector('input[name="size"]:checked');
            if (!size) {
                alert('Пожалуйста, выберите размер.');
                return;
            }

            let quantity = document.getElementById('quantity').value;
            let csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;

            fetch(`/cart/add-to-cart/${productId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: `size=${size.value}&quantity=${quantity}&color=${encodeURIComponent(form.querySelector('input[name="color"]').value)}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    addToCartBtn.textContent = 'Перейти в корзину';
                    addToCartBtn.classList.remove('add-to-cart-btn');
                    addToCartBtn.classList.add('go-to-cart-btn');
                    isInCart = true;
                    addToCartBtn.onclick = function() {
                        window.location.href = '/cart/';
                    };
                } else {
                    alert(data.error);
                }
            })
            .catch(error => console.error('Ошибка:', error));
        } else {
            window.location.href = '/cart/';
        }
    });

    let favoriteBtn = document.getElementById('favorite-btn');
    favoriteBtn.addEventListener('click', function() {
        let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        fetch(`/favorites/toggle/${productId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.is_favorite) {
                    favoriteBtn.innerHTML = '<i class="fas fa-heart"></i> Удалить из избранного';
                    favoriteBtn.classList.add('favorited');
                } else {
                    favoriteBtn.innerHTML = '<i class="far fa-heart"></i> Добавить в избранное';
                    favoriteBtn.classList.remove('favorited');
                }
            }
        })
        .catch(error => console.error('Ошибка:', error));
    });

    let alertMessages = document.getElementById('alert-messages');
    if (alertMessages) {
        alertMessages.style.display = 'block';
        setTimeout(() => {
            alertMessages.style.display = 'none';
        }, 5000);
    }
});