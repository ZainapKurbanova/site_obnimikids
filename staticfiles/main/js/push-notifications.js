function urlBase64ToUint8Array(base64String) {
    try {
        console.log('Input base64String:', base64String);
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        console.log('Converted to Uint8Array:', outputArray);
        return outputArray;
    } catch (e) {
        console.error('Ошибка в urlBase64ToUint8Array:', e);
        throw e;
    }
}

async function subscribeToPush() {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
        try {
            const registration = await navigator.serviceWorker.register('/static/js/sw.js');
            console.log('Service Worker зарегистрирован:', registration);

            const permission = await Notification.requestPermission();
            if (permission !== 'granted') {
                console.log('Разрешение на уведомления не получено');
                return;
            }

            console.log('Using VAPID public key:', VAPID_PUBLIC_KEY);
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
            });
            console.log('Подписка:', subscription);

            await fetch('/subscribe/', {
                method: 'POST',
                body: JSON.stringify(subscription),
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });
            console.log('Подписка отправлена на сервер');
        } catch (error) {
            console.error('Ошибка подписки:', error);
        }
    } else {
        console.log('Push API или Service Worker не поддерживаются');
    }
}

document.addEventListener('DOMContentLoaded', subscribeToPush);