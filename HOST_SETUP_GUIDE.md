# Руководство по настройке хостов для GSocket C2 Panel

## Обзор

Для работы с панелью, каждый управляемый хост должен быть настроен с **gsocket агентом в режиме listening**. Панель будет подключаться к хостам как клиент и отправлять команды.

### Важно: Как работает идентификация

**GSocket использует ТОЛЬКО секретный токен для идентификации подключения:**
- ✅ **Секрет (Secret)** - это глобальный уникальный идентификатор подключения
- ✅ Оба конца (хост и панель) используют **один и тот же секрет**
- ✅ Hostname в панели - это просто **описательное имя для вашего удобства**
- ❌ Hostname **НЕ** используется для подключения к хосту

**Пример:**
- Хост запускается с секретом: `gs-netcat -l -s "6fzXHFQ7gNwN..."`
- Панель подключается используя тот же секрет
- В панели вы называете этот хост "web-server-01" (просто для удобства)

## Предварительные требования

- Доступ к целевому хосту (SSH, физический доступ и т.д.)
- Root или sudo привилегии
- Интернет соединение для установки gsocket

## Шаг 1: Установка gsocket

### Linux (все дистрибутивы)

```bash
# Автоматическая установка через официальный скрипт
bash -c "$(curl -fsSL https://gsocket.io/x)"
```

Или вручную:

```bash
git clone https://github.com/hackerschoice/gsocket.git
cd gsocket
./bootstrap
./configure
make
sudo make install
```

### Проверка установки

```bash
which gs-netcat
# Должно вывести: /usr/local/bin/gs-netcat или /usr/bin/gs-netcat

gs-netcat --version
# Должно показать версию
```

## Шаг 2: Генерация секретного ключа

Для каждого хоста необходим уникальный секретный ключ:

```bash
gs-netcat -g
```

**Пример вывода:**
```
6fzXHFQ7gNwNEpmKvGKZvZYxZw4Q4KLrgvnF2k2pCGk=
```

**ВАЖНО:**
- Сохраните этот ключ - он понадобится при добавлении хоста в панель
- Каждый хост должен иметь уникальный ключ
- Храните ключи в безопасном месте (например, password manager)

## Шаг 3: Запуск gsocket агента

### Метод 1: Запуск в фоновом режиме (для тестирования)

```bash
# Замените YOUR_SECRET_KEY на сгенерированный ключ
GSOCKET_ARGS="-s YOUR_SECRET_KEY" gs-netcat -l -e /bin/bash -D
```

Флаги:
- `-l` - режим listening (ожидание подключений)
- `-e /bin/bash` - выполнять команды через bash
- `-D` - daemon mode с автоматическим переподключением

### Метод 2: Systemd service (рекомендуется для production)

Создайте systemd service для автоматического запуска при загрузке:

```bash
# Создайте файл сервиса
sudo tee /etc/systemd/system/gsocket-agent.service > /dev/null <<'EOF'
[Unit]
Description=GSocket C2 Agent
After=network.target
Wants=network-online.target

[Service]
Type=simple
Restart=always
RestartSec=10
Environment="GSOCKET_ARGS=-s YOUR_SECRET_KEY_HERE"
ExecStart=/usr/local/bin/gs-netcat -l -e /bin/bash -D
StandardOutput=journal
StandardError=journal

# Security hardening (опционально)
# NoNewPrivileges=true
# PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# ВАЖНО: Замените YOUR_SECRET_KEY_HERE на настоящий ключ!
sudo sed -i 's/YOUR_SECRET_KEY_HERE/6fzXHFQ7gNwNEpmKvGKZvZYxZw4Q4KLrgvnF2k2pCGk=/g' /etc/systemd/system/gsocket-agent.service

# Перезагрузите systemd и запустите сервис
sudo systemctl daemon-reload
sudo systemctl enable gsocket-agent
sudo systemctl start gsocket-agent

# Проверьте статус
sudo systemctl status gsocket-agent
```

### Метод 3: Cron (альтернатива для старых систем)

```bash
# Добавьте в crontab
crontab -e

# Добавьте строку:
@reboot GSOCKET_ARGS="-s YOUR_SECRET_KEY" /usr/local/bin/gs-netcat -l -e /bin/bash -D
```

## Шаг 4: Проверка работоспособности

### На хосте

```bash
# Проверьте, что процесс запущен
ps aux | grep gs-netcat

# Должно показать что-то вроде:
# user  1234  0.0  0.1  12345  6789 ?  Ss  10:00  0:00 gs-netcat -l -e /bin/bash -D

# Проверьте логи systemd (если используете systemd)
sudo journalctl -u gsocket-agent -f
```

### С другой машины (тест подключения)

```bash
# На машине с gsocket установленным
GSOCKET_ARGS="-s YOUR_SECRET_KEY" gs-netcat

# После подключения введите:
hostname
# Должно вернуть hostname целевого хоста

# Выйдите:
exit
```

## Шаг 5: Добавление хоста в панель

1. Откройте web-панель: http://your-panel-address:3000
2. Войдите в систему
3. Перейдите в раздел **Hosts**
4. Нажмите **+ Add Host**
5. Заполните форму:
   - **Hostname**: имя хоста (например: web-server-01)
   - **IP Address**: IP адрес (опционально, для справки)
   - **GSocket Secret**: вставьте сгенерированный ключ
   - **Description**: описание хоста
   - **Notes**: дополнительные заметки
   - **Tags**: теги для группировки (через запятую)
6. Нажмите **Add Host**

## Проверка через панель

После добавления хоста:

1. Monitor service автоматически проверит доступность (каждые 3 минуты)
2. Статус хоста изменится на **online** если всё настроено правильно
3. Вы можете создать тестовую задачу:
   - Перейдите в **Scripts**
   - Создайте скрипт с командой: `hostname && uname -a`
   - Перейдите в **Tasks**
   - Создайте задачу с этим скриптом для вашего хоста
   - Проверьте результаты

## Безопасность

### Рекомендации по безопасности:

1. **Уникальные ключи**: Используйте уникальный ключ для каждого хоста
2. **Ротация ключей**: Меняйте ключи периодически (например, раз в 3-6 месяцев)
3. **Мониторинг**: Следите за логами подключений
4. **Firewall**: Рассмотрите ограничение исходящих подключений (если критично)
5. **Encrypted transport**: gsocket использует AES-256-CBC encryption по умолчанию

### Дополнительная защита:

#### Routing через TOR (опционально)

Для анонимности можно маршрутизировать gsocket через TOR:

```bash
# Установите TOR
sudo apt-get install tor

# Запустите gsocket через TOR
GSOCKET_ARGS="-s YOUR_SECRET_KEY -T" gs-netcat -l -e /bin/bash -D
```

#### Ограничение команд

Для ограничения выполняемых команд используйте wrapper script:

```bash
# Создайте wrapper
cat > /usr/local/bin/gsocket-wrapper.sh <<'EOF'
#!/bin/bash
# Wrapper для ограничения команд

# Разрешенные команды
case "$1" in
  hostname|uptime|df|free)
    $@
    ;;
  *)
    echo "Command not allowed"
    exit 1
    ;;
esac
EOF

chmod +x /usr/local/bin/gsocket-wrapper.sh

# Используйте wrapper вместо /bin/bash
GSOCKET_ARGS="-s YOUR_SECRET_KEY" gs-netcat -l -e /usr/local/bin/gsocket-wrapper.sh -D
```

## Troubleshooting

### Хост показывается как offline

**Проверьте:**

1. Процесс gsocket запущен:
   ```bash
   ps aux | grep gs-netcat
   ```

2. Нет ошибок в логах:
   ```bash
   sudo journalctl -u gsocket-agent -n 50
   ```

3. Интернет доступен:
   ```bash
   ping -c 3 8.8.8.8
   ```

4. Секрет правильный (попробуйте подключиться вручную)

### Connection refused или timeout

- Проверьте что хост запущен с флагом `-l` (listen mode)
- Проверьте что используется правильный секрет
- Попробуйте перезапустить gsocket агент

### Command not found: gs-netcat

- Установите gsocket (см. Шаг 1)
- Проверьте PATH: `export PATH=$PATH:/usr/local/bin`

### "Authentication failed"

- Секретный ключ неверный
- Сгенерируйте новый ключ и обновите в панели и на хосте

## Массовое развертывание

Для развертывания на множестве хостов используйте ansible/puppet/chef:

### Ansible playbook пример:

```yaml
---
- name: Setup gsocket agents
  hosts: all
  become: yes
  vars:
    gsocket_secret: "{{ lookup('password', '/dev/null length=32 chars=ascii_letters,digits') }}"

  tasks:
    - name: Install gsocket
      shell: bash -c "$(curl -fsSL https://gsocket.io/x)"
      args:
        creates: /usr/local/bin/gs-netcat

    - name: Create systemd service
      template:
        src: gsocket-agent.service.j2
        dest: /etc/systemd/system/gsocket-agent.service

    - name: Enable and start service
      systemd:
        name: gsocket-agent
        enabled: yes
        state: started
        daemon_reload: yes

    - name: Save secret for panel
      local_action:
        module: copy
        content: "{{ inventory_hostname }}: {{ gsocket_secret }}"
        dest: "./secrets/{{ inventory_hostname }}.txt"
```

## Мониторинг и обслуживание

### Логи

```bash
# Systemd logs
sudo journalctl -u gsocket-agent -f

# Просмотр последних ошибок
sudo journalctl -u gsocket-agent -p err -n 20
```

### Рестарт сервиса

```bash
sudo systemctl restart gsocket-agent
```

### Обновление секрета

```bash
# 1. Сгенерируйте новый ключ
NEW_SECRET=$(gs-netcat -g)

# 2. Обновите service
sudo sed -i "s/Environment=\"GSOCKET_ARGS=.*/Environment=\"GSOCKET_ARGS=-s $NEW_SECRET\"/" /etc/systemd/system/gsocket-agent.service

# 3. Перезагрузите
sudo systemctl daemon-reload
sudo systemctl restart gsocket-agent

# 4. Обновите ключ в панели управления
```

## FAQ

**Q: Нужно ли открывать порты в firewall?**
A: Нет! Это основное преимущество gsocket - работает через NAT и firewall без конфигурации.

**Q: Безопасно ли передавать команды?**
A: Да, gsocket использует end-to-end encryption (AES-256) с SRP authentication.

**Q: Можно ли использовать один секрет для всех хостов?**
A: Технически да, но это небезопасно. Используйте уникальный секрет для каждого хоста.

**Q: Что делать если хост за корпоративным proxy?**
A: gsocket работает через HTTPS и обычно проходит через прокси. Если нет - настройте proxy в системе.

**Q: Сколько панелей могут подключаться к одному хосту?**
A: Одновременно только одна. Gsocket использует 1-to-1 соединение.

## Поддержка

- GitHub: https://github.com/hackerschoice/gsocket
- Documentation: https://www.gsocket.io/
- Issues: https://github.com/hackerschoice/gsocket/issues
