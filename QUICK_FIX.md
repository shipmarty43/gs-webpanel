# Быстрое решение проблемы с логином

## Проблема: HTTP 401 (Unauthorized) при входе

Тесты показали, что учетные данные в базе данных корректны, но вход не работает.

## Решение (выберите один из способов)

### Способ 1: Сброс пароля через Docker (Рекомендуется)

```bash
# 1. Перезапустить контейнеры с новой конфигурацией
docker-compose down
docker-compose up -d

# 2. Подождать 5 секунд, затем сбросить пароль
docker-compose exec web python3 scripts/reset_admin.py

# 3. Войти с новыми учетными данными
# URL: http://localhost:3000/login
# Username: admin
# Password: Admin123456!
```

### Способ 2: Сброс пароля локально (Быстрее)

```bash
# Запустить скрипт напрямую (без Docker)
python3 scripts/reset_admin.py

# Войти с учетными данными
# URL: http://localhost:3000/login
# Username: admin
# Password: Admin123456!
```

### Способ 3: Только перезагрузка

Иногда достаточно просто перезагрузить:

```bash
docker-compose restart web

# Подождать 5 секунд, затем попробовать войти
# Username: admin
# Password: Admin123456!
```

## Проверка результата

После выполнения команд:

1. Откройте http://localhost:3000/login
2. Введите точно (без ошибок):
   - **Username**: `admin`
   - **Password**: `Admin123456!`
3. Нажмите Login

**Важно:**
- Не копируйте пароль - вводите вручную
- Проверьте, что Caps Lock выключен
- Пароль чувствителен к регистру: `Admin123456!` (не admin123456!)

## Если всё равно не работает

### Проверка 1: Контейнер запущен?

```bash
docker-compose ps

# Должно показать:
# c2-panel-web    Up X minutes
```

### Проверка 2: Логи сервера

```bash
docker-compose logs web --tail=30

# Ищите ошибки или сообщения о неудачных попытках входа
```

### Проверка 3: Тест через curl

```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin123456!"}'

# Должно вернуть:
# {"access_token":"...", "token_type":"bearer"}

# Если вернулось {"detail":"Incorrect username or password"}
# Запустите: python3 scripts/reset_admin.py
```

### Проверка 4: Браузер

- Очистите cookies для localhost:3000
- Попробуйте в режиме инкогнито
- Откройте DevTools (F12) → Console - проверьте ошибки
- Откройте DevTools (F12) → Network → смотрите что отправляется в /api/auth/login

## Полный сброс (крайняя мера)

**ВНИМАНИЕ:** Это удалит все данные!

```bash
# Остановить и удалить все
docker-compose down -v

# Удалить базу данных
rm data/c2panel.db

# Запустить заново
docker-compose up -d

# Подождать 10 секунд

# Создать admin пользователя
docker-compose exec web python3 scripts/init_db.py
docker-compose exec web python3 scripts/reset_admin.py

# Войти
```

## Дополнительные скрипты для диагностики

```bash
# Проверить что пароль в БД правильный
python3 scripts/test_login.py

# Подробная диагностика
python3 scripts/debug_login.py

# Тест API
bash scripts/test_api_login.sh
```

## Поддержка

Если ничего не помогло:

1. Сделайте скриншот ошибки в браузере
2. Запустите: `docker-compose logs web > logs.txt`
3. Проверьте консоль браузера (F12)
4. Проверьте Network tab в DevTools при попытке входа
