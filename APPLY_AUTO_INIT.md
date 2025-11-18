# Как применить автоматическую инициализацию

## Проблема решена! ✅

Теперь Docker контейнеры **автоматически** создают базу данных и администратора при первом запуске.

## Как применить обновление

### Вариант 1: Полный ребилд (Рекомендуется)

```bash
# 1. Остановить контейнеры
docker-compose down

# 2. Пересобрать образы с новым entrypoint
docker-compose build

# 3. Запустить контейнеры
docker-compose up -d

# 4. Подождать 10 секунд для инициализации

# 5. Проверить логи
docker-compose logs web | head -40
```

Вы должны увидеть:
```
==========================================
GSocket C2 Panel - Starting...
==========================================

→ Database not found, initializing...
✓ Database initialized

→ Creating default admin user...
✓ Admin user created

==========================================
Starting application...
==========================================

Login credentials:
  URL: http://localhost:8000/login
  Username: admin
  Password: Admin123456!
==========================================
```

### Вариант 2: Использование deploy.sh

```bash
# Автоматическое обновление и ребилд
./deploy.sh

# Скрипт:
# - Создаст резервную копию БД
# - Подтянет последние изменения
# - Пересоберёт контейнеры
# - Запустит с инициализацией
```

### Вариант 3: Чистый старт

**ВНИМАНИЕ:** Удаляет все данные!

```bash
# Полностью очистить и начать заново
docker-compose down -v
rm -f data/c2panel.db
docker-compose build
docker-compose up -d
```

## Проверка работы

### 1. Проверить логи инициализации

```bash
docker-compose logs web | grep -E "Database|admin|Login"
```

Должно показать:
- ✓ Database initialized
- ✓ Admin user created
- Login credentials

### 2. Проверить что БД создана

```bash
ls -lh data/c2panel.db

# Должен показать файл размером > 100KB
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

## Что изменилось

### До (требовались ручные действия):

```bash
docker-compose up -d
docker-compose exec web python3 scripts/init_db.py
docker-compose exec web python3 scripts/create_test_admin.py
```

### После (всё автоматически):

```bash
docker-compose up -d
# Готово! БД и admin созданы автоматически
```

## Файлы изменений

- `entrypoint.sh` - Скрипт автоматической инициализации
- `Dockerfile` - Добавлен ENTRYPOINT
- `INITIALIZATION.md` - Полная документация
- `README.md` - Обновлена инструкция по установке

## Для существующих установок

Если у вас уже есть рабочая БД и пользователи:

```bash
# Обновить код
git pull origin claude/gsocket-c2-panel-01CChs23hpBqkFEJi2ygWxWR

# Пересобрать контейнеры
docker-compose down
docker-compose build
docker-compose up -d

# БД и пользователи сохранятся!
# Entrypoint обнаружит существующую БД и не будет её пересоздавать
```

Entrypoint скрипт **идемпотентен**:
- ✅ Не трогает существующую БД
- ✅ Не создаёт дубликаты пользователей
- ✅ Безопасно запускается многократно

## Миграция данных

Если нужно сохранить существующие данные:

```bash
# 1. Резервная копия
cp data/c2panel.db data/c2panel.db.backup

# 2. Обновить и пересобрать
git pull origin claude/gsocket-c2-panel-01CChs23hpBqkFEJi2ygWxWR
docker-compose down
docker-compose build
docker-compose up -d

# 3. Данные сохранены!
```

## Troubleshooting

### Entrypoint не запускается

Проверьте что entrypoint.sh имеет права на выполнение:

```bash
ls -l entrypoint.sh
# Должно быть: -rwxr-xr-x

# Если нет, исправить:
chmod +x entrypoint.sh
git add entrypoint.sh
git commit -m "Fix entrypoint permissions"
```

### БД не создаётся

```bash
# Проверить логи
docker-compose logs web

# Проверить права на data/
ls -ld data/
sudo chown -R $USER:$USER data/
```

### Пользователь не создаётся

```bash
# Создать вручную
docker-compose exec web python3 scripts/reset_admin.py

# Или
python3 scripts/reset_admin.py
```

### Контейнер не запускается

```bash
# Посмотреть полные логи
docker-compose logs web

# Проверить синтаксис entrypoint.sh
bash -n entrypoint.sh
```

## Следующие шаги

После успешного запуска:

1. ✅ Войдите на http://localhost:8000/login
2. ✅ Используйте `admin` / `Admin123456!`
3. ⚠️ **Смените пароль после первого входа!**
4. 📖 Изучите `INITIALIZATION.md` для деталей
5. 🚀 Начните работу с панелью

## Дополнительная информация

- `INITIALIZATION.md` - Полная документация автоинициализации
- `TROUBLESHOOTING_LOGIN.md` - Решение проблем с входом
- `QUICK_FIX.md` - Быстрые решения частых проблем
- `CUSTOM_GSRN_GUIDE.md` - Настройка кастомных GSRN серверов

## Поддержка

Если что-то не работает:

1. Проверьте логи: `docker-compose logs web`
2. Запустите диагностику: `python3 scripts/debug_login.py`
3. Попробуйте чистый старт (удалит данные!)
4. Посмотрите документацию выше
