---
type: architecture-catalog
platform: WinForms
---

# Каталог архитектур WinForms

Архитектуры разделены по семейству runtime, а не по возрасту. `.NET Framework` и современный `.NET` считаются равноправными вариантами для разных задач.

| Архитектура | Runtime | Главное отличие | Эталон |
| --- | --- | --- | --- |
| [[Documents/Architectures/WinForms/DotNetFramework/WinForms - View - Presenter - DIUnity - IModule]] | .NET Framework 4.6.1 | Форма получает Presenter и связывает его с View; модули и зависимости регистрируются в Unity | `Sources/Architectures/WinForms/DotNetFramework/WinForms.NETFramework.App1/` |
| [[Documents/Architectures/WinForms/DotNet/WinForms - View - Presenter - DI]] | Версия .NET выбирается перед созданием | View публикует события и ничего не знает о Presenter | Ещё не создан |

## Кубики .NET Framework

| Кубик | Назначение | Проект | Режимы применения |
| --- | --- | --- | --- |
| [[Documents/Architectures/Cubes/DotNetFramework/Service - DIUnity]] | Сервис состояния с операциями `Save` и `Clear`, подключаемый через Unity | `Common.Service` | Интеграция в существующий solution или отдельный solution |

## Где находится код

- Старый проект-источник: `Sources/old/PreTestWCF/`.
- Эталонные реализации и будущие шаблоны: `Sources/Architectures/WinForms/`.
- Обычные рабочие приложения не размещаются внутри `Sources/Architectures/`.

## Порядок развития решения

1. Согласовать архитектурную карточку.
2. Создать минимальную эталонную реализацию.
3. Проверить сборку, запуск и работу WinForms Designer.
4. После повторного использования решить, нужен ли шаблон `dotnet new`.
