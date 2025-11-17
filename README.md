# GSocket C2 Panel

Web-панель для централизованного управления рабочими станциями через gsocket (hackerschoice/gsocket).

## 🎯 Реализация gsocket

Интеграция с gsocket выполнена согласно **официальной документации**:

- **Архитектура**: Хосты работают в listen mode (`gs-netcat -l`), панель подключается как клиент
- **Безопасность**: Секреты передаются через временные файлы (`-k` флаг) и хранятся зашифрованными в БД
- **Протокол**: SRP-AES-256-CBC-SHA с 4096-bit prime (end-to-end encryption)
- **Функции**: Поддержка `-w` (wait for listener), `-i` (interactive PTY), `-t` (test connection)

**Важные документы:**
- `INITIALIZATION.md` - автоматическая инициализация БД и создание admin
- `HOST_SETUP_GUIDE.md` - пошаговая инструкция настройки хостов
- `CSV_IMPORT_GUIDE.md` - импорт хостов из CSV файлов (bulk import)
- `GSOCKET_ARCHITECTURE.md` - архитектура gsocket и как работает подключение
- `WEB_TERMINAL_GUIDE.md` - руководство по веб-терминалу
- `CUSTOM_GSRN_GUIDE.md` - настройка кастомных GSRN серверов
- `TROUBLESHOOTING_LOGIN.md` - решение проблем с входом
- `GSOCKET_IMPLEMENTATION_ISSUES.md` - детальный анализ архитектуры
- `MIGRATION_GUIDE.md` - миграции базы данных

## Возможности

- **Управление хостами**: Добавление, удаление, мониторинг статуса хостов
- **CSV импорт**: Массовое добавление хостов из CSV файлов (bulk import)
- **Библиотека скриптов**: Создание и управление bash-скриптами для выполнения
- **Выполнение задач**: Параллельное выполнение скриптов на множестве хостов
- **Мониторинг**: Автоматическая проверка доступности хостов каждые 3 минуты
- **Логирование**: Детальные логи всех операций
- **Отчетность**: Dashboard со статистикой, экспорт в CSV
- **Безопасность**: Шифрование gsocket secrets, JWT аутентификация
- **Кастомные GSRN серверы**: Поддержка собственных relay серверов
- **Автоматизация развертывания**: Скрипты для обновления и ребилда контейнеров
- **Веб-терминал**: Полнофункциональный интерактивный терминал в браузере (xterm.js + WebSocket)
- **Автоматические миграции**: База данных обновляется автоматически при рестарте контейнеров

## Технологический стек

- **Backend**: Python 3.11+, FastAPI
- **Database**: SQLite с SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Интеграция**: gsocket-netcat для связи с хостами
- **Deployment**: Docker, Docker Compose

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <repo-url>
cd gs-webpanel
```

### 2. Настройка окружения

Скопируйте файл с переменными окружения:

```bash
cp .env.example .env
```

Отредактируйте `.env` и установите секретные ключи:

```bash
SECRET_KEY=your-secret-key-min-32-chars
ENCRYPTION_KEY=your-encryption-key-32-bytes
```

### 3. Запуск с Docker (рекомендуется)

```bash
# Запустить контейнеры
docker-compose up -d

# Дождаться инициализации (5-10 секунд)
# БД и администратор создаются автоматически!
```

**Готово!** Панель доступна по адресу:
- **URL**: http://localhost:8000/login
- **Логин**: `admin`
- **Пароль**: `Admin123456!`

⚠️ **После первого входа смените пароль!**

### 3. Локальная установка (без Docker)

#### Установка зависимостей:

```bash
# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

#### Инициализация базы данных:

```bash
# Создать базу данных
python3 scripts/init_db.py

# Создать администратора
python3 scripts/create_test_admin.py
```

```bash
# Запуск web-сервера
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Запуск monitor service (в отдельном терминале)
python -m app.services.monitor_service
```

**Доступ к панели**: http://localhost:8000/login
- Логин: `admin`
- Пароль: `Admin123456!`

Войдите используя созданные учетные данные.

## Структура проекта

```
gs-webpanel/
├── app/
│   ├── models/          # Модели базы данных
│   ├── routes/          # API endpoints
│   ├── services/        # Бизнес-логика
│   ├── templates/       # HTML шаблоны
│   ├── utils/           # Утилиты
│   ├── config.py        # Конфигурация
│   ├── database.py      # Настройка БД
│   ├── main.py          # Точка входа
│   └── schemas.py       # Pydantic схемы
├── static/
│   ├── css/            # Стили
│   └── js/             # JavaScript
├── scripts/
│   ├── init_db.py      # Инициализация БД
│   └── create_admin.py # Создание админа
├── data/               # База данных (SQLite)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Использование

### Добавление хоста

1. Перейдите в раздел "Hosts"
2. Нажмите "+ Add Host"
3. Заполните форму:
   - **Hostname**: Имя хоста
   - **IP Address**: IP адрес (опционально)
   - **GSocket Secret**: Секретный ключ gsocket для подключения
   - **Description**: Описание
   - **Notes**: Заметки
   - **Tags**: Теги для группировки (через запятую)
4. Нажмите "Add Host"

### Создание скрипта

1. Перейдите в "Scripts"
2. Нажмите "+ Add Script"
3. Заполните:
   - **Name**: Название скрипта
   - **Description**: Описание
   - **Content**: Bash-скрипт
   - **Timeout**: Таймаут выполнения (секунды)
4. Нажмите "Add Script"

### Выполнение задачи

1. Перейдите в "Tasks"
2. Нажмите "+ Create Task"
3. Выберите скрипт из списка
4. Выберите целевые хосты (checkbox)
5. Нажмите "Execute Task"
6. Задача будет выполнена параллельно на всех выбранных хостах

### Просмотр результатов

1. В разделе "Tasks" нажмите "View Results" для нужной задачи
2. Увидите детальную информацию:
   - Статус выполнения на каждом хосте
   - Exit code
   - Время выполнения
   - Вывод (stdout/stderr)

### Просмотр логов

1. Перейдите в "Logs"
2. Используйте фильтры:
   - Level (INFO, WARNING, ERROR, DEBUG)
   - Category (connection, execution, system, auth)
   - Time Range
3. Экспортируйте логи в CSV при необходимости

## API Documentation

Интерактивная документация API доступна по адресу:

```
http://localhost:8000/api/docs
```

### Основные эндпоинты:

#### Аутентификация
- `POST /api/auth/login` - Вход
- `POST /api/auth/logout` - Выход
- `GET /api/auth/status` - Статус авторизации

#### Хосты
- `GET /api/hosts` - Список хостов
- `POST /api/hosts` - Добавить хост
- `GET /api/hosts/{id}` - Информация о хосте
- `PUT /api/hosts/{id}` - Обновить хост
- `DELETE /api/hosts/{id}` - Удалить хост

#### Скрипты
- `GET /api/scripts` - Список скриптов
- `POST /api/scripts` - Создать скрипт
- `GET /api/scripts/{id}` - Информация о скрипте
- `PUT /api/scripts/{id}` - Обновить скрипт
- `DELETE /api/scripts/{id}` - Удалить скрипт

#### Задачи
- `GET /api/tasks` - Список задач
- `POST /api/tasks` - Создать и выполнить задачу
- `GET /api/tasks/{id}` - Информация о задаче
- `GET /api/tasks/{id}/status` - Статус выполнения
- `GET /api/tasks/{id}/results` - Результаты выполнения
- `POST /api/tasks/{id}/retry` - Повторить неудачные выполнения

#### Логи
- `GET /api/logs` - Получить логи
- `GET /api/logs/export` - Экспорт логов в CSV

#### Отчеты
- `GET /api/reports/dashboard` - Статистика dashboard
- `GET /api/reports/host/{id}` - Отчет по хосту
- `GET /api/reports/task/{id}` - Отчет по задаче
- `GET /api/reports/availability` - История доступности

## Безопасность

### Шифрование секретов

Все gsocket secrets хранятся в базе данных в зашифрованном виде с использованием AES-256-GCM.

### Аутентификация

Используется JWT токены с временем жизни 8 часов. Пароли хешируются с использованием bcrypt.

### Требования к паролям

- Минимум 12 символов
- Минимум 1 заглавная буква
- Минимум 1 строчная буква
- Минимум 1 цифра

## Мониторинг

Monitor service автоматически проверяет доступность всех хостов каждые 3 минуты:

- Отправляет простую команду `echo 'ping'` через gsocket
- Обновляет статус хоста (online/offline)
- Записывает историю доступности в ping_history
- Логирует изменения статуса

## Troubleshooting

### База данных не инициализируется

```bash
# Удалите старую базу и пересоздайте
rm data/c2panel.db
python scripts/init_db.py
python scripts/create_admin.py
```

### Не могу подключиться к хосту

1. Проверьте, что gsocket установлен на целевом хосте
2. Убедитесь, что secret правильный
3. Проверьте сетевую доступность
4. Увеличьте значение timeout в настройках

### Ошибка "Unauthorized"

1. Проверьте, что токен авторизации действителен
2. Войдите заново через `/login`
3. Проверьте настройки SECRET_KEY в .env

## Автоматизация развертывания

### Полное обновление и ребилд

Для обновления кода из репозитория и ребилда контейнеров:

```bash
./deploy.sh
```

Скрипт автоматически:
- Создает резервную копию базы данных
- Проверяет наличие обновлений в git
- Останавливает контейнеры
- Пересобирает Docker образы
- Запускает обновленные контейнеры
- Показывает статус и логи

### Быстрое обновление

Для быстрого обновления без полного ребилда:

```bash
./update.sh
```

Это выполнит:
- `git pull` для получения последних изменений
- Перезапуск контейнеров

### Дополнительные команды

```bash
# Посмотреть логи
./deploy.sh <branch> logs

# Проверить статус контейнеров
./deploy.sh <branch> status

# Остановить контейнеры
./deploy.sh <branch> stop

# Запустить контейнеры
./deploy.sh <branch> start

# Перезапустить контейнеры
./deploy.sh <branch> restart

# Создать резервную копию БД
./deploy.sh <branch> backup
```

### Миграция базы данных

При обновлении с предыдущих версий для добавления поддержки кастомных GSRN:

```bash
# С Docker
docker-compose exec web python scripts/migrate_add_custom_gsrn.py

# Локально
python scripts/migrate_add_custom_gsrn.py
```

## Кастомные GSRN серверы

Панель поддерживает использование собственных GSRN relay серверов:

### Глобальная настройка

В `.env`:
```bash
DEFAULT_GSRN_SERVER="relay.example.com:443"
ENABLE_CUSTOM_GSRN=true
```

### Настройка для отдельного хоста

При добавлении хоста через Web UI укажите "Custom GSRN Server":
```
relay.example.com:443
```

### Подробная документация

См. `CUSTOM_GSRN_GUIDE.md` для:
- Настройки собственного GSRN relay сервера
- Конфигурации мульти-региональной инфраструктуры
- Troubleshooting и best practices

## Разработка

### Запуск в режиме разработки

```bash
# С hot-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Тесты

```bash
pytest tests/
```

## Лицензия

MIT License

## Контакты

При возникновении вопросов создайте issue в репозитории.

---

**Внимание**: Этот инструмент предназначен для легитимного администрирования систем. Используйте только на системах, которыми вы владеете или имеете разрешение на управление.
