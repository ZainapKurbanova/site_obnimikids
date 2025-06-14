document.addEventListener('DOMContentLoaded', function () {
    // Удаляем все существующие обработчики перед добавлением новых
    document.querySelectorAll('.quantity-btn').forEach(button => {
        const clonedButton = button.cloneNode(true);
        button.parentNode.replaceChild(clonedButton, button);
    });
    document.querySelectorAll('.remove-btn').forEach(button => {
        const clonedButton = button.cloneNode(true);
        button.parentNode.replaceChild(clonedButton, button);
    });

    // Обработчики для кнопок увеличения/уменьшения количества
    document.querySelectorAll('.quantity-btn').forEach(button => {
        button.addEventListener('click', function (event) {
            event.stopPropagation(); // Предотвращаем переход по ссылке
            const itemId = this.getAttribute('data-item-id');
            const change = parseInt(this.getAttribute('data-change'));
            console.log(`Обновление количества для itemId: ${itemId}, change: ${change}`);
            updateQuantity(itemId, change);
        });
    });

    // Обработчики для кнопок удаления
    document.querySelectorAll('.remove-btn').forEach(button => {
        button.addEventListener('click', function (event) {
            event.stopPropagation(); // Предотвращаем переход по ссылке
            const itemId = this.getAttribute('data-item-id');
            console.log(`Удаление itemId: ${itemId}`);
            removeItem(itemId);
        });
    });

    function updateQuantity(itemId, change) {
        // Проверяем, не обрабатывается ли уже запрос
        if (document.querySelector(`.cart-item[data-item-id="${itemId}"][data-processing="true"]`)) {
            console.warn(`Обработка для itemId ${itemId} уже выполняется`);
            return;
        }

        let cartItem = document.querySelector(`.cart-item[data-item-id="${itemId}"]`);
        if (!cartItem) {
            console.error(`Элемент с itemId ${itemId} не найден`);
            return;
        }

        let quantityElement = cartItem.querySelector(`.quantity-value[data-item-id="${itemId}"]`);
        if (!quantityElement) {
            console.error(`Элемент .quantity-value для itemId ${itemId} не найден`);
            return;
        }

        let currentValue = parseInt(quantityElement.textContent) || 0;
        let newValue = currentValue + change;

        if (newValue < 1) {
            removeItem(itemId);
            return;
        }

        // Отмечаем элемент как обрабатываемый
        cartItem.setAttribute('data-processing', 'true');

        // Оптимистическое обновление
        quantityElement.textContent = newValue;

        const csrfToken = document.querySelector('meta[name="csrf-token"]');
        if (!csrfToken) {
            console.error('CSRF-токен не найден');
            quantityElement.textContent = currentValue; // Откатываем
            cartItem.removeAttribute('data-processing');
            return;
        }

        fetch(`/cart/update_quantity/${itemId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken.content
            },
            body: JSON.stringify({ quantity: newValue })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Ответ сервера:', data);
            if (data.success) {
                let itemTotalPrice = cartItem.querySelector('.item-total-price');
                if (itemTotalPrice) {
                    itemTotalPrice.textContent = `${data.item_total_price} ₽`;
                } else {
                    console.error(`Элемент .item-total-price для itemId ${itemId} не найден`);
                }
                let totalPrice = document.querySelector('.total-price');
                if (totalPrice) {
                    totalPrice.textContent = `${data.total_price} ₽`;
                } else {
                    console.error('Элемент .total-price не найден');
                }
                let cartItemCount = document.querySelector('.cart-item-count');
                if (cartItemCount) {
                    cartItemCount.textContent = data.item_count;
                } else {
                    console.error('Элемент .cart-item-count не найден');
                }
            } else {
                quantityElement.textContent = currentValue; // Откатываем
                alert('Ошибка при обновлении количества: ' + data.error);
            }
        })
        .catch(error => {
            quantityElement.textContent = currentValue; // Откатываем
            console.error('Ошибка:', error);
            alert('Произошла ошибка при обновлении количества.');
        })
        .finally(() => {
            cartItem.removeAttribute('data-processing'); // Удаляем флаг после завершения
        });
    }

    function removeItem(itemId) {
        if (!confirm('Удалить товар из корзины?')) {
            return;
        }

        const csrfToken = document.querySelector('meta[name="csrf-token"]');
        if (!csrfToken) {
            console.error('CSRF-токен не найден');
            return;
        }

        fetch(`/cart/remove_item/${itemId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken.content
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Ответ сервера при удалении:', data);
            if (data.success) {
                let cartItem = document.querySelector(`.cart-item[data-item-id="${itemId}"]`);
                if (cartItem) {
                    cartItem.parentElement.remove();
                    let cartItems = document.querySelectorAll('.cart-item');
                    let cartItemCount = document.querySelector('.cart-item-count');
                    if (cartItemCount) {
                        cartItemCount.textContent = cartItems.length;
                    } else {
                        console.error('Элемент .cart-item-count не найден');
                    }
                    let totalPrice = document.querySelector('.total-price');
                    if (totalPrice) {
                        totalPrice.textContent = `${data.total_price} ₽`;
                    } else {
                        console.error('Элемент .total-price не найден');
                    }
                    if (cartItems.length === 0) {
                        document.querySelector('.cart-container').innerHTML = '<p class="empty-cart">Ваша корзина пуста.</p>';
                    }
                } else {
                    console.error(`Элемент с itemId ${itemId} не найден для удаления`);
                }
            } else {
                alert('Ошибка при удалении товара: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            alert('Произошла ошибка при удалении товара.');
        });
    }
});
function showAlert(message, type) {
    let alertDiv = document.createElement('div');
    alertDiv.className = `custom-alert ${type}`;
    alertDiv.textContent = message;
    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.classList.add('show');
    }, 100);

    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => {
            alertDiv.remove();
        }, 500);
    }, 5000);
}

document.addEventListener('DOMContentLoaded', function() {
    let alertMessages = document.getElementById('alert-messages');
    if (alertMessages) {
        let messages = alertMessages.getElementsByClassName('alert-message');
        let currentPage = window.location.pathname;

        for (let i = 0; i < messages.length; i++) {
            let message = messages[i];
            let messageText = message.textContent;
            let messageType = message.classList.contains('success') ? 'success' : 'error';
            let messageDataType = message.getAttribute('data-type');

            if (currentPage.includes('/cart/')) {
                if (messageDataType === 'cart_action') {
                    showAlert(messageText, messageType);
                }
            } else if (currentPage.includes('/catalog/') || currentPage.includes('/product/')) {
                if (messageDataType === 'cart_action') {
                    showAlert(messageText, messageType);
                }
            } else if (currentPage.includes('/checkout/')) {
                if (messageDataType === 'order_success') {
                    showAlert(messageText, messageType);
                }
            }
        }
    }
});