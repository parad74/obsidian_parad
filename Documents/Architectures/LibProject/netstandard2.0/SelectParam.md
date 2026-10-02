---
type: architecture
runtime_family: netstandard
target_framework: netstandard2.0
project: Service.Model.EF.SelectParam
---

# SelectParam

## Назначение

Общая библиотека параметров выборки: фильтры, сортировка и paging для `IQueryable<T>`. Имя проекта и сборки — `Service.Model.EF.SelectParam`, namespace исходного API — `Count4U.Model.SelectionParams`. Проект сохранён из [исторического источника](../../../../Sources/old/WebAPI.Monitor/src/Service.Model.EF.SelectParam/Service.Model.EF.SelectParam.csproj) без переименования публичных типов.

## Исходный код и зависимости

- [Проект](../../../../Sources/Architectures/LibProject/netstandard2.0/SelectParam/Service.Model.EF.SelectParam.csproj) и [самостоятельный solution](../../../../Sources/Architectures/LibProject/netstandard2.0/SelectParam/Service.Model.EF.SelectParam.sln).
- [SelectParams](../../../../Sources/Architectures/LibProject/netstandard2.0/SelectParam/SelectionParams/SelectParams.cs) реализует [ISelectParams](../../../../Sources/Architectures/LibProject/netstandard2.0/SelectParam/SelectionParams/ISelectParams.cs); связанные типы фильтров находятся в той же папке `SelectionParams`.
- Целевая платформа — `netstandard2.0`; прямые зависимости проекта — `EntityFramework` 6.4.0 и `Microsoft.Windows.Compatibility` 3.1.1.

## Перенос в рабочее приложение

`Service.Model.EF.SelectParam` копируется в рабочий Git-репозиторий приложения как отдельный проект с исходным кодом и включается в `<Service>.sln`. Источник — `Sources/Architectures/LibProject/netstandard2.0/SelectParam/`; копируются `Service.Model.EF.SelectParam.csproj` и исходники, но не отдельный эталонный `.sln`, `bin`, `obj` и Git-метаданные. Проект не подключается относительной ссылкой на checkout `Sources/Architectures` и не заменяется NuGet-пакетом. Если локальный `Service.Model.EF.SelectParam` уже существует, используется он без создания второй копии.

Каждый проект solution, который использует `SelectParams` или другие типы этой библиотеки, получает `ProjectReference` на локальный `Service.Model.EF.SelectParam.csproj`. Проектам без такого использования ссылка не добавляется. В стартовом ExportImport solution ссылка нужна как минимум `<Service>.Model` для интерфейсов репозитория и EF-проекту для реализации фильтрации, сортировки и paging.

## Где используется в текущих образцах

| Проект | Ссылка и использование |
| --- | --- |
| [Monitor.Model](Monitor.Model.md) | [ProjectReference](../../../../Sources/Architectures/LibProject/netstandard2.0/Monitor.Model/Monitor.Model.csproj) на `SelectParam`; [ICommandResultRepository](../../../../Sources/Architectures/LibProject/netstandard2.0/Monitor.Model/Interface/ICommandResultRepository.cs) принимает `SelectParams` в методе выборки. `SelectParam` также включён в [Monitor.Model.sln](../../../../Sources/Architectures/LibProject/netstandard2.0/Monitor.Model/Monitor.Model.sln). |
| [Monitor.Model.Sqlite.CodeFirst.ExportImport](../netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport.md) | Прямой [ProjectReference](../../../../Sources/Architectures/LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport/Monitor.Model.Sqlite.CodeFirst.ExportImport.csproj); [BaseEFDbSetRepository](../../../../Sources/Architectures/LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport/BaseEFDbSetRepository.cs) применяет фильтры, сортировку и paging, а [CommandResultEFRepository](../../../../Sources/Architectures/LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport/RepositoryEF/CommandResultEFRepository.cs) возвращает результат с `TotalCount` до paging. `SelectParam` включён в [solution ExportImport](../../../../Sources/Architectures/LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport/Monitor.Model.Sqlite.CodeFirst.ExportImport.sln). |

## Связанные материалы

- [[Tasks/Items/dotnet_architecture_examples/TASK-20260909-001-preserve-selectparam-library]]
- [[Tasks/Items/dotnet_architecture_examples/TASK-20260909-003-design-selectparam-guided-workflow]]
