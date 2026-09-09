# Исправление ошибки Windows-песочницы Codex

## Когда применять

Используй эту инструкцию, если локальная команда Codex завершается ошибкой:

```text
helper_unknown_error: setup refresh had errors
```

Сначала выполни одну безопасную проверку чтения в песочнице. Если она возвращает эту же ошибку, не повторяй одинаковые попытки и не создавай серию запросов `require_escalated` без объяснения причины.

## Диагностика

Если обычный доступ заблокирован, запроси один повышенный запуск только для чтения диагностических данных. Профиль пользователя определяй через:

```powershell
$userProfilePath = [Environment]::GetFolderPath('UserProfile')
```

Проверь:

- `$userProfilePath\.codex\.sandbox\setup_error.json`;
- самый свежий `$userProfilePath\.codex\.sandbox\sandbox.YYYY-MM-DD.log`.

Найди сообщение `SetNamedSecurityInfoW failed`, указанный рядом путь и код ошибки. Если код равен `5`, а проблемный путь указывает на `.git` или `.codex`, проверь владельца точного каталога:

```powershell
(Get-Acl -LiteralPath 'W:\obsidian\_parad\.git').Owner
```

Если владельцем указан служебный пользователь вида `CodexSandboxOffline`, предложи Parad закрыть Codex, открыть PowerShell или Windows Terminal **от имени администратора** и исправить владельца только у найденного каталога:

```powershell
$targetPath = 'W:\obsidian\_parad\.git'
$currentIdentity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
icacls.exe $targetPath /setowner $currentIdentity
```

Затем проверить результат:

```powershell
(Get-Acl -LiteralPath $targetPath).Owner
```

Путь в примере обязательно замени на точный путь из журнала. Ожидаемый владелец — текущая учётная запись Parad.

Если `icacls` сообщает об отказе в доступе, допустим резервный вариант для того же точного каталога:

```powershell
takeown.exe /F $targetPath /A
icacls.exe $targetPath /setowner $currentIdentity
```

## Ограничения безопасности

- Не удаляй `.git` и не выполняй `git init` для исправления этой ошибки.
- Не используй по умолчанию `icacls /reset /T`, `takeown /R` и другие широкие рекурсивные изменения прав.
- Не применяй исправление к корню диска, профилю пользователя или всему vault.
- Не считай `git safe.directory` исправлением: он обходит проверку Git, но не восстанавливает работу песочницы.
- Если путь, сообщение или код ошибки отличаются, не угадывай причину. Сообщи Parad точные данные из журнала и предложи решение для фактической ошибки.

## Проверка после исправления

После изменения владельца Parad должна снова открыть Codex. Затем проверь без повышения прав:

1. Простое чтение файла в рабочем каталоге.
2. Создание и удаление небольшого контрольного файла через `apply_patch`.
3. `git status` без добавления `safe.directory`.

Контрольный файл после проверки удали и убедись, что он не остался в `git status`.

## Справка

- [OpenAI Docs — Windows sandbox](https://learn.chatgpt.com/codex/windows/windows-sandbox)
