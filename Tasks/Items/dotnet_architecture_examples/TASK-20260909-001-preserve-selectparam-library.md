---
type: task
id: TASK-20260909-001
created: 2026-09-09
project: dotnet_architecture_examples
---

# TASK-20260909-001 — Сохранить общую библиотеку SelectParam

## Проект: dotnet_architecture_examples

- [r] Перенести Service.Model.EF.SelectParam в общие архитектурные библиотеки 🆔 TASK-20260909-001

## Цель

Сохранить библиотеку динамического составления запросов как общий проект архитектурных примеров.

## Описание

Перенести проект из `Sources/old/WebAPI.Monitor/src/Service.Model.EF.SelectParam` в `Sources/Architectures/LibProject/netstandard2.0/SelectParam`.

## Критерии приёмки

- Имя проекта сохранено: `Service.Model.EF.SelectParam`.
- Целевая платформа сохранена: `netstandard2.0`.
- Исходный код библиотеки перенесён без изменения исходного проекта в `Sources/old/`.
- В проект включены только необходимые зависимости; версии сохранённых зависимостей не изменены.
- Перенесённый проект успешно собирается.

## Ограничения

- Не изменять исходный проект в `Sources/old/WebAPI.Monitor`.
- Не добавлять новые библиотеки, версии, solution или Git-репозиторий.

## Артефакты

- Исходник: `Sources/old/WebAPI.Monitor/src/Service.Model.EF.SelectParam`.
- Результат: `Sources/Architectures/LibProject/netstandard2.0/SelectParam`.

## Код и GitHub

- Репозиторий: `Sources/Architectures` (`dotnet_architecture_examples`).
- Проект: `Sources/Architectures/LibProject/netstandard2.0/SelectParam/Service.Model.EF.SelectParam.csproj`.
- Commit: [`25997e7`](https://github.com/parad74/dotnet_architecture_examples/commit/25997e70422a223d12ab80d74c670d22d48597a0).

## Результат

- В `LibProject/netstandard2.0/SelectParam` добавлены проект, восемь файлов исходного кода, текущий файл решения и `readme.txt`; на момент публикации `readme.txt` пуст.
- Сохранены `netstandard2.0`, имя сборки `Service.Model.EF.SelectParam`, `EntityFramework 6.4.0` и необходимая для Reflection.Emit зависимость `Microsoft.Windows.Compatibility 3.1.1`.
- Неиспользуемые зависимости SQL Server Compact, SQLite и bulk-copy исключены.
- Текст восьми перенесённых файлов исходного кода совпадает с оригиналом.
- `dotnet build` завершён успешно: 0 предупреждений, 0 ошибок.

## Журнал

- 2026-09-09 — Работа начата, статус `Doing`.
- 2026-09-09 — Перенос и сборка завершены, статус `Review`.
- 2026-09-09 — Commit `25997e7` отправлен в GitHub; повторная сборка успешна.
