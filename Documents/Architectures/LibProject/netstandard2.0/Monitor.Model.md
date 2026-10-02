---
type: architecture
runtime_family: netstandard
target_framework: netstandard2.0
project: Monitor.Model
---

# Monitor.Model

## Назначение

Эталон библиотеки внутренних данных приложения. Для другого сервиса имя проекта и корневой namespace имеют вид `<Service>.Model`. Первый пример — `Monitor.Model` на `netstandard2.0`.

Библиотека содержит `DomainObject`, коллекции, необходимые им перечисления и интерфейсы доступа к данным. Реализации репозиториев, `Entity`, `DbContext`, EF-конфигурации, migrations и провайдеры СУБД находятся в других проектах.

По шаблону каждого нового `DomainObject` первое объявленное свойство — обязательное `public long ID { get; set; }`, даже если во входном описании его нет. Корректный `ID long` из источника не дублируется. В конструкторе явно устанавливается `ID = 0`. В парном `Entity` `long ID` также объявляется первым и служит первичным ключом БД; его EF-конфигурация находится в проекте доступа к данным. `Code` остаётся отдельным логическим ключом для `Equals` и `GetHashCode`.

## Состав первого образца

`CommandResult` и `CommandResults` — готовый образец стиля кода для Машины при генерации нового класса и для программиста. При повторном использовании в другом сервисе бери текущую адаптацию из `Sources/Architectures/LibProject/netstandard2.0/Monitor.Model/` с её необходимыми перечислениями. Повторное согласование полей, перечислений и исторической адаптации не требуется, если Parad отдельно не запросила изменение образца. При включении в рабочий проект приводи namespaces и ссылки на типы к текущему `<Service>`; имена классов и остальной готовый состав сохраняй.

Образец задаёт стиль, а не предметный состав всех будущих моделей. Поля нового DomainObject определяются его входными данными и общим шаблоном и согласуются в Excel. После возврата утверждённой книги отдельное подтверждение кода каждого класса не требуется. Сам существующий эталон для нового сервиса не переименовывается — адаптируется его копия в целевом проекте.

```text
Monitor.Model/
├─ Domain/CommandResult/
│  ├─ CommandResult.cs
│  └─ CommandResults.cs
├─ Enum/CommandResultEnum.cs
├─ Interface/
│  ├─ ICommandResultRepository.cs
│  ├─ IConnectionADOMonitorDB.cs
│  ├─ IConnectionMonitorDB.cs
│  ├─ IConnectionMSSQLMonitorDB.cs
│  └─ IConnectionSqliteMonitorDB.cs
└─ Monitor.Model.csproj
```

`CommandResult` берёт состав свойств [исторического класса](../../../../Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/CommandResult/CommandResult.cs), кроме `AdapterType`, `IturCodes` и `DocumentHeaderCodes`. `Files` и `UnsureFiles` оставлены как строковые поля первого образца. `ImportDomainEnum` и `ICount4uContext` не переносятся. Конструктор, использовавший `ICount4uContext`, сохраняет остальные параметры и поведение без этой зависимости. `Code` — основное логическое свойство для сравнения объектов; историческое `CommandResultCode` хранит отдельное значение. `Equals` и `GetHashCode` используют `Code`. Остальные перечисления, необходимые этому классу, берутся из [исторического файла](../../../../Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/Enum/CommandResultEnum.cs).

Все пять интерфейсов берутся из [исторической папки](../../../../Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/Interface). Их namespace в образце — `Monitor.Model.Interface`; для другого `<Service>` соответствующие части имён и namespaces заменяются. Интерфейсы сохраняются независимо от выбранного позже провайдера.

При выборе этапа Repository для пары Code First `Entity` ↔ `DomainObject` в этой папке добавляется `I<Имя>Repository`; реализация `<Имя>EFRepository` находится в `RepositoryEF` проекта EF. Типовые методы и порядок добавления дополнительных сигнатур из файла описаны в [[Commands/Add Code First Fields by Step]].

Остальные типы старого `Monitor.Service.Shared`, включая `Login` и `EmailSender`, добавляются только по запросу Parad. Каждый выбранный тип помещается в отдельную папку по назначению; ссылка на точный старый исходный файл и пример использования показываются Parad и при необходимости сохраняются в существующей рабочей задаче или заметках Машины. Порядок поиска и каталог типов приведены в [[Wiki/HowToDo/Create Project Domain Model by Step]].

## Где используется

В текущих архитектурных образцах библиотеку использует [Monitor.Model.Sqlite.CodeFirst.ExportImport](../netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport.md): в его [проекте](../../../../Sources/Architectures/LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport/Monitor.Model.Sqlite.CodeFirst.ExportImport.csproj) есть прямой `ProjectReference` на `Monitor.Model`.

- [CommandResultMapper](../../../../Sources/Architectures/LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport/MappingEF/CommandResultMapper.cs) преобразует `Entity` в `Monitor.Model.CommandResult` и обратно.
- [CommandResultEFRepository](../../../../Sources/Architectures/LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport/RepositoryEF/CommandResultEFRepository.cs) реализует `ICommandResultRepository` и возвращает `CommandResult` и `CommandResults` из `Monitor.Model`.
- [ConnectionSqliteMonitorDB](../../../../Sources/Architectures/LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport/ConnectionSqliteMonitorDB.cs) реализует интерфейс подключения из `Monitor.Model.Interface`.
- [Solution ExportImport](../../../../Sources/Architectures/LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport/Monitor.Model.Sqlite.CodeFirst.ExportImport.sln) включает оба проекта.

## Зависимости и solution

- `Monitor.Model` ссылается через `ProjectReference` на существующий [SelectParam](SelectParam.md) в соседней папке `SelectParam`.
- Оба проекта включены в текущий демонстрационный solution `Monitor.Model.sln`. Для нового автономного применения solution называется именем сервиса, выбранным в начале: `<Service>.sln`; имя БД и имена последующих проектов его не меняют. Два проекта — базовый состав запроса на создание `.Model`; запрос на ExportImport включает уже три проекта: EF-проект, Model и SelectParam. Общего запрета включать другие необходимые проекты в solution нет.
- В рабочем репозитории приложения `Service.Model.EF.SelectParam` хранится как скопированный локальный проект и включается в `<Service>.sln`. `<Service>.Model` получает `ProjectReference` на него, потому что интерфейсы репозитория используют `SelectParams`; внешняя ссылка на репозиторий архитектур не используется.
- Для исторических атрибутов `[Display]` перечислений добавлен `System.ComponentModel.Annotations` версии `4.7.0` — как в [старом `Monitor.Model.ServiceContract`](../../../../Sources/old/WebAPI.Monitor/src/Monitor.Model.ServiceContract/Monitor.Model.ServiceContract.csproj). Другие прямые `PackageReference` у `Monitor.Model` отсутствуют. Зависимости `SelectParam` учитываются при сборке.
- Исторические исходники не изменяются.

Состав работы определяется запросом Parad и фактическим состоянием проекта: названные части создаются или дополняются, существующие части используются без дублирования. 11 последовательностей кубика — примеры, а не закрытый список команд. Сначала Машина готовит Excel и ждёт его проверки и возврата Parad. Затем весь запрошенный комплект классов создаётся одним проходом: по умолчанию в Model и ExportImport, а при явно ограниченном запросе — только в названном проекте или составе. Отдельные подтверждения каждого класса, объекта или этапа после утверждения Excel не требуются. При недостающих зависимостях пути или расширение состава уточняются до генерации. Правила: [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Гибкий состав работы и согласование модели]].

## Вопросы перед созданием

Для этого первого образца определены: `<Service> = Monitor`, расположение в `Sources/Architectures/LibProject/netstandard2.0`, target framework `netstandard2.0`, состав файлов, ссылка на `SelectParam` и включение его в solution. Дополнительных обязательных вопросов перед созданием этого образца нет.

Для следующего применения используй явно указанные или ранее согласованные параметры; если они не заданы, бери параметры первого образца: `<Service> = Monitor`, `netstandard2.0`, готовый состав Model и `System.ComponentModel.Annotations` 4.7.0. Целевой solution или место автономного образца определяй из запроса и однозначного рабочего контекста, иначе уточняй. При интеграции сохраняй defaults первого образца и проверяй совместимость с solution; при несовместимости задавай вопрос, не подстраивай framework и версии автоматически. Имя БД, EF, подход, СУБД и провайдер определяются на этапе запрошенного проекта доступа к данным по тому же правилу defaults.

Имя сервиса `<Service>`, выбранное при создании `<Service>.Model`, задаёт общий префикс связанных проектов и namespaces и имя контекста `<Service>DbContext`. Выбранное позднее имя БД не переопределяет `<Service>` и не переименовывает эти элементы.

## Проверка

Собрать `Monitor.Model.sln`; проверить `ProjectReference`, состав интерфейсов, независимость `Code` и `CommandResultCode`, сравнение по `Code` и отсутствие в новом проекте `ICount4uContext`, `AdapterType`, `ImportDomainEnum`. Первый образец собран без предупреждений и ошибок 2026-09-19.

## Связанные материалы

- [[Tasks/Items/dotnet_architecture_examples/TASK-20260909-003-design-selectparam-guided-workflow]]
- [[Commands/Create Project Domain Model by Step]]
- [[Wiki/HowToDo/Create Project Domain Model by Step]]
- Эталон: `Sources/Architectures/LibProject/netstandard2.0/Monitor.Model/`.

## Образец как опора при создании модели

При создании модели сохраняй стартовые CommandResult/CommandResults, необходимые перечисления и все пять интерфейсов как опору Parad, адаптируя их к правилам проекта. Неиспользование не является основанием убрать их на этом этапе. Удаление ненужного выполняется позднее, на этапе бизнес-правил, по отдельному запросу Parad. Полное правило: [[Tasks/Artifacts/TASK-20260909-003/project-structure-discussion-v1#Образец как опора при создании модели]].

## Согласованные правила развития и вычитки

Таблицы этой архитектуры независимы. Повторы Code допустимы; поведение согласуется по операциям проекта, без универсального выбора минимального ID. Равенство состава DomainObject/Entity относится к стартовому шаблону; последующие бизнес-различия описываются и отображаются явно. Достаточно описанные дополнительные методы реализуются, неизвестное поведение оставляется явно обозначенной заглушкой. Подробности: [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Предметные правила и развитие шаблона]].

После создания согласованного комплекта показывай итоговые файлы/классы целиком для вычитки. Перед классом и новыми/изменёнными членами ставь комментарии с датой генерации и статусом вычитки. Новый код требует Full, изменение ранее вычитанного — проверки Changes с отметкой участка; ранее невычитанное не считается прочитанным. Read ставится только по проверке Parad; возврат Excel сам по себе не означает вычитку кода. Рабочий формат: [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Показ кода и отметки вычитки]].
