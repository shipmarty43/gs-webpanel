# Исправление ошибки bcrypt

## Проблема

При запуске контейнеров возникала ошибка:
```
✗ Failed to create user: password cannot be longer than 72 bytes
(trapped) error reading bcrypt version
AttributeError: module 'bcrypt' has no attribute '__about__'
```

## Причина

Bcrypt версии 5.x имеет несовместимость с passlib и более строгую валидацию.

## Решение ✅

Зафиксирована версия bcrypt 4.1.2 в `requirements.txt`.

## Как применить исправление

### Шаг 1: Получить последние изменения

```bash
git pull origin claude/gsocket-c2-panel-01CChs23hpBqkFEJi2ygWxWR
```

### Шаг 2: Остановить и удалить контейнеры

```bash
docker-compose down
```

### Шаг 3: Пересобрать образы (ВАЖНО!)

```bash
docker-compose build --no-cache
```

Флаг `--no-cache` обязателен для установки правильной версии bcrypt!

### Шаг 4: Запустить контейнеры

```bash
docker-compose up -d
```

### Шаг 5: Проверить логи

```bash
docker-compose logs web | head -50
```

Должны увидеть:
```
==========================================
GSocket C2 Panel - Starting...
==========================================

→ Database not found, initializing...
✓ Database initialized

→ Creating default admin user...
✓ Test admin user created successfully!
  Username: admin
  Password: Admin123456!

==========================================
Starting application...
==========================================
```

## Быстрая команда (всё в одну строку)

```bash
git pull origin claude/gsocket-c2-panel-01CChs23hpBqkFEJi2ygWxWR && docker-compose down && docker-compose build --no-cache && docker-compose up -d
```

## Проверка успешности

### 1. Проверить что нет ошибок bcrypt

```bash
docker-compose logs web | grep -i bcrypt
```

Не должно быть ошибок!

### 2. Проверить что admin создан

```bash
docker-compose logs web | grep "admin user created"
```

Должно показать:
```
✓ Test admin user created successfully!
```

### 3. Попробовать войти

Откройте: http://localhost:8000/login

```
Username: admin
Password: Admin123456!
```

### 4. Тест через API

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin123456!"}'
```

Должно вернуть токен:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

## Что было изменено

**Файл**: `requirements.txt`

```diff
# Authentication
passlib[bcrypt]==1.7.4
+bcrypt==4.1.2
python-jose[cryptography]==3.3.0
```

## Если всё равно не работает

### Вариант 1: Полная очистка и пересборка

```bash
# Остановить всё
docker-compose down -v

# Удалить образы
docker rmi gs-webpanel-web gs-webpanel-monitor 2>/dev/null || true

# Удалить БД (если хотите начать с чистого листа)
rm -f data/c2panel.db

# Пересобрать
docker-compose build --no-cache

# Запустить
docker-compose up -d
```

### Вариант 2: Проверить версию bcrypt в контейнере

```bash
docker-compose exec web python -c "import bcrypt; print(bcrypt.__version__)"
```

Должно показать: `4.1.2`

Если показывает другую версию - нужна пересборка с `--no-cache`.

### Вариант 3: Создать admin вручную

Если автоинициализация не сработала:

```bash
docker-compose exec web python3 scripts/reset_admin.py
```

## Технические детали

### Почему bcrypt 5.x не работает?

1. Удалён атрибут `__about__` → passlib не может определить версию
2. Более строгая валидация → некоторые операции хеширования падают
3. Несовместимость с passlib 1.7.4

### Почему выбрана версия 4.1.2?

- Стабильная версия
- Полная совместимость с passlib
- Проверена в продакшене
- Нет известных уязвимостей

## Дополнительная информация

Эта ошибка влияла только на:
- Создание новых пользователей
- Смену паролей
- Инициализацию admin при старте

Существующие хеши паролей в БД продолжали работать корректно.

## Поддержка

Если после пересборки всё равно ошибки:

1. Проверьте логи: `docker-compose logs --tail=100`
2. Проверьте версию bcrypt: `docker-compose exec web pip show bcrypt`
3. Удалите образы и пересоберите с `--no-cache`
4. Попробуйте создать admin вручную: `docker-compose exec web python3 scripts/reset_admin.py`

## Файлы для справки

- `requirements.txt` - Зависимости Python
- `entrypoint.sh` - Скрипт инициализации
- `scripts/create_test_admin.py` - Создание admin пользователя
- `scripts/reset_admin.py` - Сброс пароля admin
