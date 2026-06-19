# Mock Terminal Emulator Web

Веб-версия эмулятора терминалов для отправки mock-событий/детектов на устройства.

## Что есть

- Backend: FastAPI, SQLAlchemy 2 async ORM, SQLite через `aiosqlite`.
- Frontend: React + Vite + TypeScript.
- Хранение состояния в SQLite: сеть, устройства, настройки устройств, выбранные изображения, задания отправки.
- Регистрация и авторизация по `email + password`.
- Персональные последние настройки для каждого пользователя.
- Поддерживаемые устройства:
  - Luna Fast 2 Next Gen
  - Luna Fast 4A
  - R20
  - Beward
  - Hikvision Terminal Thermo
- Поддержка папки `images` для `.jpg`, `.jpeg`, `.png`.
- Просмотр, загрузка, удаление и переименование изображений из веб-интерфейса.
- Docker Compose запуск backend/frontend.

## Запуск

Создайте папки для данных и изображений, если их еще нет:

```bash
mkdir -p data images
```

Запустите приложение:

```bash
docker compose up --build
```

Откройте frontend:

```text
http://localhost:5173
```

Backend API:

```text
http://localhost:8000/api
```

Swagger UI:

```text
http://localhost:8000/docs
```

## Использование

1. Создайте пользователя или войдите под существующим email/password.
2. Настройте `host` и `port` сервера во вкладке Network Settings.
3. Выберите устройство в списке слева.
4. Укажите `device_id` и дополнительные параметры устройства.
5. Положите изображения в папку `images`.
6. Нажмите `Refresh` в блоке Photos или загрузите новые изображения через `Upload`.
7. Выберите изображения, при необходимости переименуйте или удалите старые, и сохраните выбор.
8. Нажмите `Send Photos` и отслеживайте прогресс.

Каталог изображений общий для всех пользователей. Настройки сети, устройств, выбор фото и история отправок сохраняются отдельно для каждого пользователя.

## Docker volumes

- `./data:/app/data` - SQLite база `app.db`.
- `./images:/app/images` - изображения для отправки.

## Основные API

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/settings/network`
- `PUT /api/settings/network`
- `GET /api/devices`
- `GET /api/devices/{device_name}`
- `PUT /api/devices/{device_name}/settings`
- `GET /api/images`
- `POST /api/images/refresh`
- `GET /api/images/{image_name}/content`
- `POST /api/images/upload`
- `DELETE /api/images/{image_name}`
- `PUT /api/images/{image_name}/rename`
- `PUT /api/images`
- `POST /api/devices/{device_name}/send`
- `GET /api/send-jobs/{job_id}`
- `POST /api/devices/lunafast4a/card-event`

## Старая Tkinter-версия

Исходные Tkinter-файлы оставлены в папке `app` как предыдущая реализация и источник перенесенной бизнес-логики.
