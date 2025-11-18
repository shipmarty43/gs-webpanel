# Решение ошибки "FILE_ERROR_NO_SPACE" в Chrome

## Проблема

Ошибка:
```
Uncaught (in promise) Error: IO error: .../051293.ldb: FILE_ERROR_NO_SPACE
```

Это ошибка браузера Chrome - заполнено локальное хранилище (localStorage/IndexedDB) или кеш.

## ⚡ Быстрые решения

### Решение 1: Очистка через DevTools (Рекомендуется)

1. Откройте **DevTools**: `F12` или `Ctrl+Shift+I` (Mac: `Cmd+Option+I`)
2. Перейдите на вкладку **Application**
3. В левой панели найдите **Storage** → **Clear site data**
4. Нажмите **"Clear site data"**
5. Закройте DevTools и **перезагрузите страницу**: `Ctrl+R`

### Решение 2: Через настройки Chrome

```
1. Chrome → ⋮ (три точки) → Settings (или chrome://settings/)
2. Privacy and security → Clear browsing data
3. Выберите "All time" (За все время)
4. Отметьте галочки:
   ☑ Cookies and other site data
   ☑ Cached images and files
   ☑ Site settings (опционально)
5. Нажмите "Clear data"
6. Закройте и откройте Chrome заново
```

### Решение 3: Режим инкогнито (Временное решение)

Самый быстрый способ:
- **Windows/Linux**: `Ctrl+Shift+N`
- **Mac**: `Cmd+Shift+N`

Откройте панель в режиме инкогнито - там чистое хранилище.

### Решение 4: Проверка места на диске

**Windows:**
```cmd
# Откройте PowerShell или CMD
wmic logicaldisk get caption,freespace,size

# Или через GUI: This PC → посмотрите свободное место на C:\
```

**Linux/Mac:**
```bash
df -h
# Проверьте строку с / или /home
```

Убедитесь что есть минимум **1-2 GB свободного места**.

Если диска мало:
```bash
# Linux: Очистить кеш apt
sudo apt clean
sudo apt autoremove

# Очистить временные файлы
sudo rm -rf /tmp/*

# Найти большие файлы
du -h / | sort -rh | head -20
```

## 🔧 Постоянное решение

Я добавил автоматическую очистку в код панели:

### Что изменилось:

1. **При logout** теперь очищается:
   - localStorage (токены)
   - sessionStorage
   - IndexedDB (если есть)

2. **При загрузке страницы:**
   - Проверяется квота storage
   - Автоматически очищаются старые кешированные данные
   - Показывается предупреждение если storage почти заполнен

### Применение обновления:

```bash
# Получить последние изменения
git pull origin claude/gsocket-c2-panel-01CChs23hpBqkFEJi2ygWxWR

# Перезапустить (без ребилда)
docker-compose restart web

# Или если используете без Docker
# Просто перезагрузите страницу в браузере с очисткой кеша (Ctrl+Shift+R)
```

## 🔍 Диагностика

### Проверка квоты storage в Console

Откройте DevTools (`F12`) → Console, введите:

```javascript
// Проверить квоту storage
navigator.storage.estimate().then(estimate => {
    const used = (estimate.usage / 1024 / 1024).toFixed(2);
    const quota = (estimate.quota / 1024 / 1024).toFixed(2);
    const percent = ((estimate.usage / estimate.quota) * 100).toFixed(1);
    console.log(`Storage: ${used} MB used of ${quota} MB (${percent}%)`);
});

// Посмотреть что в localStorage
console.log('LocalStorage size:', JSON.stringify(localStorage).length, 'bytes');
for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    const size = localStorage.getItem(key).length;
    console.log(`  ${key}: ${size} bytes`);
}

// Проверить IndexedDB
indexedDB.databases().then(dbs => {
    console.log('IndexedDB databases:', dbs);
});
```

### Очистка вручную через Console

Если панель не загружается, очистите через Console:

```javascript
// Очистить всё localStorage
localStorage.clear();

// Очистить sessionStorage
sessionStorage.clear();

// Удалить все IndexedDB базы
indexedDB.databases().then(dbs => {
    dbs.forEach(db => {
        console.log('Deleting:', db.name);
        indexedDB.deleteDatabase(db.name);
    });
});

// Перезагрузить страницу
location.reload();
```

## 🛡️ Предотвращение проблемы

### Рекомендации:

1. **Регулярно очищайте кеш браузера** (раз в месяц)
2. **Используйте logout** для очистки данных сессии
3. **Освобождайте место на диске** (минимум 5% свободно)
4. **Используйте разные браузеры** для разных целей

### Chrome настройки для автоочистки:

```
chrome://settings/content/all

1. Найдите localhost:3000
2. Нажмите "Clear data"
3. Опционально: Включите "Clear cookies and site data when you close all windows"
```

### Увеличение квоты (Advanced):

Chrome обычно выделяет ~60% доступного места на диске для storage.

Чтобы увеличить:
1. Освободите больше места на диске
2. Chrome автоматически увеличит квоту

## 📊 Типичные причины

### 1. Накопление токенов

**Симптомы:** При каждом login создается новый токен

**Решение:** Обновленный код теперь автоматически очищает старые токены

### 2. Кеш xterm.js терминала

**Симптомы:** После долгой работы с терминалом storage заполняется

**Решение:**
- Закрывайте вкладки терминала когда не используете
- Делайте logout периодически
- Используйте кнопку "Clear" в терминале

### 3. Заполнен диск компьютера

**Симптомы:** Общая нехватка места

**Решение:**
```bash
# Windows: Disk Cleanup
cleanmgr

# Linux: Очистка системы
sudo apt clean
sudo journalctl --vacuum-time=7d
docker system prune -a  # Очистка Docker
```

### 4. Множество вкладок

**Симптомы:** Открыто много вкладок панели одновременно

**Решение:**
- Закройте неиспользуемые вкладки
- Используйте одну вкладку для работы

## 🔧 Если ничего не помогает

### Полный сброс Chrome profile:

**ВНИМАНИЕ:** Это удалит все настройки, закладки, расширения!

```
1. Закройте Chrome полностью
2. Найдите папку профиля:
   Windows: %LOCALAPPDATA%\Google\Chrome\User Data\
   Linux: ~/.config/google-chrome/
   Mac: ~/Library/Application Support/Google/Chrome/

3. Переименуйте папку "Default" в "Default.old"
4. Запустите Chrome - создастся новый чистый профиль
```

### Альтернативные браузеры:

Если проблема сохраняется в Chrome:
- Firefox
- Edge (Chromium)
- Brave

Они используют ту же панель, но имеют независимое storage.

## 📚 Дополнительная информация

### Chrome storage limits:

- **localStorage**: ~10 MB per origin
- **IndexedDB**: ~60% of available disk space
- **Cache API**: ~60% of available disk space
- **Total per origin**: Limited by disk space

### Проверка использования:

```
chrome://quota-internals/
```

Здесь можно увидеть сколько места использует каждый сайт.

### Очистка конкретного сайта:

```
chrome://settings/siteData

1. Найдите localhost:3000
2. Нажмите корзину для удаления
```

## ✅ Checklist решения:

- [ ] Очистили кеш через DevTools (Application → Clear site data)
- [ ] Проверили свободное место на диске (минимум 1GB)
- [ ] Закрыли лишние вкладки панели
- [ ] Перезагрузили страницу с очисткой кеша (Ctrl+Shift+R)
- [ ] Попробовали режим инкогнито
- [ ] Применили обновление кода (git pull + restart)
- [ ] Делаете logout периодически

## 💡 Если нужна помощь:

1. Откройте Console (F12)
2. Запустите диагностику (код выше)
3. Сделайте скриншот результатов
4. Проверьте логи Docker: `docker-compose logs web --tail=50`

---

**Краткая инструкция:**
```
1. F12 → Application → Clear site data
2. Ctrl+Shift+R (перезагрузка с очисткой)
3. Готово!
```
