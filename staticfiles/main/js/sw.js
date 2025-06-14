// static/js/sw.js
self.addEventListener('push', function(event) {
    console.log('Получено push-событие:', event);
    const data = event.data.json();
    const options = {
        body: data.body,
        icon: '/static/main/images/logo.png',
        data: { url: data.url }
    };
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    console.log('Уведомление кликнуто:', event);
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});