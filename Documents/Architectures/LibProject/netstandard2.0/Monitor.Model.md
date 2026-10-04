---
type: architecture
runtime_family: netstandard
target_framework: netstandard2.0
project: Monitor.Model
---

# Monitor.Model

## Назначение

Контракт библиотеки внутренних данных `<Service>.Model` и описание первого профиля Monitor.Model на netstandard2.0. Библиотека содержит DomainObject, коллекции и контейнеры, перечисления, value objects, интерфейсы и общие операции над внутренними данными, не зависящие от конкретной внешней технологии. Верхние слои используют эти типы без обязательной копии для каждого слоя. Разрешены стандартные типы выбранного framework и операции самой модели; ASP.NET-, SignalR-, frontend- и другая инфраструктурная реализация в Model не размещается.

Устойчивые границы и направления ссылок: [[Documents/Architectures/Data Model Harness#Модули и устойчивые границы]]. Для нового применения основной источник кода — [[Documents/Architectures/Data Model Examples]]; первый профиль ниже сохраняет своё имя и историю.

## Контракт новых DomainObject

DomainObject, создаваемые из описания в чате или файле, размещаются в `<Service>.Model/Domain/<Имя>` и предназначены для хранения в БД. Папка `Domain` является границей автоматического создания Entity; типы вне неё автоматически в Entity не преобразуются.

Для нового DomainObject действуют правила:

- первое свойство — обязательное `public long ID { get; set; }`, в конструкторе `ID = 0`;
- `Code` обязателен и используется для `Equals` и `GetHashCode`, но не становится первичным ключом БД;
- рядом создаётся `<Имя>s : ObservableCollection<<Имя>>` с `FromEnumerable`, `CurrentItem`, `CurrentChanged` и `TotalCount`;
- состав остальных полей берётся из утверждённого Excel, а не из предметных полей `CommandResult`;
- атрибуты из опционального столбца `Attributes` добавляются на свойства DomainObject; `[NoEntity]` исключает свойство из Entity, конфигурации и всех методов маппера по [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Attributes и NoEntity]];
- типы и defaults, отсутствующие во входе, предлагаются в Excel и согласуются возвратом книги.

Если состав полей нового DomainObject вообще не задан, минимальный набор по прежнему согласованному шаблону — `long ID` и строки `Code`, `Name`, `Description`, `Tag`. Покажи этот набор в Excel для проверки; он не подменяет поля переданного описания и не сокращает полный готовый стартовый `CommandResult`.

Конструктор явно инициализирует все свойства. Базовые значения шаблона — `0` для `int`/`long` и `""` для `string`; другие значения из источника или предложенные варианты явно показываются в Excel. Значения конструктора и DB defaults не считаются одним и тем же.

Проверки null, идентичности экземпляра и типа в Equals, а также безопасный hash по Code показаны в [[Documents/Architectures/Data Model Examples#Выбор примера]] на Room. Полный контракт единичного объекта, коллекции и их потребителей: [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Единичный объект и коллекция]].

Коллекция находится рядом с DomainObject в `Domain/<Имя>` и использует namespace `<Service>.Model`. `FromEnumerable` создаёт типизированную коллекцию, `CurrentItem` хранит текущий объект, `CurrentChanged` — обработчик изменения текущего объекта, `TotalCount` — полное количество записей после фильтрации до paging. Образец реализации — Rooms из фиксированной версии Book4U.

## Состав первого образца

Первый образец Monitor содержит следующий готовый состав. При новом применении используй [[Documents/Architectures/Data Model Examples#Применение готового состава]] и [[Commands/Create Project Domain Model by Step#Состав solution]]. Готовый стартовый объект и создание новых предметных объектов имеют разные входы; поля CommandResult не задают состав остальных моделей.

```text
Monitor.Model/
├─ Domain/CommandResult/
│  ├─ CommandResult.cs
│  └─ CommandResults.cs
├─ NoEntityAttribute.cs
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

Остальные типы старого `Monitor.Service.Shared`, включая `Login` и `EmailSender`, добавляются только по запросу Parad. Каждый выбранный тип помещается в отдельную папку по назначению; ссылка на точный старый исходный файл и пример использования показываются Parad и при необходимости сохраняются в существующей рабочей задаче или заметках Машины. Порядок поиска и каталог типов приведены в [[Documents/Architectures/Data Model Examples#Тип 2 — пары request/response]].

## Атрибут NoEntity и Excel

Расположение, назначение служебного NoEntityAttribute, формат Attributes и исключение полей из сохраняемого представления определены в [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Attributes и NoEntity]].

Атрибут входит в стартовый состав по [[Commands/Create Project Domain Model by Step#Состав solution]].

## Где используется

В текущих архитектурных образцах библиотеку использует [Monitor.Model.Sqlite.CodeFirst.ExportImport](../netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport.md): в его [проекте](../../../../Sources/Architectures/LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport/Monitor.Model.Sqlite.CodeFirst.ExportImport.csproj) есть прямой `ProjectReference` на `Monitor.Model`.

- [CommandResultMapper](../../../../Sources/Architectures/LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport/MappingEF/CommandResultMapper.cs) преобразует `Entity` в `Monitor.Model.CommandResult` и обратно.
- [CommandResultEFRepository](../../../../Sources/Architectures/LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport/RepositoryEF/CommandResultEFRepository.cs) реализует `ICommandResultRepository` и возвращает `CommandResult` и `CommandResults` из `Monitor.Model`.
- [ConnectionSqliteMonitorDB](../../../../Sources/Architectures/LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport/ConnectionSqliteMonitorDB.cs) реализует интерфейс подключения из `Monitor.Model.Interface`.
- [Solution ExportImport](../../../../Sources/Architectures/LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport/Monitor.Model.Sqlite.CodeFirst.ExportImport.sln) включает оба проекта.

## Зависимости и solution

Границы ссылок проектов заданы [[Documents/Architectures/Data Model Harness#Модули и устойчивые границы]]. Правило физического включения SelectParam: [[Documents/Architectures/LibProject/netstandard2.0/SelectParam#Перенос в рабочее приложение]]. Новый стартовый состав: [[Commands/Create Project Domain Model by Step#Состав solution]].

В первом Monitor.Model.sln находятся Monitor.Model и соседний SelectParam. Для исторических Display-атрибутов добавлен System.ComponentModel.Annotations 4.7.0; других прямых PackageReference у Monitor.Model нет. Учитываются также зависимости SelectParam. Исторические исходники не изменяются.

## Вопросы перед созданием

Параметры нового применения и правило использования существующих значений: [[Wiki/HowToDo/Create Project Domain Model by Step#Параметры по умолчанию]]. Сведения первого профиля выше описывают существующий образец и не являются автоматически выбранными значениями нового проекта.

## Проверка

Первый Monitor.Model.sln собран без ошибок и предупреждений 2026-09-19. При новом применении проверяй целевой solution по [[Commands/Create Project Domain Model by Step]] и контракт нового объекта по этой карточке. В готовом стартовом составе Code и CommandResultCode — независимые свойства; ICount4uContext, AdapterType и ImportDomainEnum не возвращаются из исторического кода.

## Связанные материалы

- [[Tasks/Items/dotnet_architecture_examples/TASK-20260909-003-design-selectparam-guided-workflow]]
- [[Commands/Create Project Domain Model by Step]]
- [[Wiki/HowToDo/Create Project Domain Model by Step]]
- Эталон: `Sources/Architectures/LibProject/netstandard2.0/Monitor.Model/`.

## Образец как опора при создании модели

На этапе создания модели сохраняй предусмотренный стартовый комплект: `CommandResult`, парную коллекцию `CommandResults`, необходимые перечисления и все пять интерфейсов. Для Parad это опора при чтении и построении модели, даже если часть комплекта пока не используется в предметной задаче или относится к другому провайдеру.

Включай комплект с учётом согласованных правил конкретного проекта: адаптируй namespaces, ссылки на типы и соответствующие сервису имена; сохраняй согласованные правила библиотек и совместимость. Состав новых предметных объектов определяется их входным описанием; поля `CommandResult` не становятся обязательными полями других моделей.

Не исключай и не удаляй части этого комплекта на этапе создания модели только из-за их неиспользования. После создания модели, на этапе бизнес-правил, Parad отдельно попросит удалить ненужное. Тогда проверь фактическое использование и зависимости и выполни согласованное удаление. Сам переход к бизнес-правилам не является командой очистки. Существующий эталон сохраняется.

## Согласованные правила развития и вычитки

При изменении контрактов и реализации используй [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Предметные правила и развитие шаблона]]. При передаче результата — [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Показ кода и отметки вычитки]].
