---
type: architecture
runtime_family: netcoreapp
target_framework: netcoreapp3.1
project: Monitor.Model.Sqlite.CodeFirst.ExportImport
---

# Monitor.Model.Sqlite.CodeFirst.ExportImport

## Назначение

Первый образец EF Core-проекта для отображения `Monitor.Model` на SQLite и обратного преобразования данных. Источник для разбора — [исторический проект](../../../../Sources/old/WebAPI.Monitor/src/Monitor.Model.Sqlite.CodeFirst.ExportImport/Monitor.Model.Sqlite.CodeFirst.ExportImport.csproj). Для нового применения имя сервиса `<Service>` берётся из существующего Model или запрашивается до создания и задаёт префикс проектов, namespaces и имя нового solution. Контекст называется `<ИмяБД>Context` по выбранному логическому имени БД: `WarehouseDb` → `WarehouseDbContext`. Имя файла и расширение не входят в имя контекста.

Первый профиль предлагает значения для начальных вопросов: проект `<Service>.Model.Sqlite.CodeFirst.ExportImport`, namespace `<Service>.Sqlite.CodeFirst`, Code First, SQLite, `netcoreapp3.1` и EF Core с `Microsoft.EntityFrameworkCore.Sqlite` 3.1.9. Все необходимые незаданные параметры спрашиваются до создания по [[Wiki/HowToDo/Create Project Domain Model by Step#Параметры по умолчанию]]: предложенный вариант и редактируемое поле для своего значения. До создания solution/проектов сначала задаётся вопрос о СУБД со списком для выбора и свободным вводом; после ответа — отдельный вопрос о провайдере со списком совместимых вариантов, семейством EF, пакетом и версией. Оба выбора должны быть получены до создания по [[Wiki/HowToDo/Create Project Domain Model by Step#Порядок вопросов перед созданием]]. Уже существующие и согласованные параметры используются без повторных вопросов. При интеграции выбранные настройки проверяются на совместимость; при конфликте Машина спрашивает Parad, версии автоматически не меняются.

`Sqlite` в имени проекта и namespace обозначает СУБД. Оно не обозначает EF Core: тот же принцип имён для SQL Server использует сегмент `MSSQL` независимо от выбора EF Core или EF6. Подробная таблица терминов и ещё не созданных вариантов находится в [[Documents/Architectures/Catalog]].

## Зависимости

- Обязательные независимые `ProjectReference` на [Monitor.Model](../netstandard2.0/Monitor.Model.md) и [SelectParam](../netstandard2.0/SelectParam.md).
- В рабочем репозитории приложения `Service.Model.EF.SelectParam` копируется как локальный проект с исходным кодом и включается в `<Service>.sln`. ExportImport получает `ProjectReference` на эту локальную копию, поскольку использует типы `SelectParam`. Ссылку на внешний checkout `Sources/Architectures` не создавай; если локальный проект уже существует, не дублируй его.
- Текущий первый образец хранится в `Monitor.Model.Sqlite.CodeFirst.ExportImport.sln` и включает ExportImport, `Monitor.Model` и `SelectParam`. Для нового автономного применения solution называется по выбранному в начале имени сервиса: `<Service>.sln`, например `Inventory.sln`. Имя БД и имя ExportImport-проекта это имя не меняют. При интеграции используй указанный существующий solution. Для запроса ExportImport базовый состав включает три проекта: отсутствующие зависимости создаются или подключаются в рамках запроса. Общего запрета включать другие необходимые проекты в solution нет.
- Текущий готовый образец по умолчанию использует `Microsoft.EntityFrameworkCore.Sqlite` 3.1.9 и `Microsoft.Extensions.Logging` 3.1.9. EF Core Design/Tools отсутствуют в его текущем `.csproj` и добавляются только при необходимости соответствующего отдельного шага с проверкой совместимости. SQL Server, Unity и старые Prism DLL не добавляются только потому, что они были в старом проекте.
- `BaseEFRepository.cs` остаётся с кодом EF6 и пометкой `NOT USE`; ссылка на интерфейс переводится на `Monitor.Model.Interface`. EF6 доступен через `SelectParam`.

## Стартовый комплект нового solution

Запрос создать `<Service>.Model.<DataStore>.CodeFirst.ExportImport` означает создание готового стартового solution из трёх связанных проектов: ExportImport, `<Service>.Model` и `Service.Model.EF.SelectParam`. В Model включаются готовые DomainObject `CommandResult`, `CommandResults`, необходимые перечисления и все пять интерфейсов, включая интерфейс репозитория. В ExportImport для `CommandResult` включаются Entity, Fluent-конфигурация, `DbSet` в `<ИмяБД>Context`, MappingEF и EF-репозиторий.

Этот состав создаётся как единый стартовый комплект без повторного согласования готового `CommandResult`. Гибкий кубик применяется к последующим новым объектам и дополнениям. Тестовые проекты и автоматизированные тесты на текущем этапе в solution не добавляются.

Единичный DomainObject и Entity объявляются обычными классами без автоматически добавленного IEquatable; парная коллекция — отдельный ObservableCollection. Контракты использования и различие равенства по Code и идентичности записи: [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Единичный объект и коллекция]].

## Структура первого образца

```text
Monitor.Model.Sqlite.CodeFirst.ExportImport/
├─ Context/
│  ├─ MonitorDbContext.cs
│  └─ DbInitializer.cs
├─ MonitorDb/CommandResult/
│  ├─ CommandResult.cs
│  └─ CommandResultConfiguration.cs
├─ MappingEF/
│  ├─ CommandResultMapper.cs
│  └─ StringLength.cs
├─ RepositoryEF/
│  ├─ CommandResultEFRepository.cs
│  └─ PaginatedList.cs
├─ BaseEFDbSetRepository.cs
├─ BaseEFRepository.cs
├─ CollectionOf.cs
├─ CollectionPagingOf.cs
├─ ConnectionSqliteMonitorDB.cs
├─ DomainObjects.cs
└─ Monitor.Model.Sqlite.CodeFirst.ExportImport.csproj
```

Шесть корневых файлов берутся из исторического проекта. `ConnectionSqliteMonitorDB` реализует `Monitor.Model.Interface.IConnectionSqliteMonitorDB`. Первый образец сохраняет строку `Data Source=command.db`; его логическое имя БД `MonitorDb` и файл SQLite — разные значения. Для нового применения логическое имя БД и имя/расположение файла определяются отдельно до создания по [[Wiki/HowToDo/Create Project Domain Model by Step#Параметры по умолчанию]]. Имя файла вводится без расширения, например `monitor`; расширение зависит от СУБД, для текущего SQLite-профиля — `.db`. Для SQLite расположение выбирается через вопрос с примерами строки подключения: только имя файла (относительно рабочей папки программы) или полный путь, по [[Wiki/HowToDo/Create Project Domain Model by Step#Строка подключения SQLite]]. `command.db` автоматически не переносится. Согласованное подключение хранится простым строковым литералом в классе подключения. Все файлы первого образца используют namespace `Monitor.Sqlite.CodeFirst`, включая вложенные папки.

`MonitorDbContext` получает `DbContextOptions<MonitorDbContext>` через конструктор, объявляет `DbSet<CommandResult> CommandResultDatas` и подключает Fluent API-конфигурации через `ApplyConfigurationsFromAssembly`. В нём нет `OnConfiguring`, строки подключения, создания БД и начальных данных.

`DbInitializer` проверяет путь SQLite из строки подключения контекста. Для отсутствующего файла БД он применяет только заранее подготовленные migrations; при отсутствии `InitialCreate` выдаёт ошибку. Для существующего файла pending migrations автоматически не применяются. `EnsureCreated()` и автоматическое создание migration не используются.

`Entity` и конфигурация создаются из `Monitor.Model/Domain/CommandResult` и исторических ограничений столбцов. Состав свойств Domain Model и Entity одинаков. Первичный ключ таблицы — `ID` с генерацией Identity, как в старом Entity. `Code` в Domain Model служит логическим ключом сравнения объектов, но не первичным или уникальным ключом таблицы. `Code` и `CommandResultCode` — независимые значения и два обычных текстовых столбца максимальной длины 50. `IturCodes` и `DocumentHeaderCodes` удалены из обоих классов; `Files` и `UnsureFiles` представлены обычными строками и столбцами максимальной длины 500. Маппер преобразует все свойства между `Entity` и `Monitor.Model.CommandResult`. Исключённый из Domain Model `AdapterType` не переносится. Репозиторий реализует `Monitor.Model.Interface.ICommandResultRepository` на EF Core. `GetTestDataCommandResults` возвращает пример данных в памяти и не записывает его в БД.

Для каждой новой пары `DomainObject` ↔ `Entity` первое свойство обоих классов — обязательное `long ID`. Если во входном описании его нет, оно добавляется автоматически, без отдельного вопроса; уже указанное корректное `ID long` не дублируется. В EF-конфигурации `ID` явно назначается первичным ключом (`builder.HasKey(p => p.ID)`); методы типового репозитория по `ID` используют `long`. `Code` сохраняет роль логического ключа сравнения.

Состав работы определяется запросом Parad и фактическим состоянием проекта: названные части создаются или дополняются, существующие части используются без дублирования. 11 последовательностей кубика — примеры, а не закрытый список команд. Сначала Машина готовит Excel и ждёт его проверки и возврата Parad. Затем весь запрошенный комплект классов создаётся одним проходом: по умолчанию в Model и ExportImport, а при явно ограниченном запросе — только в названном проекте или составе. Отдельные подтверждения каждого класса, объекта или этапа после утверждения Excel не требуются. При недостающих зависимостях пути или расширение состава уточняются до генерации. Правила: [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Гибкий состав работы и согласование модели]].

Дополнение существующих объектов определяется запросом и найденным кодом. Используй существующие классы; не создавай пару заново и не запускай не запрошенные части автоматически. При запросе синхронизации поля одним проходом дополни все входящие в запрос Entity, DomainObject, конфигурации и мапперы. Если отсутствует необходимая часть, уточни её путь либо создание до генерации. После возвращения утверждённого Excel отдельные подтверждения по объектам и этапам не требуются. Существующие поля автоматически не удаляются и не переделываются; migrations остаются отдельными запрошенными действиями.

На выбранном этапе MappingEF для пары `Entity` ↔ `DomainObject` создаётся отдельный `<Имя>Mapper.cs` с методами `ToDomainObject`, `ToSimpleDomainObject`, `ToEntity` и `ApplyChanges`. В первом образце ToSimpleDomainObject пока имеет заглушку. В новом применении метод даёт сокращённое представление по составу проекта; если состав определён, предложи реализацию. Свойства DomainObject с `[NoEntity]` не добавляются в Entity, конфигурацию и ни в один метод маппера по [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Attributes и NoEntity]]; ApplyChanges сохраняет ID существующей Entity, а ToEntity переносит ID отдельно в новый объект; обновление репозитория адресует запись по Code. Старый `CutLength` вынесен в общий файл `MappingEF/StringLength.cs` и вызывается для поля только по явному правилу, без автоматической обрезки всех строк с `HasMaxLength`. Все файлы используют namespace `Monitor.Sqlite.CodeFirst`.

На выбранном этапе Repository создаются `I<Имя>Repository` в `Monitor.Model/Interface` и `<Имя>EFRepository` в папке `RepositoryEF` проекта EF. Типовой набор реализует чтение всех записей и выборку с `SelectParams`, чтение по Code, вставку одной и нескольких записей, обновление по ID или Code, удаление всех совпадений по Code, а также DeleteAll. При повторяющемся Code чтение и обновление по Code выбирают запись с минимальным техническим ID, удаление по Code удаляет все совпадения. UpdateById выбирает запись только по ID и обновляет все её данные, включая Code; проверка совпадения Code не нужна. Оба способа обновления сохраняют ID Entity, вставка допускает повторный Code. Чтение/удаление по ID и методы по специфичным полям сохранены в готовом образце для совместимости и не входят в типовой набор новых объектов; UpdateById входит в типовой набор наряду с UpdateByCode. Полная политика — [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Предметные правила и развитие шаблона]]. Методы по другим полям и тестовым данным добавляются только по запросу. Если поведение дополнительного метода из файла достаточно описано, предложи реализацию; неизвестное поведение оставь явно обозначенной заглушкой.

`PaginatedList<T>` перенесён из исторической папки в один общий файл `RepositoryEF/PaginatedList.cs` с namespace EF-проекта. Он остаётся примером и не меняет выборку через `SelectParams` и `CommandResults.TotalCount`. Метод Delete(string code) и явно названный DeleteByCode(string code) удаляют все совпадения по Code. Прежнее использование CommandResultCode в строковой перегрузке заменено текущим решением Parad; это отдельное свойство данных, не ключ удаления.

## Текущее состояние

Шесть корневых файлов перенесены в `Sources/Architectures/LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport`. Их namespace — `Monitor.Sqlite.CodeFirst`; обращения к интерфейсу приведены к `Monitor.Model.Interface`. Создан `.csproj` с обоими `ProjectReference` и версиями SQLite/Logging из старого проекта. Выбранный solution содержит три проекта. Добавлены `MonitorDbContext`, `DbInitializer`, Entity, Fluent API-конфигурация, полный шаблон маппера, общий `CutLength` и репозиторий. Папка репозитория переименована в `RepositoryEF`; добавлен один общий `PaginatedList<T>` и методы по `Code`. Domain Model и Entity содержат по 74 совпадающих по имени свойства. Solution собирается без предупреждений и ошибок. Migration `InitialCreate` пока не создана; проверка работы с реальной SQLite-БД остаётся следующим отдельным шагом.

## Проверка

После создания собрать целевой solution и проверить ссылки, namespaces, маппинг `Code`, фильтрацию и paging через `SelectParam`. Успешную сборку явно сообщить Parad; автоматизированные тесты на этом этапе не требуются.

Перед созданием migration проверить design-time готовность выбранного профиля: доступность инструмента, Design-пакета и способ создания `DbContext`. При создании solution необходимая design-time factory добавляется без отдельного согласования с уже выбранными провайдером и строкой подключения; существующий рабочий способ создания контекста не дублируется. После добавления проверить сборку и создание контекста без изменения БД. Добавление ещё не разрешённых зависимостей согласуется отдельно. Полное правило: [[Commands/Create Project Domain Model by Step#Сборка, migrations и создание БД]]. После успешной сборки выдать две точные команды с фактическими путями, project, startup project и контекстом: отдельно создать `InitialCreate`, затем применить migrations для создания отсутствующей БД. По умолчанию команды запускает Parad; Машина может выполнить каждую из них по отдельному явному запросу.

Существующую БД автоматически не обновлять. После применения `InitialCreate` к отсутствующей БД проверить, что файл или экземпляр БД создан, migration зарегистрирована в истории и ожидаемая схема присутствует, затем сообщить результат. Исторические файлы остаются без изменений.

## Связанные материалы

- [[Tasks/Items/dotnet_architecture_examples/TASK-20260909-003-design-selectparam-guided-workflow]]
- [[Tasks/Artifacts/TASK-20260909-003/project-structure-discussion-v1]]
- [[Documents/Architectures/LibProject/netstandard2.0/Monitor.Model]]

## Согласованные правила развития и вычитки

Таблицы этой архитектуры независимы. Повторы Code допустимы. Удаление по Code удаляет все совпадения; чтение и обновление по Code выбирают запись с минимальным техническим ID. Обновление по ID выбирает запись только по ID и переносит данные, включая Code, без проверки совпадения кодов. При обоих способах обновления ID записи в БД сохраняется. Политика не требует повторного согласования для каждого проекта. Равенство состава DomainObject/Entity относится к стартовому шаблону с исключением свойств DomainObject, помеченных `[NoEntity]`; последующие бизнес-различия описываются и отображаются явно. Достаточно описанные дополнительные методы реализуются, неизвестное поведение оставляется явно обозначенной заглушкой. Подробности: [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Предметные правила и развитие шаблона]].

После создания согласованного комплекта показывай итоговые файлы/классы целиком для вычитки. Отметки CodeReview добавляй только по явной просьбе Parad для текущих изменений или дополнений («при изменениях пометь как TODO», «при дополнениях пометь как TODO» или равнозначная формулировка). По умолчанию, включая первую генерацию, создание, миграции и добавление данных, комментарии вычитки не добавляются. Условия включения и формат: [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Показ кода и отметки вычитки]].
