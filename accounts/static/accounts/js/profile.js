document.addEventListener('DOMContentLoaded', function() {
    const birthDateInput = document.getElementById('id_birth_date');
    if (birthDateInput) {
        if (!birthDateInput.value) {
            birthDateInput.removeAttribute('placeholder');
        } else {
            const dateValue = birthDateInput.value;
            const dateParts = dateValue.split('.');
            if (dateParts.length === 3) {
                const formattedDate = `${dateParts[2]}-${dateParts[1]}-${dateParts[0]}`;
                birthDateInput.value = formattedDate;
            }
        }
    }

    // Логика переключения вкладок
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });

    // Кастомное автозаполнение для городов
    const cityInput = document.getElementById('id_city');
    const suggestionsContainer = document.getElementById('city-suggestions');
    const selectedCityInput = document.getElementById('id_selected_city');
    let selectedCity = null;
    let activeSuggestionIndex = -1;

    if (cityInput && suggestionsContainer && selectedCityInput) {
        console.log('Автозаполнение инициализировано для поля id_city');

        // Функция для получения предложений через DaData API
        const fetchSuggestions = async (query) => {
            if (!query || query.length < 1) {
                suggestionsContainer.style.display = 'none';
                console.log('Запрос слишком короткий:', query);
                return;
            }

            const url = 'https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address';
            const token = '79da688188c12cf893b72df07cbca7bc42e54cec';
            const requestOptions = {
                method: 'POST',
                mode: 'cors',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': 'Token ' + token
                },
                body: JSON.stringify({
                    query: query,
                    count: 10,
                    locations: [{ country: 'Россия' }],
                    restrict_value: true,
                    type: 'CITY'
                })
            };

            try {
                const response = await fetch(url, requestOptions);
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                const data = await response.json();
                console.log('Полученные данные:', data);
                const citySuggestions = data.suggestions.filter(suggestion => suggestion.data.city);
                displaySuggestions(citySuggestions.map(suggestion => ({
                    properties: { city: suggestion.data.city }
                })));
            } catch (error) {
                console.error('Ошибка при запросе предложений:', error);
                suggestionsContainer.style.display = 'none';
            }
        };

        // Функция для отображения предложений
        const displaySuggestions = (features) => {
            suggestionsContainer.innerHTML = '';
            if (features.length === 0) {
                suggestionsContainer.style.display = 'none';
                console.log('Нет предложений для отображения');
                return;
            }

            console.log('Отображение предложений:', features);
            features.forEach((feature, index) => {
                const cityName = feature.properties.city;
                const suggestionItem = document.createElement('div');
                suggestionItem.classList.add('suggestion-item');
                suggestionItem.textContent = cityName;
                suggestionItem.dataset.city = cityName;

                suggestionItem.addEventListener('click', () => {
                    selectedCity = cityName;
                    cityInput.value = selectedCity;
                    selectedCityInput.value = selectedCity;
                    suggestionsContainer.style.display = 'none';
                    activeSuggestionIndex = -1;
                    console.log('Выбран город (клик):', selectedCity);
                });

                suggestionItem.addEventListener('mouseover', () => {
                    activeSuggestionIndex = index;
                    updateActiveSuggestion();
                });

                suggestionsContainer.appendChild(suggestionItem);
            });

            suggestionsContainer.style.display = 'block';
            activeSuggestionIndex = -1;
        };

        // Обработчик ввода текста
        let debounceTimeout;
        cityInput.addEventListener('input', () => {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
                selectedCity = null;
                selectedCityInput.value = '';
                fetchSuggestions(cityInput.value);
            }, 500);
        });

        // Обработка клавиш (стрелки и Enter)
        cityInput.addEventListener('keydown', (e) => {
            const suggestionItems = suggestionsContainer.querySelectorAll('.suggestion-item');
            if (!suggestionItems.length) return;

            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    activeSuggestionIndex = Math.min(activeSuggestionIndex + 1, suggestionItems.length - 1);
                    updateActiveSuggestion();
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    activeSuggestionIndex = Math.max(activeSuggestionIndex - 1, 0);
                    updateActiveSuggestion();
                    break;
                case 'Enter':
                    e.preventDefault();
                    if (activeSuggestionIndex >= 0 && activeSuggestionIndex < suggestionItems.length) {
                        const cityName = suggestionItems[activeSuggestionIndex].dataset.city;
                        selectedCity = cityName;
                        cityInput.value = selectedCity;
                        selectedCityInput.value = selectedCity;
                        suggestionsContainer.style.display = 'none';
                        activeSuggestionIndex = -1;
                        console.log('Выбран город (Enter):', selectedCity);
                    }
                    break;
                case 'Escape':
                    suggestionsContainer.style.display = 'none';
                    activeSuggestionIndex = -1;
                    break;
            }
        });

        // Обновление активного элемента
        const updateActiveSuggestion = () => {
            const suggestionItems = suggestionsContainer.querySelectorAll('.suggestion-item');
            suggestionItems.forEach((item, index) => {
                item.classList.toggle('active', index === activeSuggestionIndex);
            });
            if (activeSuggestionIndex >= 0) {
                suggestionItems[activeSuggestionIndex].scrollIntoView({ block: 'nearest' });
            }
        };

        // Очистка при снятии фокуса
        cityInput.addEventListener('blur', () => {
            setTimeout(() => {
                if (!selectedCity) {
                    cityInput.value = '';
                    selectedCityInput.value = '';
                    console.log('Поле очищено');
                } else {
                    cityInput.value = selectedCity;
                    selectedCityInput.value = selectedCity;
                }
                suggestionsContainer.style.display = 'none';
                activeSuggestionIndex = -1;
            }, 200);
        });

        // Закрытие списка при клике вне поля
        document.addEventListener('click', (e) => {
            if (!cityInput.contains(e.target) && !suggestionsContainer.contains(e.target)) {
                suggestionsContainer.style.display = 'none';
                activeSuggestionIndex = -1;
            }
        });
    } else {
        console.error('Не удалось найти элементы cityInput, suggestionsContainer, selectedCityInput или submitBtn');
    }
});