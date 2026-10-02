---
type: architecture-catalog
---

# Catalog — проекты и архитектурные кубики

Это точка входа для выбора архитектуры по словам Parad. Каталог кратко показывает доступные проекты, кубики и проверенные сочетания; точные правила, обязательные вопросы, ограничения и ссылки на исходный код находятся в указанных карточках. Перед созданием или изменением решения прочитай выбранные карточки полностью.

## Термины для проектов доступа к данным

СУБД или хранилище, семейство доступа к данным, пакет провайдера и подход моделирования — отдельные настройки. `SQLite` и `MSSQL` (SQL Server) — примеры СУБД, а не полный список допустимых вариантов. `EF Core` и `EF6` обозначают разные семейства Entity Framework; технически провайдером EF называется компонент для конкретной пары «семейство EF + СУБД». `CodeFirst` и `DatabaseFirst` описывают подход и выбираются отдельно. Cloud Firestore в историческом примере использует собственный SDK, а не провайдер EF.

| СУБД или хранилище | Семейство доступа | Пакет провайдера или SDK | Сегмент имени проекта и namespace | Состояние |
| --- | --- | --- | --- | --- |
| SQLite | EF Core | `Microsoft.EntityFrameworkCore.Sqlite` | `Sqlite` | Создан первый образец ExportImport. |
| SQL Server | EF Core | `Microsoft.EntityFrameworkCore.SqlServer` | `MSSQL` | Вариант для следующего проекта; в текущих эталонах не собран. При запросе MSSQL без выбора EF по решению Parad предлагается EF Core. |
| SQL Server | EF6 | Провайдер SQL Server из пакета `EntityFramework` | `MSSQL` | Есть исторический проект; новый эталон не создан. |
| Cloud Firestore | Firestore SDK, без EF | `Google.Cloud.Firestore` | `CloudFirestore` | Есть исторический проект; новый эталон не создан. |

Сегмент `Sqlite`, `MSSQL` или `CloudFirestore` в имени проекта и namespace указывает хранилище, а не EF Core, EF6 или имя NuGet-пакета. Например, для SQL Server возможны разные семейства EF при одном сегменте `MSSQL`; совместимость и точные версии пакетов проверяются для конкретного solution. Справка Microsoft: [провайдеры EF Core](https://learn.microsoft.com/en-us/ef/core/dbcontext-configuration/), [провайдеры EF6](https://learn.microsoft.com/en-us/ef/ef6/fundamentals/providers/).

Таблица показывает известные примеры и не ограничивает выбор Parad. Если названа другая СУБД или хранилище, перед созданием ExportImport найди в актуальной документации провайдер именно для запрошенного семейства `EF Core` или `EF6`. Проверь точное имя NuGet-пакета и его версию по документации разработчика провайдера и пакета, совместимость с выбранными версиями EF, .NET и СУБД, а также поддержку нужного подхода и операций со схемой. Покажи Parad найденный вариант и ссылки на источники; только после проверки закрепляй пакет и версию в проекте. Если совместимый провайдер не найден, сообщи об этом и предложи варианты, не подменяя выбранные СУБД или семейство EF без согласования. [Каталог провайдеров EF Core](https://learn.microsoft.com/en-us/ef/core/providers/), [каталог провайдеров EF6](https://learn.microsoft.com/en-us/ef/ef6/fundamentals/providers/).

## Библиотеки и работа с данными

| Как можно попросить | Что выбрать | Точная карточка |
| --- | --- | --- |
| «Нужен `SelectParam`», «добавь фильтры, сортировку и paging для выборки» | Общая библиотека `Service.Model.EF.SelectParam` (`netstandard2.0`); её API использует namespace `Count4U.Model.SelectionParams`. | [[Documents/Architectures/LibProject/netstandard2.0/SelectParam]] |
| «Создай `<Service>.Model`», «добавь `DomainObject`», «нужен интерфейс репозитория в модели» | Библиотека внутренних объектов, коллекций, перечислений и интерфейсов. Первый образец — `Monitor.Model`; он зависит от `SelectParam`. | [[Documents/Architectures/LibProject/netstandard2.0/Monitor.Model]] |
| «Создай `ExportImport` с `CodeFirst` и `Sqlite`», «добавь `Entity`, `DbContext`, `MappingEF`, `RepositoryEF`» | Проект доступа к SQLite и преобразования `Entity` ↔ `DomainObject`. Первый образец — `Monitor.Model.Sqlite.CodeFirst.ExportImport` на `netcoreapp3.1`. При применении уточняются имя проекта и БД. | [[Documents/Architectures/LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport]] |

Кубик [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository]] задаёт гибкий состав создания и дополнения объектов. Состав работы определяется запросом Parad и фактическим состоянием проекта: названные этапы создаются или дополняются, существующие части используются без дублирования. 11 последовательностей кубика — примеры, а не закрытый список команд. По умолчанию после утверждения Excel выполняется DomainObject с парной коллекцией → Entity с конфигурацией и подключением к DbContext → MappingEF → Repository с интерфейсом. Запрос только Entity не запускает остальные этапы. При недостающих зависимостях уточни существующие пути либо расширение состава работы. Правила: [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Гибкий состав работы и согласование модели]]. Команда: [[Commands/Create Data Objects by Step]]. Практическая проверка всех вариантов пока не выполнена.

Порядок зависимостей первого образца: `SelectParam` → `Monitor.Model` → `Monitor.Model.Sqlite.CodeFirst.ExportImport`. Последний проект также содержит прямую ссылку на `SelectParam`. Правила добавления нового `DomainObject` и новых полей Code First находятся в [[Commands/Create Project Domain Model by Step]] и [[Commands/Add Code First Fields by Step]].

Для рабочего приложения проект `Service.Model.EF.SelectParam` копируется с исходным кодом внутрь Git-репозитория приложения и включается в `<Service>.sln`. Не используй `ProjectReference` на внешний checkout `Sources/Architectures` и не подменяй проект пакетом. Локальный `ProjectReference` добавляется каждому проекту, который использует типы `SelectParam`; неиспользующим проектам ссылка не добавляется.

Запрос создать `<Service>.Model.<DataStore>.CodeFirst.ExportImport` создаёт полный стартовый solution `<Service>.sln` из ExportImport, `<Service>.Model` и `Service.Model.EF.SelectParam`. Готовый `CommandResult` включается в Model как DomainObject с коллекцией, перечислениями и интерфейсами, а в ExportImport — как Entity с конфигурацией, `DbSet`, MappingEF и EF-репозиторием. Имя solution задаётся именем сервиса, выбранным в начале; имя БД его не меняет. Гибкий кубик относится к последующим объектам и дополнениям. Тестовые проекты на текущем этапе не создаются: сначала solution собирается и результат сообщается Parad; затем выдаются точные отдельные команды для `InitialCreate` и создания отсутствующей БД, после применения проверяются migration history и ожидаемая схема.

## WinForms и сервисные кубики

| Как можно попросить | Что выбрать | Точная карточка |
| --- | --- | --- |
| «WinForms на .NET Framework 4.6.1», «View–Presenter с Unity и `IModule`» | WinForms-архитектура с `Main`, `Common.View`, `Common.Presenter`, `Common.MessageOperation` и папкой `Lib`. | [[Documents/Architectures/WinForms/DotNetFramework/WinForms - View - Presenter - DIUnity - IModule]] |
| «WinForms на современном .NET», «View–Presenter с DI» | WinForms-архитектура, где View публикует события и не знает о Presenter. Версия .NET и DI-контейнер выбираются перед созданием; проверенные примеры используют .NET 8 и стандартный DI. | [[Documents/Architectures/WinForms/DotNet/WinForms - View - Presenter - DI]] |
| «Добавь сервис через Unity», «создай `Service - DIUnity`» | Кубик `Common.Service` для .NET Framework 4.6.1: интеграция в существующий solution или отдельный Console-пример с Unity. | [[Documents/Architectures/Cubes/DotNetFramework/Service - DIUnity]] |
| «Добавь сервис через DI», «создай `Service - DI`» | Кубик `Common.Service` для современного .NET: интеграция в существующий solution или отдельный Console-пример со стандартным DI. | [[Documents/Architectures/Cubes/DotNet/Service - DI]] |

В WinForms-примерах `Main` содержит точку входа и первую пару View–Presenter; `Common.View` и `Common.Presenter` содержат общие контракты; `Common.MessageOperation` отвечает за логирование. `Common.Service` добавляется по соответствующему кубику, когда нужен отдельный сервис. Подробный указатель по WinForms находится в [[Documents/Architectures/WinForms/WinForms Architecture Catalog]]. Кубик выбирается из того же семейства runtime, что и основная архитектура.

## Существующие эталоны и сочетания

| Сочетание и точная карточка | Solution | Проверенное состояние |
| --- | --- | --- |
| [SelectParam](LibProject/netstandard2.0/SelectParam.md) | [Service.Model.EF.SelectParam.sln](../../Sources/Architectures/LibProject/netstandard2.0/SelectParam/Service.Model.EF.SelectParam.sln) | Отдельная библиотека собрана. |
| [Monitor.Model](LibProject/netstandard2.0/Monitor.Model.md) + SelectParam | [Monitor.Model.sln](../../Sources/Architectures/LibProject/netstandard2.0/Monitor.Model/Monitor.Model.sln) | Оба проекта включены; solution собран. |
| [ExportImport](LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport.md) + Monitor.Model + SelectParam | [Monitor.Model.Sqlite.CodeFirst.ExportImport.sln](../../Sources/Architectures/LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport/Monitor.Model.Sqlite.CodeFirst.ExportImport.sln) | Solution собран. `InitialCreate` ещё не создана; чтение и запись реальной SQLite-БД не проверялись. |
| [WinForms .NET Framework, App1](WinForms/DotNetFramework/WinForms%20-%20View%20-%20Presenter%20-%20DIUnity%20-%20IModule.md) | [WinForms.NETFramework.App1.sln](../../Sources/Architectures/WinForms/DotNetFramework/WinForms.NETFramework.App1/WinForms.NETFramework.App1.sln) | Базовая View–Presenter архитектура, Unity и `IModule`; сборка и сценарий `Save`/`Clear` проверены. |
| [WinForms .NET Framework + Service - DIUnity, App2](WinForms/DotNetFramework/WinForms%20-%20View%20-%20Presenter%20-%20DIUnity%20-%20IModule.md) | [WinForms.NETFramework.App2.sln](../../Sources/Architectures/WinForms/DotNetFramework/WinForms.NETFramework.App2/WinForms.NETFramework.App2.sln) | Интегрирован [кубик сервиса](Cubes/DotNetFramework/Service%20-%20DIUnity.md); проверены Unity, запуск и операции сервиса. |
| [Service - DIUnity](Cubes/DotNetFramework/Service%20-%20DIUnity.md) | [DataService.NETFramework.App1.sln](../../Sources/Architectures/Cubes/DotNetFramework/DataService.NETFramework.App1/DataService.NETFramework.App1.sln) | Отдельный Console-пример .NET Framework 4.6.1 с Unity проверен. |
| [WinForms .NET, App1](WinForms/DotNet/WinForms%20-%20View%20-%20Presenter%20-%20DI.md) | [WinForms.dotnet.App1.sln](../../Sources/Architectures/WinForms/DotNet/WinForms.dotnet.App1/WinForms.dotnet.App1.sln) | Базовая View–Presenter архитектура на .NET 8 со стандартным DI проверена. |
| [WinForms .NET + Service - DI, App2](WinForms/DotNet/WinForms%20-%20View%20-%20Presenter%20-%20DI.md) | [WinForms.dotnet.App2.sln](../../Sources/Architectures/WinForms/DotNet/WinForms.dotnet.App2/WinForms.dotnet.App2.sln) | Интегрирован [кубик сервиса](Cubes/DotNet/Service%20-%20DI.md); DI, запуск, сервис и View–Presenter проверены. |
| [Service - DI](Cubes/DotNet/Service%20-%20DI.md) | [DataService.dotnet.App1.sln](../../Sources/Architectures/Cubes/DotNet/DataService.dotnet.App1/DataService.dotnet.App1.sln) | Отдельный Console-пример .NET 8 со стандартным DI проверен. |

## Как составить новый запрос или решение

1. Назови цель: библиотека данных, доступ к БД, WinForms-приложение или отдельный сервис. Достаточно слов из таблиц выше; имя проекта, solution и БД добавь, если они уже выбраны.
2. Выбери основную карточку и семейство runtime. Для доступа к данным отдельно назови СУБД, семейство EF или SDK, подход и пакет провайдера с версией, если они уже известны. Для сервиса укажи режим: встроить в существующий solution или создать отдельный пример. Если нужен сервис в WinForms, добавь кубик того же runtime.
3. Машина читает точные карточки и целевой solution, проверяет совместимость проектов и спрашивает только решения, которых нет в запросе и карточках. После этого показывает состав и порядок создания, затем реализует и проверяет результат.
4. Новое проверенное сочетание существующих карточек получает строку в разделе «Существующие эталоны и сочетания». Если появились новые правила или самостоятельный компонент, сначала создаётся точная архитектурная карточка, затем ссылка на неё в этом каталоге.

## Если нужного элемента пока нет

Здесь пока нет согласованных карточек для Database First и новых эталонов ExportImport с хранилищами, отличными от SQLite. Не считай их вариантами уже проверенного ExportImport. Если запрос не покрыт каталогом, Машина называет отсутствующий элемент, изучает применимые карточки и реальный solution, предлагает совместимое решение на основе актуальных рекомендаций .NET и объясняет, как оно сохранит согласованные имена, структуру проектов и стиль кода. Однозначную часть запроса выполняет сразу; недостающие архитектурные решения согласует с Parad. После создания и проверки добавляет новую карточку или сочетание в каталог.

## Текущий подход и семейство EF

Текущий процесс — Code First; существующая БД или Entity-модель может служить входом для Excel, затем после утверждения модели применяется обычный процесс. EF6 или EF Core и совместимые версии определяются для конкретного проекта; API и провайдер подбираются соответственно. Правила: [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Code First и выбор семейства EF]].
