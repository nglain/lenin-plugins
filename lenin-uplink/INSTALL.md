# Установка lenin-uplink

Пошаговый гайд: от нулевого Мака до работающего аплинка сессий на сервер.
Рассчитан на установщика (владелец ядра на новом Маке, или флот после consent).

> Если что-то пошло не так — сразу в раздел [Troubleshooting](#troubleshooting) внизу.

---

## Предпосылки

| Нужно | Проверка |
|---|---|
| macOS | `sw_vers` |
| Claude Code | `claude --version` |
| python3 (в системе) | `python3 --version` (≥ 3.8) |

Зависимостей нет — клиент на stdlib, ставится на чистую систему.

---

## Шаг 1. Поставить плагин

В Claude Code (любая сессия):

```
/plugin marketplace add https://github.com/nlarryelvis2-max/lenin-plugins.git
/plugin install lenin-uplink@lenin
```

Маркетплейс публичный — авторизация на GitHub не нужна.

**Проверка:** в кэше появился плагин —
```
ls ~/.claude/plugins/cache/lenin/lenin-uplink/
```
должна показать версию (`1.1.x`).

---

## Шаг 2. Перезапустить Claude Code

⚠️ **Обязательный шаг, про который забывают.** Слэш-команды и хуки плагина
подхватываются **при старте** Claude Code. В сессии, где ставил, `/uplink`
будет «неизвестная команда» — это нормально, не баг.

Закрой окно (или `/exit`) и открой новый сеанс. После этого появится `/uplink`.

---

## Шаг 3. Подключить Mac

1. Выполни `/uplink setup`.
2. Открой свой профиль на `https://lenin.nglain.com`.
3. Нажми **«Подключить Mac»** и подтверди передачу истории Claude Code.
4. Скопируй одноразовый код и выполни:

```
/uplink register ОДНОРАЗОВЫЙ_КОД
```

Код действует 10 минут и только один раз. Плагин получает отдельный token для
этого Mac и сохраняет его в `~/.claude/lenin_uplink/config.json` с правами
`0600`. Token в чат не печатается.

---

## Шаг 4. Проверить

```
/uplink status
```
или напрямую:
```
python3 ~/.claude/plugins/cache/lenin/lenin-uplink/*/scripts/session_uplink.py --status
```

Должно показать: endpoint, owner/core/machine, last_run, сколько файлов и МБ
не отправлено.

**Тестовая отправка** (ограничь объём, чтобы не вывалить гигабайты за раз):
```
/uplink dry      # показать, что ушло бы — без реальной отправки
/uplink run      # реально отправить (все лимиты из config)
```

Документация контракта ручки (для тех, кто пишет сервер): `UPLINK_CONTRACT.md`.

---

## Шаг 5. Автозапуск (launchd)

Команда `register` ставит ежедневный будильник автоматически. Повторная ручная
установка нужна только для ремонта:

```
/uplink install
```

Ставит `~/Library/LaunchAgents/com.lenin.session-uplink.plist` (ежедневно
08:10 + RunAtLoad). SessionStart-хук плагина — страховка: если зайдёшь в
Ленин, а аплинка не было >24ч, запустит в фоне.

**Проверка launchd:**
```
launchctl list com.lenin.session-uplink
```
`LastExitStatus = 0` — ок.

---

## Шаг 6. Health-check (doctor)

```
python3 ~/.claude/plugins/cache/lenin/lenin-uplink/*/scripts/doctor.py
```

Проверяет всё одним прогоном: python3, config.json (валидность + 4 поля
заполнены), достижимость endpoint, launchd установлен и загружен, сколько
не отправлено. Если что-то не так — говорит конкретно, что именно.

---

## Troubleshooting

| Симптом | Причина / fix |
|---|---|
| `/uplink` — «неизвестная команда» | Сессия стартовала до установки. Перезапусти Claude Code (шаг 2). |
| `LastExitStatus ≠ 0` у launchd | Смотри логи: `cat ~/.claude/lenin_uplink/launchd.err` |
| «ошибка отправки» в run | Сервер недоступен. `doctor.py` подскажет состояние. |
| «доступ отозван» | Сервер вернул 403, поэтому плагин безопасно выключился. Получи новый код в профиле и повтори `/uplink register КОД`. |
| launchd-plist указывает на старую версию после обновы | Самопочинка: SessionStart-хук переустановит. Либо вручную `/uplink install`. |
| Ничего не отправляется, «0 chunk(s)» | Всё уже синхронизировано (offset = размер). Проверь `/uplink status` — «не отправлено: 0MB». |
| Код просрочен | Получи новый в профиле: старый живёт 10 минут и одноразовый. |
| Хочу выключить | `enabled: false` в config.json (всё стопается), либо `/plugin uninstall lenin-uplink@lenin`. |

Логи: `~/.claude/lenin_uplink/uplink.log` (каждый прогон), `launchd.log`/`launchd.err`.

---

## Удаление

```
/plugin uninstall lenin-uplink@lenin
launchctl unload ~/Library/LaunchAgents/com.lenin.session-uplink.plist
rm ~/Library/LaunchAgents/com.lenin.session-uplink.plist
rm -rf ~/.claude/lenin_uplink      # конфиг + state + логи (опц.)
```

Отправленные на сервер данные этим не удаляются — отзыв через серверный
механизм (см. UPLINK_CONTRACT.md §6, `403` + `enabled: false`).
