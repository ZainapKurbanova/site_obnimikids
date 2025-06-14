from django.contrib import admin
from .models import Size, Product
import requests
from decouple import config
import os
import uuid
from django.utils.text import slugify
import logging

logger = logging.getLogger(__name__)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'category', 'price', 'created_at')  # Добавляем category в список
    list_filter = ('color', 'category', 'created_at')  # Добавляем фильтр по категории
    search_fields = ('name', 'description')
    def save_model(self, request, obj, form, change):
        logger.info(f"Начало сохранения товара: {obj.name}, image_file: {obj.image_file}")
        if 'image_file' in form.changed_data and obj.image_file:
            logger.info(f"Путь к файлу: {obj.image_file.path}")
            if not os.path.exists(obj.image_file.path):
                logger.error(f"Файл не найден: {obj.image_file.path}")
                self.message_user(request, f"Файл {obj.image_file.path} не найден. Проверьте настройки media.", level='error')
                obj.image_file = None
                super().save_model(request, obj, form, change)
                return

            imgbb_api_key = config('IMGBB_API_KEY')
            if not imgbb_api_key:
                logger.error("API-ключ ImgBB отсутствует")
                self.message_user(request, "Отсутствует API-ключ ImgBB в .env", level='error')
                return
            logger.info(f"Используемый API-ключ: {imgbb_api_key}")

            ext = obj.image_file.name.split('.')[-1]
            name = slugify(obj.name, allow_unicode=False)
            unique_id = uuid.uuid4().hex[:8]
            filename = f"{name}-{unique_id}.{ext}"
            logger.info(f"Генерируем имя файла: {filename}")

            url = "https://api.imgbb.com/1/upload"
            try:
                with open(obj.image_file.path, 'rb') as image_file:
                    payload = {'key': imgbb_api_key, 'image': image_file, 'name': filename}
                    logger.info(f"Отправка запроса на {url} с payload: {payload}")
                    response = requests.post(url, files=payload)
                    response.raise_for_status()
                    logger.info(f"Ответ от ImgBB: {response.text}")
            except FileNotFoundError:
                logger.error(f"Файл не найден: {obj.image_file.path}")
                self.message_user(request, f"Файл {obj.image_file.path} не найден.", level='error')
                obj.image_file = None
                super().save_model(request, obj, form, change)
                return
            except requests.RequestException as e:
                logger.error(f"Ошибка загрузки в ImgBB: {e}")
                self.message_user(request, f"Ошибка загрузки в ImgBB: {e}", level='error')
                return

            data = response.json()
            logger.info(f"JSON-ответ от ImgBB: {data}")
            if data.get('success'):
                obj.image = data['data']['url']
                self.message_user(request, f"Файл успешно загружен в ImgBB: {obj.image}", level='success')
            else:
                logger.error(f"Ошибка ImgBB: {data.get('status_text')}")
                self.message_user(request, f"Ошибка ImgBB: {data.get('status_text')}", level='error')
                return

            try:
                if os.path.exists(obj.image_file.path):
                    os.remove(obj.image_file.path)
                    logger.info(f"Временный файл {obj.image_file.path} удален")
            except Exception as e:
                logger.warning(f"Ошибка удаления файла: {e}")
                self.message_user(request, f"Ошибка удаления временного файла: {e}", level='warning')

            obj.image_file = None

        super().save_model(request, obj, form, change)

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)