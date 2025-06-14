document.addEventListener('DOMContentLoaded', function () {
  const statusLabels = window.statusLabels || [];
  const statusData = window.statusData || [];
  const topProductsLabels = window.topProductsLabels || [];
  const topProductsData = window.topProductsData || [];

  const statusCtx = document.getElementById('status-pie-chart').getContext('2d');
  new Chart(statusCtx, {
    type: 'pie',
    data: {
      labels: statusLabels,
      datasets: [{
        data: statusData,
        backgroundColor: ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0"]
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'top' },
        title: { display: true, text: 'Распределение статусов' }
      }
    }
  });

  // График топ-5 товаров
  const topProductsCtx = document.getElementById('top-products-bar-chart').getContext('2d');
  new Chart(topProductsCtx, {
    type: 'bar',
    data: {
      labels: topProductsLabels,
      datasets: [{
        label: 'Количество заказов',
        data: topProductsData,
        backgroundColor: ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF"]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' },
        title: { display: true, text: 'Топ-5 популярных товаров' }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            font: { size: 14 }
          }
        },
        x: {
          ticks: {
            font: { size: 14 },
            maxRotation: 0,
            minRotation: 0
          }
        }
      },
      layout: {
        padding: {
          left: 10,
          right: 10,
          top: 10,
          bottom: 10
        }
      }
    }
  });
});