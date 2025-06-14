document.addEventListener('DOMContentLoaded', () => {
    // Используем id полей, заданные в форме через атрибуты виджетов: 'city-input' и 'address-detail-input'
    const cityField = document.getElementById('city-input');
    const detailField = document.getElementById('address-detail-input');
    const citySug = document.getElementById('city-input-suggestions');
    const detailSug = document.getElementById('address-detail-input-suggestions');
    let selectedCity = cityField ? cityField.value : null;
    let selectedDetail = null;

    const token = '79da688188c12cf893b72df07cbca7bc42e54cec';
    const api = 'https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address';

    function createRequest(query, bounds) {
        return fetch(api, {
            method: 'POST',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': 'Token ' + token
            },
            body: JSON.stringify({ query, count: 5, ...bounds })
        }).then(r => r.json());
    }

    function show(items, type) {
        const field = type === 'city' ? cityField : detailField;
        const container = type === 'city' ? citySug : detailSug;
        container.innerHTML = '';
        if (!items || !items.length) { container.style.display = 'none'; return; }
        items.forEach(s => {
            const val = type === 'city'
                ? s.data.city
                : s.value.replace(s.data.city + ', ', '');
            if (!val) return;
            const div = document.createElement('div');
            div.className = 'suggestion-item';
            div.textContent = val;
            div.addEventListener('click', () => {
                field.value = val;
                if (type === 'city') {
                    selectedCity = val;
                    detailField.value = '';
                    selectedDetail = null;
                } else {
                    selectedDetail = val;
                }
                container.style.display = 'none';
            });
            container.appendChild(div);
        });
        container.style.display = 'block';
    }

    let timer;
    if (cityField) {
        cityField.addEventListener('input', () => {
            clearTimeout(timer);
            selectedCity = null;
            timer = setTimeout(() => {
                if (!cityField.value) {
                    citySug.style.display = 'none';
                    return;
                }
                createRequest(cityField.value, {
                    locations: [{ country: 'Россия' }],
                    from_bound: { value: 'city' },
                    to_bound: { value: 'city' }
                }).then(res => show(res.suggestions, 'city'));
            }, 300);
        });
    }

    if (detailField) {
        detailField.addEventListener('input', () => {
            if (!selectedCity) {
                alert('Выберите город из списка');
                detailField.value = '';
                return;
            }
            clearTimeout(timer);
            selectedDetail = null;
            timer = setTimeout(() => {
                if (!detailField.value) {
                    detailSug.style.display = 'none';
                    return;
                }
                createRequest(`${selectedCity}, ${detailField.value}`, {
                    locations: [{ city: selectedCity }],
                    from_bound: { value: 'street' },
                    to_bound: { value: 'flat' }
                }).then(res => show(res.suggestions, 'detail'));
            }, 300);
        });
    }

    document.addEventListener('click', e => {
        if (cityField && !cityField.contains(e.target) && !citySug.contains(e.target)) {
            citySug.style.display = 'none';
        }
        if (detailField && !detailField.contains(e.target) && !detailSug.contains(e.target)) {
            detailSug.style.display = 'none';
        }
    });

    const form = document.getElementById('checkout-form');
    if (form) {
        form.addEventListener('submit', e => {
            if (!selectedCity) {
                e.preventDefault();
                alert('Пожалуйста, выберите город из списка');
            }
            if (!selectedDetail) {
                e.preventDefault();
                alert('Пожалуйста, выберите детальный адрес из списка');
            }
        });
    }

    // Логика для обновления стоимости доставки
    const deliveryCostElement = document.getElementById('delivery-cost');
    const totalWithDeliveryElement = document.getElementById('total-with-delivery');
    const totalPriceText = document.querySelector('.total-price').textContent; // Например, "1500 ₽"
    const totalPrice = parseFloat(totalPriceText.replace(' ₽', '')); // Извлекаем числовое значение (1500)

    // Стоимость доставки в зависимости от метода
    const deliveryCosts = {
        'post': 300, // Почта России
        'courier': 500 // Курьер
    };

    // Функция для обновления стоимости доставки и итоговой суммы
    function updateDeliveryCost() {
        const selectedMethod = document.querySelector('input[name="delivery_method"]:checked');
        if (selectedMethod) {
            const cost = deliveryCosts[selectedMethod.value] || 0;
            deliveryCostElement.textContent = `${cost} ₽`;
            const totalWithDelivery = totalPrice + cost;
            totalWithDeliveryElement.textContent = `${totalWithDelivery} ₽`;
        }
    }

    // Инициализация: установить стоимость доставки при загрузке страницы
    const initialMethod = document.querySelector('input[name="delivery_method"]:checked');
    if (initialMethod) {
        updateDeliveryCost();
    }

    // Обработчик события для изменения метода доставки
    const deliveryRadios = document.querySelectorAll('input[name="delivery_method"]');
    deliveryRadios.forEach(radio => {
        radio.addEventListener('change', updateDeliveryCost);
    });
});