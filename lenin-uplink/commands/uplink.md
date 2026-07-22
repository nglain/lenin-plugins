---
description: "Подключение и синхронизация сессий Claude Code с Lenin"
allowed-tools: ["Bash"]
---

Управление централизацией сессий (плагин lenin-uplink). Аргумент пользователя: `$ARGUMENTS`.

Выполни соответствующую команду через Bash:

- без аргумента или `status` → `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/session_uplink.py" --status`
- `run` → `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/session_uplink.py" --run`
- `dry` → `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/session_uplink.py" --dry-run`
- `install` → `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/session_uplink.py" --install-launchd`
- `register <КОД>` → выполни `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/register.py" "<КОД>"`. Если регистрация успешна, затем выполни `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/session_uplink.py" --install-launchd` и один `--run`. Никогда не показывай содержимое `config.json` или token.
- `setup` → объясни: открой профиль на `https://lenin.nglain.com`, нажми «Подключить Mac», подтверди передачу истории и скопируй одноразовый код. Затем используй `/uplink register КОД`.
- `doctor` → `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py"` — health-check всей установки одним прогоном.
- `test` → `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/test_uplink.py"` — end-to-end тест на моке одной командой (поднимает мок → прогон → проверка приёма → идемпотентность → гасит мок).

Вывод команды передай кратко. Не читай и не печатай token: он хранится только в `~/.claude/lenin_uplink/config.json` с правами `0600`.
