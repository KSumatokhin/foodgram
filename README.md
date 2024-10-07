# Проект «Foodgram» описание:
Foodgram дает людям возможность поделиться рецептами своих любимых блюд. Зарегестрированные пользователи могут создавать и редактировать рецепты, подписываться на понравившихся авторов рецепта, а так же добавлять рецепт в избранное и список покупок. Список покупок можно скачать, в результате получится файл TXT формата, содержащий все необходимые ингридиенты и их количество для рецептов из списка покупок.

## Как развернуть проект на сервере:
Для развертывания на сервере:
1. Убедитесь, что на сервере установлен Docker, если нет, то установите.

2. Убедитесь, что на сервере установлен Nginx, если нет, то установите.

3. Настройте nginx на перенаправление всех запросов в докер:
На сервере в редакторе nano откройте конфиг Nginx:
`sudo nano /etc/nginx/sites-enabled/default`. Измените настройки `location` в секции `server`.

```json
server {
    listen 80;
    server_name server_ip domain;

    location / {
            proxy_set_header Host $http_host;
            proxy_pass http://127.0.0.1:8000;
    }

}
```
Cмысл прост: «все запросы передавать в приложение, которое слушает порт 8000».
Вместо `server_ip` и `domain` укажите ip адрес сервера и домен.

4. Скачайте на сервер в папку проекта файл "docker-compose.production.yml".

5. Создайте в папке проекта файл ".env". Пример для заполнения файла представлен в "example.env".

6. Запустите Docker Compose в режиме демона:
```bash
sudo docker compose -f docker-compose.production.yml up -d
```

7. Выполните миграции, импортируйте фикстуры, соберите статические файлы бэкенда:
```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py loaddata recipes/data/ingredients.json
sudo docker compose -f docker-compose.production.yml exec backend python manage.py loaddata recipes/data/tags.json
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```

8. Для создания суперюзера выполните следующие команды:
```
sudo docker exec -it foodgram-backend-1 bash
echo "from django.contrib.auth import get_user_model; User = get_user_model(); \
    u, _ = User.objects.get_or_create(username='superuser'); u.is_superuser = True; u.is_staff = True; \
	u.email = 'superuser@admin.ru'; u.first_name = 'Admin'; u.set_password('5eCretPaSsw0rD'); u.save();" | python manage.py shell
exit
```
Данные для входа:
email: superuser@admin.ru
password: 5eCretPaSsw0rD

## Как развернуть проект локально:
Для локального развертывания проекта:
1. Скопируйте репозиторий в папку на компьютере.

2. Разверните и активируйте виртуальное окружение, установите зависимости:
```python
python -m venv venv
source venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

3. Создайте папку "data" для базы SQLite в папке "backend": `mkdir backend/data/`

4. Создайте в папке `backend\foodgram_backend\` файл ".env". Пример для заполнения файла представлен в "example.env".
В файле ".env" укажите в качестве базы данных БД SQLite, для этого установвите `PSG=False`.

5. Выполните миграции и импортируйте фикстуры:
```python
cd backend/
python manage.py migrate
python manage.py loaddata recipes/data/ingredients.json
python manage.py loaddata recipes/data/tags.json
```

6. Запустите проект `python manage.py runserver`. 



### Техно-стек:
![Static Badge](https://img.shields.io/badge/v.3.9-brightgreen?logo=Python&logoColor=brightgreen&label=Python)
![Static Badge](https://img.shields.io/badge/v.4.2-blue?logo=Django&logoColor=white&label=Django&labelColor=%23004B33)
![Static Badge](https://img.shields.io/badge/DRF-v.3.15-blue)
![Static Badge](https://img.shields.io/badge/Djoser-v.2.1-blue)
![Static Badge](https://img.shields.io/badge/Docker-%232496ED?logo=docker&logoColor=white&labelColor=%232496ED)



### Разработчики проекта
- Суматохин Константин - https://github.com/KSumatokhin
- Команда Яндекс Практикум - https://github.com/yandex-praktikum
