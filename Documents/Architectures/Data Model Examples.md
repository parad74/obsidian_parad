# Образцы модели — v2

Основной источник — вычитанный Parad код Book4U. Зафиксирована версия `5c1aaced8d286cd7c6c894553621abf598ea98ab`; последующие изменения приложения не меняют этот набор автоматически. Локальная папка: `Sources/Book4U`. Перед копированием сравни файл с этой версией; при расхождении используй сохранённую версию или явно выбранное новое основание, не откатывая рабочий проект.

## Выбор примера

Для конкретной операции прочитай строку ниже и нужный файл. Полный solution исследуется при проверке состава и совместимости; весь набор предметных объектов не требуется для понимания одного приёма.

| Пример фиксированной версии | Что показывает | Граница применения |
| --- | --- | --- |
| [Room](https://github.com/parad74/Book4U/blob/5c1aaced8d286cd7c6c894553621abf598ea98ab/Book4U.Model/Domain/Room/Room.cs) | Единичный объект, явная инициализация, Equals/GetHashCode по Code | Имя Room и поле Count предметные; типы/defaults нового объекта берутся из Excel |
| [Rooms](https://github.com/parad74/Book4U/blob/5c1aaced8d286cd7c6c894553621abf598ea98ab/Book4U.Model/Domain/Room/Rooms.cs) | Отдельная ObservableCollection, FromEnumerable, CurrentItem, CurrentChanged, TotalCount | Коллекция не становится базовым классом единичного объекта |
| [Entity Room](https://github.com/parad74/Book4U/blob/5c1aaced8d286cd7c6c894553621abf598ea98ab/Book4U.Model.Sqlite.CodeFirst.ExportImport/Book4UDb/Room/Room.cs) | Отдельное представление сохраняемых данных | Book4UDb и namespace адаптируются к выбранным именам |
| [RoomConfiguration](https://github.com/parad74/Book4U/blob/5c1aaced8d286cd7c6c894553621abf598ea98ab/Book4U.Model.Sqlite.CodeFirst.ExportImport/Book4UDb/Room/RoomConfiguration.cs) | Fluent-конфигурация и технический PK | Длины, nullable и defaults не копируются на другую модель без её входных данных |
| [RoomMapper](https://github.com/parad74/Book4U/blob/5c1aaced8d286cd7c6c894553621abf598ea98ab/Book4U.Model.Sqlite.CodeFirst.ExportImport/MappingEF/RoomMapper.cs) | Преобразование двух представлений и сохранение ID в ApplyChanges | Заглушка ToSimpleDomainObject означает неопределённый состав; при определённом составе метод реализуется |
| [IRoomRepository](https://github.com/parad74/Book4U/blob/5c1aaced8d286cd7c6c894553621abf598ea98ab/Book4U.Model/Interface/IRoomRepository.cs) | Внешний контракт репозитория | Предметные дополнительные методы задаются конкретной задачей |
| [RoomEFRepository](https://github.com/parad74/Book4U/blob/5c1aaced8d286cd7c6c894553621abf598ea98ab/Book4U.Model.Sqlite.CodeFirst.ExportImport/RepositoryEF/RoomEFRepository.cs) | Реализация типовых операций и SelectParams | Обязательная семантика — в кубике; провайдер и его API выбираются для проекта |
| [Book4UDbContextFactory](https://github.com/parad74/Book4U/blob/5c1aaced8d286cd7c6c894553621abf598ea98ab/Book4U.Model.Sqlite.CodeFirst.ExportImport/Context/Book4UDbContextFactory.cs) | Создание контекста для design-time без изменения БД | Имя БД, провайдер и строка подключения выбираются отдельно |
| [CommandResult](https://github.com/parad74/Book4U/blob/5c1aaced8d286cd7c6c894553621abf598ea98ab/Book4U.Model/Domain/CommandResult/CommandResult.cs) | Более сложный объект и готовый стартовый состав | Локальное сравнение по OperationIndexCode не является общим шаблоном равенства |

## Применение готового состава

Book4U задаёт основной образец реализации. Стартовый состав определяется [[Commands/Create Project Domain Model by Step#Состав solution]], состав новых предметных объектов — [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Гибкий состав работы и согласование модели]]. Полный перенос всех таблиц, предметных объектов, migrations или файла БД Book4U новым запросом на стартовый solution не разрешается. Для SelectParam сохраняется способ включения локального проекта из папки `Service.Model.EF.SelectParam/` фиксированного коммита; его зависимости проверяются вместе с solution.

В сохранённом Book4U `CommandResult.Equals/GetHashCode` используют `OperationIndexCode`. Это локальное решение прочитанного приложения. Для нового DomainObject применяется общий контракт сравнения по Code из карточки Model; при создании нового стартового CommandResult готовый состав адаптируется к этому контракту. Сам Book4U автоматически не переделывается. Методы чтения, удаления и обновления репозитория определяются независимо от Equals по политике кубика.

`Monitor.Model` и прежний ExportImport остаются документированными первыми реализациями. Файлы в `Sources/old` используются адресно, когда нужного примера нет в Book4U, например при запросе сохранённой request/response-пары. Исторический код не становится действующим правилом без проверки контракта.

## Состояние проверки

Parad сообщила, что прочитала код Book4U и выбрала его как основной источник образцов. Solution ранее собран, migrations применены, наличие таблиц подтверждено Parad. Это не означает выполнения всех CRUD-сценариев, всех провайдеров, всех 11 вариантов кубика или готовности ToSimpleDomainObject. В рамках v2 код не изменяется и эти проверки не объявляются выполненными заново.

## Тип 2 — пары request/response

Готовые HTTP request/response-типы находятся вне `Domain` и не входят в цепочку объектов из Excel. Они добавляются только по прямому выбору Parad.

Пара хранится в собственной папке:

```text
<Имя>/
├─ <Имя>Model.cs
└─ <Имя>Result.cs
```

По запросу «найди тип данных для `<назначение>`» Машина показывает прямые и близкие варианты, точные имена классов, полноту пары, зависимости и исходные пути, объясняет различия и ждёт выбора. Ничего не добавляется до выбора. Выбранный исходный код переносится без изменений, кроме namespace по контексту.

Связанные базовые типы не добавляются автоматически вместе с парой. Машина показывает найденные зависимости, а переносит только прямо запрошенные или отдельно выбранные Parad типы.

### Каталог полных пар в историческом примере

| Имя пары | Исходная папка | Связанные типы |
| --- | --- | --- |
| `Login` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/Login` | `LoginResult` наследует `AuthenticationCommandResult` |
| `Register` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/Register` | `RegisterResult` наследует `AuthenticationCommandResult` |
| `Profile` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/Profile` | `ProfileModel` реализует `IProfileModel`; `ProfileResult` наследует `AuthenticationCommandResult` |
| `Delete` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/Delete` | `DeleteResult` наследует `AuthenticationCommandResult` |
| `ChangePassword` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/ChangePassword` | `ChangePasswordResult` содержит поля результата непосредственно |
| `ForgotPassword` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/EmailSender` | `ForgotPasswordResult` наследует `AuthenticationCommandResult` |
| `RoleModification` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/RoleModification` | `RoleModificationResult` наследует `AuthenticationCommandResult` |
| `Role` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/RoleModification` | `RoleModel.cs` также содержит `UserViewModel`; `RoleResult` наследует `AuthenticationCommandResult` |

Общие зависимости результатов: `AuthenticationCommandResult`, `CommandErrorCodeEnum`, `SuccessfulEnum`, `CommandResultCodeEnum` из `Enum/CommandResultEnum.cs`.

Непарные типы участвуют в поиске, но не выдаются за готовую пару:

| Тип | Исходный путь |
| --- | --- |
| `UserWithPasswordModel` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/ChangePassword/UserWithPasswordModel.cs` |
| `ResetPasswordModel` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/EmailSender/ResetPasswordModel.cs` |
| `UserModel` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/User/UserModel.cs` |
| `WebAPISettingsResult` и класс `WebAPISettings` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/WebAPISettings` |

Такой тип добавляется только по прямому выбору Parad после показа его фактического состава и зависимостей.

## Тип 3 — наборы для стандартной функциональности

Точное упоминание распознаётся как просьба показать найденный набор, но само по себе не разрешает добавление файлов.

| Точное упоминание | Псевдоним | Исходная папка | Найденные файлы |
| --- | --- | --- | --- |
| `SignalR` | — | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/SignalR` | `ChatHub.cs`, `CommandHub.cs`, `HubChatSignalRRepository.cs`, `SignalRtcHub.cs`, `HubCommandSignalRRepository.cs` |
| `Claim` | `Claims` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/Claim` | `ClaimConvertItem.cs`, `ClaimsViewModel.cs`, `ClaimItems.cs`, `ClaimItem.cs` |
| `JwtService` | `Jwt` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/Infrastructure` | `JwtService.cs` |
| `ValidationStartupFilter` | `StartupFilter` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/StartupFilter` | `SettingValidationStartupFilter.cs` |
| `Urls` | — | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared` | `Urls.cs` |

Перед переносом содержимое классифицируется по фактическому коду. SignalR hubs и repositories, `JwtService` и `StartupFilter` являются технологической реализацией и по умолчанию не входят в чистую `<Service>.Model`. Для `Claim`, `Urls` и новых кандидатов граница определяется по коду, а не только по имени.
