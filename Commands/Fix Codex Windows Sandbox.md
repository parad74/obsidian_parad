# Исправление ошибки Windows-песочницы Codex

## Когда применять

Используй эту инструкцию, если локальная команда Codex завершается ошибкой:

```text
helper_unknown_error: setup refresh had errors
```

Сначала выполни одну безопасную проверку чтения в песочнице. Если она возвращает эту же ошибку, не повторяй одинаковые попытки и не создавай серию запросов `require_escalated` без объяснения причины.

## Ошибка редактора `apply_patch` на `reparse point`

Это отдельная ошибка, не требующая изменения владельца или ACL:

```text
Failed to read file ...: path contains a reparse point
```

Она может возникать, даже если PowerShell читает файл, рабочий каталог доступен для записи, а `LinkType` у пути не указан. Если встроенный редактор не принимает путь, не применяй к этой ошибке исправление владельца из следующего раздела.

Проверенный обход на Windows — вызвать тот же `codex.exe` напрямую и передать весь patch одним UTF-8 аргументом. Сначала найди wrapper и прочитай из него фактический путь к исполняемому файлу:

```powershell
$applyPatchWrapper = (Get-Command apply_patch).Source
Get-Content -LiteralPath $applyPatchWrapper -Raw
```

В `apply_patch.bat` команда содержит `codex.exe` и параметр `--codex-run-as-apply-patch`. Разреши показанный относительный путь от каталога wrapper либо используй точный абсолютный путь к этому `codex.exe`. Затем передай patch напрямую:

```powershell
$codexExe = '<точный путь к codex.exe из apply_patch.bat>'
$patchText = @'
*** Begin Patch
*** Update File: path/to/file.md
@@
-old
+new
*** End Patch
'@
$patchText = $patchText.TrimEnd("`r", "`n")
& $codexExe --codex-run-as-apply-patch $patchText
```

Вызов самого `apply_patch.bat` с многострочным patch может разбить аргумент и завершиться сообщением `--codex-run-as-apply-patch requires a UTF-8 PATCH argument` либо `The last line of the patch must be '*** End Patch'`. Поэтому при этом обходе вызывай именно `codex.exe` и передавай `$patchText` одним аргументом. После применения проверь целевой diff. Путь к `codex.exe` зависит от установленной сборки Codex, поэтому не сохраняй текущий hash каталога как постоянный.

## Диагностика

### Большой patch не запускается из-за длины команды

При прямом вызове редактора с большим patch в этой сессии получено сообщение `Имя файла или его расширение имеет слишком большую длину`. Тот же целевой файл успешно изменялся меньшими patch. Это локально проверенный случай передачи большого аргумента, а не основание переименовывать файл или менять ACL.

Раздели правку на небольшие самостоятельные patch по разделам, применяя их последовательно тем же редактором. Перед следующим patch учитывай уже изменённый текст; после всех частей проверь итоговый diff и сохранность разделов. Не заменяй редактирование перезаписью всего файла через shell. Обход проверен в этой рабочей сессии; официальный раздел Windows sandbox не описывает именно этот случай.

### Диагностика setup refresh

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

- [OpenAI Docs — Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox) — общая диагностика песочницы; локальные обходы редактора выше проверены отдельно.
