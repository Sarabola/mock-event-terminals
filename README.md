
## 1. Клонируем репозиторий
```cmd
ssh: git clone git@github.com:Sarabola/mock-event-terminals.git
https: git clone https://github.com/Sarabola/mock-event-terminals.git
```

## 2. Активация виртуального окружения и установка зависимостей
Linux:
```bash
python -m venv .venv
.venv/bin/active
pip install -r "requirements.txt"
```

Windows:
```bash
python -m venv .venv
.venv/Scripts/active
pip install -r "requirements.txt"
```

## 3. Запуск программы
```bash
pythom -m app.main
```

## Функционал

### 1. Настройка сети
- Откройте главное приложение
- Перейдите в "Settings" для настройки хоста и порта сервера

### 2. Выбор устройств
- В главном меню выберите "Devices"
- Выберите нужное устройство из списка

### 3. Настройка устройства
- В окне устройства нажмите "Settings"
- Настройте device ID и другие параметры
- Для устройств с температурой можно включить/выключить температурную детекцию

### 4. Выбор фотографий
- В окне устройства нажмите "Select photos"
- Отметьте фотографии для отправки

### 5. Отправка событий
- В окне устройства нажмите "Send photos"
- Следите за прогрессом отправки

## Файл настроек
Приложение хранит настройки в файле \`app/settings.json\`:

