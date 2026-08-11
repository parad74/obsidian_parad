---
type: architecture-cube
runtime_family: DotNet
target_framework: net8.0
project: Common.Service
di_container: Microsoft.Extensions.DependencyInjection
---

# Service - DI

## Краткое описание

Кубик добавляет проект `Common.Service` с одной или несколькими парами «интерфейс — реализация» для современного .NET. Сервис может хранить текстовое состояние и предоставлять минимальные операции `Save` и `Clear`; конкретное назначение и контракт уточняются перед созданием. Потребитель получает интерфейс сервиса через стандартный DI `Microsoft.Extensions.DependencyInjection`.

Одна карточка поддерживает два режима:

1. интеграция `Common.Service` в существующий solution;
2. создание отдельного демонстрационного solution с тем же набором сервисов.

## Имена и количество сервисов

Перед применением кубика обязательно определить количество сервисов и имя каждого сервиса, если пользователь их ещё не указал.

- Для согласованного базового имени `<Name>` создаются класс `<Name>Service` и интерфейс `I<Name>Service`, например `TextService` и `ITextService`.
- Базовое имя запрашивается без префикса `I` и без суффикса `Service`. Если пользователь сразу указал полное имя класса или интерфейса, суффикс повторно не добавляется.
- Если предметное имя ещё не выбрано, используются нейтральные временные пары `IService1`/`Service1`, `IService2`/`Service2` и так далее.
- `IMainService` и `MainService` не являются именами по умолчанию, но могут сохраняться в эталоне или существующем коде по явному решению пользователя.
- Один проект `Common.Service` может содержать несколько независимых сервисов. Для каждого создаются отдельные файлы интерфейса и реализации и отдельная DI-регистрация.
- Codex не придумывает предметные имена сервисов.

## Состав проекта Common.Service

```text
Common.Service/
├─ Interface/
│  ├─ I<Name1>Service.cs
│  └─ I<Name2>Service.cs
├─ Service/
│  ├─ <Name1>Service.cs
│  └─ <Name2>Service.cs
├─ Common.Service.csproj
└─ packages.lock.json
```

- `Common.Service` — SDK-style Class Library для согласованной версии современного .NET.
- Каждый публичный интерфейс находится в папке `Interface/`.
- Каждая реализация сервиса находится в папке `Service/`.
- Проект сервиса не зависит от Form, View, Presenter или WinForms.
- Проект сервиса не зависит от DI-пакета: регистрация выполняется в composition root приложения.
- Логирование пользовательских действий остаётся в Presenter или вызывающем приложении и не добавляется в минимальный сервис автоматически.

## Зависимости

- Composition root подключает `Microsoft.Extensions.DependencyInjection` через `PackageReference`.
- Для воспроизводимого восстановления NuGet включаются `RestorePackagesWithLockFile` и `packages.lock.json`.
- Папка `Lib/` для современного .NET не создаётся.
- Версия SDK отдельного эталонного solution закрепляется в `global.json`.

## Минимальный контракт

```csharp
public interface IService1
{
    string SavedText { get; }

    void Save(string? text);

    void Clear();
}
```

`SavedText` нужен, чтобы потребитель и автоматическая проверка могли получить фактически сохранённое значение.

## Поведение временного Service1

```csharp
public sealed class Service1 : IService1
{
    private string _savedText = string.Empty;

    public string SavedText => _savedText;

    public void Save(string? text)
    {
        _savedText = text ?? string.Empty;
    }

    public void Clear()
    {
        _savedText = string.Empty;
    }
}
```

Правила поведения:

- `Save` заменяет предыдущее значение новым;
- `null` сохраняется как `string.Empty`;
- `Clear` устанавливает `SavedText` в `string.Empty`;
- состояние хранится только в памяти и не переживает перезапуск приложения;
- nullable reference types включены, поэтому допустимость `null` явно отражается в сигнатуре `Save(string? text)`.

## Режим 1 — интеграция в существующий solution

Codex должен:

1. Прочитать целевую архитектурную карточку и существующий solution.
2. Проверить совместимость целевых framework проектов.
3. Создать или дополнить проект `Common.Service` по структуре этой карточки.
4. Добавить ссылку на `Common.Service` только в проекты-потребители, обычно в composition root или Presenter.
5. Зарегистрировать каждую пару интерфейса и реализации в существующем `IServiceCollection`. Для временного имени первого сервиса:

```csharp
services.AddSingleton<IService1, Service1>();
```

6. Передать нужные интерфейсы сервисов в потребители через конструкторы.
7. Если потребитель сам хранит состояние, обслуживаемое сервисом, удалить дублирование и делегировать операции сервису.
8. Не создавать новый solution и не копировать существующие проекты.
9. Не менять View и визуальную разметку, если это не требуется для подключения сервиса.

### Интеграция с WinForms View–Presenter

При интеграции в современный WinForms View–Presenter ожидается:

- `MainPresenter` получает интерфейс выбранного сервиса через конструктор;
- внутреннее поле Presenter с обслуживаемым состоянием удаляется;
- обработчик `Save` передаёт текст View в сервис;
- обработчик `Clear` вызывает сервис и очищает View;
- существующее логирование через `ILog` остаётся в Presenter;
- сервис регистрируется с согласованным lifetime, по умолчанию singleton для состояния в памяти.

## Режим 2 — отдельный solution

Codex должен:

1. Спросить название нового solution, если пользователь его не указал.
2. Создать отдельный solution, не изменяя существующие проекты.
3. Создать проект `Common.Service` с согласованным количеством сервисов.
4. Для запуска и проверки по умолчанию создать минимальный Console-проект `Main` на выбранной версии .NET.
5. Подключить `Microsoft.Extensions.DependencyInjection` к `Main` через `PackageReference`.
6. Зарегистрировать каждую пару в `ServiceCollection`, собрать `ServiceProvider` с проверкой графа и получить сервисы через DI.
7. Для минимального контракта проверить singleton lifetime, два последовательных `Save`, `Save(null)`, `Clear` и пустое итоговое значение каждого сервиса.

Если пользователь явно попросит WinForms-host вместо Console, интерфейс host определяется отдельно и не считается частью кубика сервиса.

## Вопросы перед применением

Задавай только вопросы, ответы на которые ещё не известны:

1. Режим: интеграция в существующий solution или отдельный solution?
2. Какая версия .NET и целевой framework используются?
3. Сколько сервисов должно находиться в `Common.Service`?
4. Какое базовое имя имеет каждый сервис? Если решение ещё не принято, подтвердить временные пары `IService1`/`Service1`, `IService2`/`Service2` и так далее.
5. Каково назначение и какие операции нужны каждому сервису? Если других требований нет, использовать `SavedText`, `Save` и `Clear`.
6. Какой lifetime нужен каждому сервису? Для состояния в памяти по умолчанию предложить singleton, но не менять явно названный lifetime.
7. Для интеграции: какой точный путь к `.sln` и какой проект является composition root?
8. Для отдельного решения: как оно называется?
9. Нужен только собираемый сервис или запускаемый демонстрационный host?
10. Если нужен host, оставить стандартный Console или создать явно запрошенный WinForms-host?

Если версия .NET, режим, имя solution, DI, количество, имена или контракт уже явно названы пользователем, повторно не спрашивать.

## Проверка результата

Для обоих режимов обязательно проверить:

- целевые framework совпадают с согласованными;
- количество сервисов и их имена совпадают с ответами пользователя;
- каждый публичный интерфейс расположен в `Interface/`, реализация — в `Service/`;
- проект `Common.Service` не зависит от DI-пакета;
- composition root разрешает каждую пару интерфейса и реализации;
- singleton действительно возвращает один экземпляр, если выбран этот lifetime;
- два последовательных `Save` заменяют значение;
- `Save(null)` даёт `string.Empty`;
- `Clear` даёт `string.Empty`;
- NuGet восстанавливается в locked mode;
- Debug и Release собираются без ошибок;
- исходные legacy-проекты не изменены.

## Проверенные эталоны

### DataService.dotnet.App1

- Согласованное имя: `DataService.dotnet.App1`.
- Режим: отдельный solution с Console-host.
- Путь: `Sources/Architectures/Cubes/DotNet/DataService.dotnet.App1/`.
- Runtime: .NET 8.
- DI: `Microsoft.Extensions.DependencyInjection`.
- Проекты: `Common.Service` и `Main`.
- Сервис: историческая пара `IMainService`/`MainService`, сохранённая для прямого сравнения с `DataService.NETFramework.App1`.
- Контракт: `SavedText`, `Save(string? text)`, `Clear`.
- Lifetime: singleton.
- SDK: 8.0.404, закреплённый в `global.json`.
- Проверены locked restore, Debug- и Release-сборки без предупреждений, разрешение одного singleton-экземпляра через DI, два последовательных `Save`, `Save(null)`, `Clear` и успешное завершение Console-host с кодом `0`.

### WinForms.dotnet.App2

- Режим: самостоятельный WinForms solution по архитектуре `WinForms - View - Presenter - DI` с интегрированным кубиком сервиса.
- Путь: `Sources/Architectures/WinForms/DotNet/WinForms.dotnet.App2/`.
- Проекты: `Main`, `Common.View`, `Common.Presenter`, `Common.MessageOperation`, `Common.Service`.
- Сервис: `IMainService`/`MainService`, singleton.
- `MainPresenter` получает сервис через конструктор и делегирует ему `Save` и `Clear`; View не зависит от сервиса.
- Проверены locked restore, Debug- и Release-сборки без предупреждений, DI-граф, события View, singleton, два последовательных `Save`, `Save(null)`, `Clear`, очистка View, логирование и запуск WinForms.
