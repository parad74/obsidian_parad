---
type: architecture
runtime_family: netcoreapp
target_framework: netcoreapp3.1
project: Monitor.Model.Sqlite.CodeFirst.ExportImport
---

# Monitor.Model.Sqlite.CodeFirst.ExportImport

## Назначение

Первый образец EF Core-проекта для отображения `Monitor.Model` на SQLite и обратного преобразования данных. Источник для разбора — [исторический проект](../../../../Sources/old/WebAPI.Monitor/src/Monitor.Model.Sqlite.CodeFirst.ExportImport/Monitor.Model.Sqlite.CodeFirst.ExportImport.csproj). Для нового применения имя сервиса `<Service>` берётся из существующего Model или запрашивается до создания и задаёт префикс проектов, namespaces и имя нового solution. Контекст называется `<ИмяБД>Context` по выбранному логическому имени БД: `WarehouseDb` → `WarehouseDbContext`. Имя файла и расширение не входят в имя контекста.

Перед новым применением используй [[Wiki/HowToDo/Create Project Domain Model by Step#Параметры по умолчанию]]. Технические параметры первого профиля ниже описывают его фактическое состояние.

`Sqlite` в имени проекта и namespace обозначает СУБД. Оно не обозначает EF Core: тот же принцип имён для SQL Server использует сегмент `MSSQL` независимо от выбора EF Core или EF6. Подробная таблица терминов и ещё не созданных вариантов находится в [[Documents/Architectures/Catalog]].

## Зависимости

- Обязательные независимые `ProjectReference` на Model и SelectParam показаны в [[Documents/Architectures/Data Model Harness#Модули и устойчивые границы]]. Локальное включение SelectParam — по [[Documents/Architectures/LibProject/netstandard2.0/SelectParam#Перенос в рабочее приложение]].
- Первый образец хранится в Monitor.Model.Sqlite.CodeFirst.ExportImport.sln; новый или интегрируемый состав — по [[Commands/Create Project Domain Model by Step#Состав solution]].
- Текущий готовый образец использует Microsoft.EntityFrameworkCore.Sqlite 3.1.9 и Microsoft.Extensions.Logging 3.1.9. EF Core Design/Tools в его .csproj отсутствуют; подготовка нового применения описана в [[Commands/Create Project Domain Model by Step#Сборка, migrations и создание БД]]. SQL Server, Unity и старые Prism DLL не добавляются только потому, что они были в старом проекте.
- BaseEFRepository.cs остаётся с кодом EF6 и пометкой NOT USE; ссылка на интерфейс переводится на Monitor.Model.Interface. EF6 доступен через SelectParam.

## Стартовый комплект нового solution

Состав и его границы задаёт [[Commands/Create Project Domain Model by Step#Состав solution]]. Для примеров реализации используется [[Documents/Architectures/Data Model Examples]].

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

Шесть корневых файлов и показанная выше структура описывают первый Monitor-образец. ConnectionSqliteMonitorDB реализует Monitor.Model.Interface.IConnectionSqliteMonitorDB; историческая строка подключения — Data Source=command.db. Для нового применения имена и подключение задаёт [[Wiki/HowToDo/Create Project Domain Model by Step#Параметры по умолчанию]]. Согласованное подключение хранится простым строковым литералом в классе подключения. Пространство имён едино во всём EF-проекте и не зависит от вложенных папок.

Фактический MonitorDbContext соответствует описанному ниже шаблону контекста и содержит DbSet<CommandResult> CommandResultDatas.

Поведение DbInitializer и граница работы с существующей БД заданы ниже в разделе «Источник модели и migrations».

`Entity` и конфигурация создаются из `Monitor.Model/Domain/CommandResult` и исторических ограничений столбцов. Состав свойств Domain Model и Entity одинаков. Первичный ключ таблицы — `ID` с генерацией Identity, как в старом Entity. `Code` в Domain Model служит логическим ключом сравнения объектов, но не первичным или уникальным ключом таблицы. `Code` и `CommandResultCode` — независимые значения и два обычных текстовых столбца максимальной длины 50. `IturCodes` и `DocumentHeaderCodes` удалены из обоих классов; `Files` и `UnsureFiles` представлены обычными строками и столбцами максимальной длины 500. Маппер преобразует все свойства между `Entity` и `Monitor.Model.CommandResult`. Исключённый из Domain Model `AdapterType` не переносится. Репозиторий реализует `Monitor.Model.Interface.ICommandResultRepository` на EF Core. `GetTestDataCommandResults` возвращает пример данных в памяти и не записывает его в БД.

Контракт нового DomainObject задаёт [[Documents/Architectures/LibProject/netstandard2.0/Monitor.Model#Контракт новых DomainObject]], состав этапа Entity — [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Entity]].

Для выбора состава работы используй [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Гибкий состав работы и согласование модели]].

Порядок дополнения, утверждения Excel и ограничения изменений существующих полей: [[Commands/Add Code First Fields by Step]].

Четыре метода маппера, обработка NoEntity, сохранение ID и явное применение CutLength определены в [[Commands/Add Code First Fields by Step#Обязательный шаблон MappingEF]]. В первом Monitor-образце ToSimpleDomainObject имеет заглушку; общий CutLength находится в MappingEF/StringLength.cs. Namespace первого EF-проекта — Monitor.Sqlite.CodeFirst.

Для создания и дополнения Repository используй [[Commands/Add Code First Fields by Step#Обязательный шаблон RepositoryEF]]; семантика операций задаётся [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Предметные правила и развитие шаблона]].

`PaginatedList<T>` перенесён из исторической папки в один общий файл RepositoryEF/PaginatedList.cs с namespace EF-проекта. Использование этого вспомогательного файла определяется [[Commands/Add Code First Fields by Step#Обязательный шаблон RepositoryEF]].

## Текущее состояние

Шесть корневых файлов перенесены в `Sources/Architectures/LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport`. Их namespace — `Monitor.Sqlite.CodeFirst`; обращения к интерфейсу приведены к `Monitor.Model.Interface`. Создан `.csproj` с обоими `ProjectReference` и версиями SQLite/Logging из старого проекта. Выбранный solution содержит три проекта. Добавлены `MonitorDbContext`, `DbInitializer`, Entity, Fluent API-конфигурация, полный шаблон маппера, общий `CutLength` и репозиторий. Папка репозитория переименована в `RepositoryEF`; добавлен один общий `PaginatedList<T>` и методы по `Code`. Domain Model и Entity содержат по 74 совпадающих по имени свойства. Solution собирается без предупреждений и ошибок. Migration `InitialCreate` пока не создана; проверка работы с реальной SQLite-БД остаётся следующим отдельным шагом.

## Проверка

Проверь ссылки, namespaces, маппинг и применение SelectParam к фактическому профилю. Порядок сборки, подготовки design-time и отдельных действий с migrations: [[Commands/Create Project Domain Model by Step#Сборка, migrations и создание БД]]. Проверка нового сочетания не следует автоматически из сборки первого профиля.

## Связанные материалы

- [[Tasks/Items/dotnet_architecture_examples/TASK-20260909-003-design-selectparam-guided-workflow]]
- [[Documents/Architectures/Data Model Harness]]
- [[Documents/Architectures/LibProject/netstandard2.0/Monitor.Model]]

## Согласованные правила развития и вычитки

При изменении контрактов и реализации используй [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Предметные правила и развитие шаблона]]. При передаче результата — [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Показ кода и отметки вычитки]].

## Согласованная граница с EF

Путь чтения:

```text
СУБД → EF / Entity → MappingEF → DomainObject → верхние слои
```

Путь записи:

```text
DomainObject → MappingEF → Entity → СУБД
```

`Entity`, `DbContext`, tracking state и provider-specific типы не выходят из EF-проекта. `SelectParam` применяется к `IQueryable<Entity>` до материализации. `TotalCount` вычисляется после фильтрации и до paging, затем возвращается в парной коллекции DomainObject.

Маппер знает обе стороны и находится в конкретной EF-реализации. `<Service>.Model` не содержит Entity, DbContext, migrations или provider-specific код.

## Первый шаг создания EF-проекта

Начальные параметры и имена определяются по [[Wiki/HowToDo/Create Project Domain Model by Step#Параметры по умолчанию]], состав проектов — по [[Commands/Create Project Domain Model by Step#Состав solution]].

Для базы создаётся папка `<ИмяБД>`, внутри неё — папка каждого Entity. Во всём EF-проекте используется namespace `<Service>.<DataStore>.<Approach>`; имена папок не становятся его частями.

Состав свойств стартового Entity соответствует свойствам парного DomainObject без `[NoEntity]` по [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Attributes и NoEntity]]. Первое свойство каждого нового Entity — `long ID`, назначенное первичным ключом таблицы. Парная коллекция `<Имя>s` остаётся в Model и в EF-проект не копируется.

## Шаблон конфигурации Entity для EF Core

Для каждого Entity создаётся один `<Имя>Configuration.cs` с `IEntityTypeConfiguration<<Имя>>`. Entity не содержит Data Annotations схемы БД. Таблица, первичный ключ, генерация значения и свойства столбцов задаются Fluent API в единственной конфигурации типа.

`ID` назначается первичным ключом через `builder.HasKey(p => p.ID)`. Для стартового SQLite-профиля значение генерируется при добавлении. DbContext подключает конфигурации через `ApplyConfigurationsFromAssembly(typeof(<ИмяБД>Context).Assembly)`.

Для EF6 используется соответствующий API `EntityTypeConfiguration<T>` и `DbModelBuilder`; API EF Core механически в EF6 не переносится.

## Шаблон Context для EF Core

Контекст хранится в `Context/<ИмяБД>Context.cs`, получает `DbContextOptions<<ИмяБД>Context>` через конструктор и не содержит `OnConfiguring`.

Для каждого Entity добавляется `DbSet<<ИмяEntity>> <ИмяEntity>Datas`. Суффикс `Datas` отличает DbSet от парной коллекции DomainObject `<Имя>s`. `OnModelCreating` только подключает конфигурации текущей assembly.

Connection string, migrations, создание БД и seed data в DbContext не помещаются. Первоначальной инициализацией отсутствующей БД занимается `Context/DbInitializer.cs`.

## Источник модели и migrations

Источники модели и границы Code First: [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Code First и выбор семейства EF]]. Утверждение и состав изменений: [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Гибкий состав работы и согласование модели]].

Создание и применение migrations выполняются по [[Commands/Create Project Domain Model by Step#Сборка, migrations и создание БД]].

DbInitializer проверяет путь SQLite из строки подключения контекста. Для отсутствующего файла БД он применяет только заранее подготовленные migrations; при отсутствии проверенной InitialCreate выдаёт ошибку. Для существующего файла pending migrations автоматически не применяются. EnsureCreated и автоматическое создание migration не используются. Этот runtime-механизм не заменяет отдельное решение о создании и применении migrations.
