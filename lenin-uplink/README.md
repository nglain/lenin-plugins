# lenin-uplink — плагин централизации сессий

Часть экосистемы Ленин. **Полный гайд по установке: [`INSTALL.md`](INSTALL.md).**
Health-check одной командой: `python3 scripts/doctor.py`.

Архитектурный принцип раздачи:
**ядро = данные владельца** (папка с CLAUDE.md / library / hot — личное, не
распространяется), **плагин = поведение** (хуки, команды, скрипты — ставится
и обновляется через маркетплейс). Этот плагин — первый в линии.

## Что делает

Раз в сутки отправляет **новые байты** сессионных файлов Claude Code
(`~/.claude/projects/**/*.jsonl`) на центральный сервер Ленина — полная
история взаимодействия человек↔ядро, для пост-обработки. Протокол и
требования к серверной ручке: `UPLINK_CONTRACT.md` (`lenin-uplink/1`).

Три триггера:

| Триггер | Механизм |
|---|---|
| ежедневно 08:10 | launchd `com.lenin.session-uplink` |
| Мак включили | тот же launchd, `RunAtLoad` |
| зашёл в Ленин, аплинка не было >24ч | SessionStart-хук плагина → фоновый прогон |

Инкрементально (byte-offset манифест, шлётся только новое), идемпотентно
(ретраи и дубли безвредны), самовосстанавливается (сервер — истина по
offset). Обкатано: heal/resync тесты, байт-в-байт сверка.

## Установка

Маркетплейс живёт в отдельном публичном репозитории `lenin-plugins` (только
поведение, без личных данных). На любом Mac:

```
/plugin marketplace add https://github.com/nlarryelvis2-max/lenin-plugins.git
/plugin install lenin-uplink@lenin
/uplink setup
```

`/uplink setup` направит в профиль на `lenin.nglain.com`: там пользователь
явно подтверждает передачу истории и получает одноразовый код. Команда
`/uplink register КОД` подключает Mac, сохраняет секрет с правами `0600`,
ставит launchd и делает первый прогон. Endpoint и token вручную не вводятся.

Конфиг: `~/.claude/lenin_uplink/config.json`. До регистрации синхронизация
выключена. Token не выводится в чат и не хранится в репозитории.

## Команды

`/uplink` (= status) · `/uplink setup` · `/uplink register КОД` · `/uplink run` · `/uplink dry` · `/uplink doctor`

## Этика (канон data-exchange-ethics)

Сырые транскрипты = personal_special. Плагин ставится на машины флота
**только с явным consent владельца ядра** — consent фиксируется при выдаче
токена. Отзыв: сервер помечает токен → 403; локально `enabled: false` в
конфиге выключает всё.

## Файлы

```
.claude-plugin/plugin.json      манифест
hooks/hooks.json                SessionStart-подхват
scripts/session_uplink.py       клиент (stdlib, один файл, позиционно-независим)
scripts/session_uplink_check.py проверка >24ч → фоновый прогон
scripts/uplink_mock_server.py   мок-ручка / эталон для серверной разработки
commands/uplink.md              слэш-команда /uplink
UPLINK_CONTRACT.md              контракт серверной ручки (передаётся на разработку)
```
