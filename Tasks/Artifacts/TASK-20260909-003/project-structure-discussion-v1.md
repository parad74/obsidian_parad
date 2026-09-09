# SelectParam — обсуждение состава проектов, версия 1

Дата начала: 2026-09-09.

Этот документ последовательно фиксирует назначение проектов будущего эталона до создания архитектурной карточки и исходного кода.

## Согласованные правила — версия 1

1. Внутренние данные приложения называются `DomainObject`.
2. Данные, отображаемые EF на структуру СУБД, называются `Entity`.
3. `DomainObject` и `Entity` обозначают архитектурные роли. Предметный класс сохраняет предметное имя, например `CommandResult`.
4. Проект внутренних моделей и его корневой namespace называются `<Service>.Model`, где `<Service>` — изменяемое имя сервиса.
5. Для первого варианта `<Service> = Monitor`; проект и namespace внутренних моделей называются `Monitor.Model`.
6. `<Service>.Model` содержит внутренние модели приложения и все общие манипуляции с ними.
7. `DomainObject` из `<Service>.Model` могут использоваться на всех более высоких слоях: в репозиториях, прикладных сервисах, бизнес-логике и frontend/UI.
8. `Entity` остаётся внутри проекта доступа к данным и не передаётся на более высокие слои.
9. После получения данных через EF репозиторий сразу преобразует `Entity` в `DomainObject` и возвращает наружу только внутреннюю модель или контейнер внутренних моделей.
10. При записи обратное преобразование `DomainObject` в `Entity` выполняется внутри EF-проекта.
11. `SelectParam` применяется к `IQueryable<Entity>` до материализации и преобразования в `DomainObject`.
12. `TotalCount` вычисляется после фильтрации, но до paging, и возвращается вместе с коллекцией `DomainObject`.
13. Namespace для `Entity` строится как `<Service>.<Provider>.<Approach>`.
14. Первый вариант использует `<Service> = Monitor`, `<Provider> = Sqlite`, `<Approach> = CodeFirst`; итоговый namespace `Entity` — `Monitor.Sqlite.CodeFirst`.
15. Основной исторический пример проекта внутренних моделей: `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared`.
16. Для первого профиля проект, содержащий `Entity` и реализацию доступа к БД, называется `Monitor.Model.Sqlite.CodeFirst.ExportImport`.
17. Второй тип данных проекта `<Service>.Model` — часто используемые пары request/response: `<Имя>Model` и `<Имя>Result` в общей папке `<Имя>`.
18. При создании проекта моделей пары request/response не добавляются автоматически.
19. Перед добавлением предоставляется каталог доступных пар из исторического примера, и Parad выбирает нужные.
20. После выбора исходный код пары копируется без изменений, кроме namespace, который определяется контекстом целевого проекта.
21. Найти и добавить request/response-модели можно на любом этапе разработки, а не только при первоначальном создании `<Service>.Model`.
22. Фраза «найди тип данных для `<назначение>`» ищет подходящие типы по смыслу, показывает точные имена, полноту пары и путь исходной папки, но сама ничего не добавляет.
23. Если назначению соответствуют несколько связанных типов, Codex показывает все варианты и не выбирает один без решения Parad.
24. Codex может предложить список типов, которые подходят или могут быть близки по назначению, кратко объяснить различия и предложить Parad выбрать нужный вариант.
25. Третий тип содержимого проекта — данные и компоненты для стандартной функциональности, сохранённые в историческом примере отдельными наборами.
26. Такой набор предлагается только при точном упоминании согласованного имени или его псевдонима; вместе с предложением Codex показывает путь к исходной папке.
27. Согласованные точные упоминания: `SignalR`; `Claim` или `Claims`; `JwtService` или `Jwt`; `ValidationStartupFilter` или `StartupFilter`; `Urls`.
28. Все `DomainObject`, создаваемые из описания в чате или приложенного файла, предназначены для хранения в БД и размещаются в `<Service>.Model/Domain/<Имя>`; вопрос о сохранении каждого объекта в БД не задаётся.
29. Папка `Domain` является явной границей: модели из неё служат источником для создания `Entity`; остальные типы `<Service>.Model` автоматически в `Entity` не преобразуются.
30. Проект конкретной EF-реализации ссылается на проект Domain Model и на `SelectParam`; если нужного проекта ещё нет в solution, его можно создать или добавить на этом шаге.
31. В начале создания EF-реализации уточняются проект Domain Model и имя базы данных.
32. Для базы создаётся папка `<ИмяБД>`, а внутри неё для каждого типа — папка `<Имя>` с файлом `Entity` `<Имя>.cs`.
33. Во всём проекте конкретной EF-реализации используется один namespace `<Service>.<Provider>.<Approach>`; папки базы и типов не добавляются к namespace. Для первого варианта это `Monitor.Sqlite.CodeFirst`.
34. Нужно ли переносить в EF-проект парный класс `<Имя>s`, пока не определено и будет выясняться на следующих шагах.
35. Для EF Core каждый тип имеет отдельный файл `<Имя>Configuration.cs` с реализацией `IEntityTypeConfiguration<<Имя>>`; EF6-класс `EntityTypeConfiguration<T>` не используется.
36. `Entity` `<Имя>.cs` не содержит Data Annotations для схемы БД; таблица, ключ, генерация значения и свойства столбцов описываются Fluent API в одном файле конфигурации этого типа.
37. В папке типа находятся `<Имя>.cs` и `<Имя>Configuration.cs`; оба используют единый namespace проекта `<Service>.<Provider>.<Approach>`.
38. `DbContext` подключает все конфигурации проекта через `ApplyConfigurationsFromAssembly`.
39. Эталон создаётся для рабочей БД, существующие данные которой должны сохраняться при изменении модели; схема развивается через EF migrations.
40. `DomainObject` является источником состава модели для БД. Изменение `DomainObject` служит основанием для синхронного изменения соответствующих `Entity` и `<Имя>Configuration.cs`.
41. Создание migration никогда не запускается автоматически. Команда выполняется только по отдельному явному запросу Parad в чате либо вручную самой Parad.
42. Применение migration к уже существующей БД никогда не выполняется автоматически и требует отдельного явного запроса Parad либо ручного запуска.
43. До первого запуска приложения должна существовать заранее созданная и проверенная migration `InitialCreate`.
44. При запуске приложения `DbInitializer` проверяет наличие БД. Если БД отсутствует, он автоматически создаёт её, применяя уже подготовленные migrations; это первоначальная инициализация, а не автоматическое обновление существующей БД.
45. Если БД уже существует, `DbInitializer` не применяет pending migrations автоматически.
46. `public static class DbInitializer` хранится в файле `Context/DbInitializer.cs` и использует общий namespace проекта `<Service>.<Provider>.<Approach>`.
47. `EnsureCreated()` не используется: первоначальная БД создаётся из подготовленной цепочки migrations, чтобы сразу иметь migration history.
48. Имя БД строится как `<Service>Db`, например `MonitorDb` или `InventoryDb`; часть `<Service>` становится единым корневым префиксом связанных проектов и namespaces.
49. Для `MonitorDb` используются префикс `Monitor`, Domain-проект и namespace `Monitor.Model`, а namespace EF-реализации начинается с `Monitor`; для `InventoryDb` соответственно используются `Inventory`, `Inventory.Model` и namespace EF-реализации с префиксом `Inventory`.
50. Контекст получает имя от БД по шаблону `<Service>DbContext`, например `MonitorDbContext` или `InventoryDbContext`.
51. Точное имя EF-проекта первого профиля — `Monitor.Model.Sqlite.CodeFirst.ExportImport`; его единый namespace — `Monitor.Sqlite.CodeFirst`.
52. Контекст хранится в файле `Context/<Service>DbContext.cs` и объявляется как `public class <Service>DbContext : DbContext`.
53. Контекст получает `DbContextOptions<<Service>DbContext>` через конструктор и не содержит собственного `OnConfiguring`.
54. Для каждого `Entity` контекст содержит `DbSet` с именем `<ИмяEntity>Datas`; например, `DbSet<CommandResult> CommandResultDatas`. Имя `CommandResults` зарезервировано для парной коллекции `DomainObject` и для `DbSet` не используется.
55. `OnModelCreating` не содержит конфигурацию отдельных таблиц и вызывает `ApplyConfigurationsFromAssembly(typeof(<Service>DbContext).Assembly)`.
56. Контекст не создаёт migrations, не содержит connection string, не вызывает создание БД и не выполняет начальное заполнение; первоначальная инициализация находится в отдельном `Context/DbInitializer.cs`.

## Общий принцип зависимостей

Нижний общий проект может использоваться всеми расположенными выше слоями приложения, но не должен ссылаться на эти слои в обратном направлении.

```text
Front / UI
Business
Application services
Repositories
    -> <Service>.Model
```

Точное положение остальных проектов и направление их ссылок будут согласовываться далее по одному проекту.

## Терминология моделей

- **DomainObject** — внутренние данные приложения, которыми пользуются business-слой, прикладные сервисы, репозитории и frontend/UI.
- **Entity** — представление данных базы, с которым работает EF и которое отображается на таблицы и столбцы СУБД.

`DomainObject` и `Entity` обозначают роли моделей. Предметный класс сохраняет предметное имя, например `CommandResult`; добавлять каждому классу суффикс `DomainObject` или `Entity` без отдельного решения не требуется.

### Namespace для Entity

Namespace `Entity` строится по технологическому профилю:

```text
<Service>.<Provider>.<Approach>
```

Для первого приоритетного профиля:

- `<Service> = Monitor`;
- `<Provider> = Sqlite`;
- `<Approach> = CodeFirst`;
- итоговый namespace: `Monitor.Sqlite.CodeFirst`.

Это правило пока определяет namespace классов `Entity`. Имя содержащего их проекта будет согласовано отдельно.

## <Service>.Model

Имя проекта и корневой namespace строятся как `<Service>.Model`, где `<Service>` — изменяемое имя сервиса.

Значение по умолчанию:

- проект: `Monitor.Model`;
- namespace: `Monitor.Model`.

Статус описания: имя, назначение и граница с EF согласованы; состав общих манипуляций продолжает обсуждаться.

### Назначение

`<Service>.Model` — проект внутренних данных приложения и общих манипуляций с ними. По умолчанию `<Service> = Monitor`, поэтому используется проект `Monitor.Model`.

Основной исторический пример: `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared`.

Модели из этого проекта могут использоваться на всех более высоких слоях приложения, в том числе:

- в бизнес-логике;
- в прикладных сервисах;
- в репозиториях;
- на frontend/UI.

Один и тот же `DomainObject` может передаваться между слоями без создания отдельной копии только ради каждого слоя.

### Предварительно относим к проекту

- классы внутренних данных приложения — `DomainObject`;
- коллекции и контейнеры результата для этих моделей;
- перечисления и value objects, являющиеся частью внутренней модели;
- значения и состояние, принадлежащие самой модели;
- общие операции, которые изменяют, нормализуют, сравнивают, группируют или иным образом обрабатывают внутренние данные и не зависят от конкретной внешней технологии.

### Шаблон DomainObject по умолчанию

Это именованный шаблон создания `DomainObject`.

#### Вызов шаблона

Когда Parad говорит:

```text
Создадим DomainObject <Имя>
```

в согласованном проекте `<Service>.Model` создаются:

```text
Domain/
└─ <Имя>/
   ├─ <Имя>.cs
   └─ <Имя>s.cs
```

- `<Имя>.cs` содержит `public class <Имя>` по шаблону `DomainObject`;
- `<Имя>s.cs` содержит полный согласованный парный класс `public class <Имя>s : ObservableCollection<<Имя>>`;
- папка объекта, оба файла и оба класса получают имена, производные от переданного `<Имя>`;
- все создаваемые по этому шаблону объекты размещаются внутри папки `Domain` и предназначены для хранения в БД;
- отдельный вопрос о сохранении каждого создаваемого `DomainObject` в БД не задаётся;
- оба класса используют ранее согласованный namespace `<Service>.Model`;
- если имя сервиса отдельно не указано, используется `<Service> = Monitor` и namespace `Monitor.Model`;
- вызов этого шаблона сам по себе не создаёт другие классы или проекты.

Если состав полей не оговорён, применяется набор полей и конструктор по умолчанию, описанные ниже.

#### Приложенный файл с описанием данных

К вызову шаблона может быть приложен файл с описанием данных. В этом случае файл является источником для:

- имени класса `DomainObject`;
- имён полей;
- типов полей.

Один приложенный файл может содержать описание как одного, так и нескольких `DomainObject`.

Правила обработки:

- все описанные в файле поля добавляются в класс;
- если для поля не указан тип, используется `string`;
- поле `Code` присутствует в `DomainObject` всегда; если его нет в описании, оно добавляется;
- все итоговые поля явно инициализируются в конструкторе класса;
- парный класс и общая папка создаются по тому же согласованному шаблону и по имени `DomainObject`, извлечённому из файла.

Если в файле описан список объектов, для каждого объекта отдельно создаются:

```text
Domain/
└─ <ИмяОбъекта>/
   ├─ <ИмяОбъекта>.cs
   └─ <ИмяОбъекта>s.cs
```

К каждому объекту независимо применяются правила полей, обязательного `Code`, конструктора, сравнения по `Code`, парной коллекции и namespace `<Service>.Model`. Все описанные в таком файле `DomainObject` предназначены для БД; выбирать это отдельно для каждого объекта не требуется.

Преобразование типов источника в типы C#, значения инициализации для типов кроме уже согласованных `string`, `int` и `long`, а также разрешение конфликта между именем в команде и именем в файле ещё не согласованы и не определяются автоматически.

Если поля объекта отдельно не оговорены, для примера `CommandResult` создаются:

```csharp
public long ID { get; set; }
public string Code { get; set; }
public string Name { get; set; }
public string Description { get; set; }
public string Tag { get; set; }
```

Конструктор явно устанавливает числовым полям `0`, а строковым полям `""`:

```csharp
public CommandResult()
{
    this.ID = 0;
    this.Code = "";
    this.Name = "";
    this.Description = "";
    this.Tag = "";
}
```

Логическим ключом `DomainObject` является свойство `Code`. `Equals` и `GetHashCode` строятся по `Code`:

```csharp
public override bool Equals(object obj)
{
    if (ReferenceEquals(null, obj))
        return false;
    if (ReferenceEquals(this, obj))
        return true;
    if (obj.GetType() != typeof(CommandResult))
        return false;
    return this.Equals((CommandResult)obj);
}

public bool Equals(CommandResult other)
{
    if (ReferenceEquals(null, other))
        return false;
    if (ReferenceEquals(this, other))
        return true;
    return Equals(other.Code, this.Code);
}

public override int GetHashCode()
{
    return this.Code != null ? this.Code.GetHashCode() : 0;
}
```

Выбран первый безопасный вариант `GetHashCode`, совместимый начиная с C# 1.0 и .NET Framework 1.0. Он не вызывает `ToString()` у возможного `null`.

### Парная коллекция DomainObject

Рядом с `CommandResult` всегда хранится `CommandResults`, наследующий `ObservableCollection<CommandResult>`:

```text
CommandResult/
├─ CommandResult.cs
└─ CommandResults.cs
```

```csharp
public class CommandResults : ObservableCollection<CommandResult>
{
    public static CommandResults FromEnumerable(System.Collections.Generic.IEnumerable<CommandResult> List)
    {
        CommandResults commandResults = new CommandResults();
        foreach (CommandResult item in List)
        {
            commandResults.Add(item);
        }
        return commandResults;
    }

    public CommandResult CurrentItem { get; set; }

    public System.EventHandler CurrentChanged { get; set; }

    public long TotalCount { get; set; }
}
```

Оба класса находятся в namespace `<Service>.Model`, для первого варианта — `Monitor.Model`.

Весь показанный состав парного класса согласован и является обязательным шаблоном:

- `FromEnumerable` создаёт типизированную наблюдаемую коллекцию из `IEnumerable<CommandResult>`;
- `CurrentItem` хранит текущий `DomainObject`;
- `CurrentChanged` предоставляет событие изменения текущего объекта;
- `TotalCount` хранит полное количество записей для выборки с paging.

Парный класс с тем же составом всегда создаётся рядом с соответствующим `DomainObject` для удобства работы.

Исторические аналоги:

- `Monitor.Service.Model.CommandResult`;
- `Monitor.Service.Model.CommandResults` с `TotalCount`;
- связанные перечисления и операции над внутренними моделями в `Monitor.Service.Shared`.

Исторический проект используется как источник назначения и примеров, но его состав не копируется автоматически целиком: в нём вместе с моделями находятся HTTP-, SignalR-, authorization- и другие технологические элементы, границы которых должны быть разобраны отдельно.

### Согласованная граница с EF

`Entity` существует только внутри проекта доступа к данным для конкретного EF-профиля и не передаётся на более высокие слои.

Путь чтения:

```text
СУБД
    -> EF / Entity
    -> немедленное преобразование
    -> DomainObject из <Service>.Model
    -> business / services / frontend
```

Путь записи:

```text
DomainObject из <Service>.Model
    -> преобразование внутри EF-проекта
    -> Entity
    -> СУБД
```

Следствия:

- после выполнения EF-запроса репозиторий сразу преобразует полученные `Entity` в `DomainObject`;
- наружу репозиторий возвращает только `DomainObject` и контейнеры результата из `<Service>.Model`;
- `Entity`, `DbContext`, tracking state и provider-specific типы не входят в публичный контракт верхних слоёв;
- маппер знает одновременно `Entity` и `DomainObject`, поэтому находится в проекте конкретной EF-реализации, а не в `<Service>.Model`;
- `TotalCount` вычисляется по EF-запросу до paging, затем прикрепляется к контейнеру `DomainObject`.

### Предлагаемая граница для обсуждения

Чтобы `<Service>.Model` оставался доступным всем слоям, предлагается не помещать в него технологически зависимые элементы:

- `Entity`, существующие только для отображения таблиц;
- `DbContext`, EF-конфигурации и migrations;
- код конкретной СУБД или provider package;
- HTTP-клиенты и контроллеры;
- UI-компоненты;
- seed data и тестовые данные конкретного эталона.

Эта граница пока является предложением Машины и требует согласования с Parad.

### Направление зависимостей

- Более высокие проекты могут ссылаться на `<Service>.Model`.
- `<Service>.Model` не ссылается на frontend, business, repository implementation, EF или конкретную СУБД.
- Возможная ссылка на общую библиотеку `Service.Model.EF.SelectParam` будет решена после определения места контрактов репозитория и операций выборки.

## Тип 2 — пары request/response

В `<Service>.Model` могут храниться часто используемые данные HTTP request/response. Они представлены двумя классами:

```text
<Имя>/
├─ <Имя>Model.cs
└─ <Имя>Result.cs
```

- `<Имя>Model` содержит данные запроса;
- `<Имя>Result` содержит данные результата;
- оба файла находятся рядом в папке `<Имя>`;
- этот тип данных отличается от шаблона `DomainObject` и его парной коллекции.

### Правило добавления

- При первоначальном создании проекта `<Service>.Model` эти пары не создаются автоматически.
- Вернуться к каталогу и добавить выбранные данные можно на любом последующем этапе разработки.
- Codex показывает список доступных пар из `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared`.
- Для каждой пары в списке показывается точный путь к её папке в исходном коде, чтобы при необходимости исследовать использование классов.
- Parad выбирает, какие пары нужно добавить.
- Для выбранной пары код обоих файлов переносится без изменений.
- Единственное допустимое изменение при переносе — namespace по контексту целевого проекта.
- Для первого варианта целевой проект и namespace внутренних моделей — `Monitor.Model`.

### Поиск по назначению

Запрос может быть сформулирован по назначению данных без точного имени класса:

```text
Найди тип данных для <назначение>
```

В ответ Codex должна:

1. Найти подходящие классы в каталоге исторического примера.
2. Составить список прямых и возможных подходящих вариантов.
3. Кратко объяснить, почему каждый вариант может подойти и чем варианты различаются.
4. Показать точные имена найденных классов.
5. Указать, образуют ли они полную пару `<Имя>Model`/`<Имя>Result`.
6. Показать точный путь исходной папки.
7. При необходимости перечислить связанные типы, без которых исходный код не рассматривается изолированно.
8. Предложить Parad выбрать нужный вариант.
9. Ничего не добавлять до выбора или отдельного решения Parad.

Поиск доступен на любом этапе разработки. После выбора нужные данные добавляются по ранее согласованному правилу: исходный код без изменений, кроме namespace по контексту.

#### Пример: логин

Фраза:

```text
Найди тип данных для логина
```

Результат поиска:

- полная пара: `LoginModel` и `LoginResult`;
- исходная папка: `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/Login`;
- связанный тип: `LoginResult` наследует `AuthenticationCommandResult`.

#### Пример: сброс пароля

Фраза:

```text
Найди тип данных для сброса пароля
```

Результат поиска:

- прямое совпадение: `ResetPasswordModel`;
- `ResetPasswordResult` в примере отсутствует;
- исходная папка: `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/EmailSender`;
- связанная полная пара в той же предметной области: `ForgotPasswordModel` и `ForgotPasswordResult`;
- `ForgotPasswordResult` наследует `AuthenticationCommandResult`.

Такой результат требует выбора Parad: добавить только `ResetPasswordModel`, пару `ForgotPasswordModel`/`ForgotPasswordResult` либо согласованный набор этих типов.

### Каталог полных пар в историческом примере

| Имя пары | Папка в исходном коде | Model | Result | Найденные связанные типы |
| --- | --- | --- | --- | --- |
| `Login` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/Login` | `LoginModel` | `LoginResult` | `LoginResult` наследует `AuthenticationCommandResult` |
| `Register` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/Register` | `RegisterModel` | `RegisterResult` | `RegisterResult` наследует `AuthenticationCommandResult` |
| `Profile` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/Profile` | `ProfileModel` | `ProfileResult` | `ProfileModel` реализует `IProfileModel`; `ProfileResult` наследует `AuthenticationCommandResult` |
| `Delete` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/Delete` | `DeleteModel` | `DeleteResult` | `DeleteResult` наследует `AuthenticationCommandResult` |
| `ChangePassword` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/ChangePassword` | `ChangePasswordModel` | `ChangePasswordResult` | `ChangePasswordResult` содержит поля результата непосредственно и не наследует `AuthenticationCommandResult` |
| `ForgotPassword` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/EmailSender` | `ForgotPasswordModel` | `ForgotPasswordResult` | `ForgotPasswordResult` наследует `AuthenticationCommandResult` |
| `RoleModification` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/RoleModification` | `RoleModificationModel` | `RoleModificationResult` | `RoleModificationResult` наследует `AuthenticationCommandResult` |
| `Role` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/RoleModification` | `RoleModel` | `RoleResult` | `RoleModel.cs` также содержит `UserViewModel`; `RoleResult` наследует `AuthenticationCommandResult` |

### Общие связанные типы примера

Большинство классов `<Имя>Result` используют:

- `AuthenticationCommandResult` из папки `AuthenticationCommandResult`;
- `CommandErrorCodeEnum`;
- `SuccessfulEnum`;
- `CommandResultCodeEnum` из `Enum/CommandResultEnum.cs`.

Автоматическое добавление этих связанных типов вместе с выбранной парой пока не согласовано.

### Файлы, не образующие полную пару по этому правилу

В историческом проекте также найдены:

- `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/ChangePassword/UserWithPasswordModel.cs` без `UserWithPasswordResult`;
- `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/EmailSender/ResetPasswordModel.cs` без `ResetPasswordResult`;
- `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/User/UserModel.cs` без `UserResult`;
- `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/WebAPISettings/WebAPISettingsResult.cs`, при этом соответствующий класс называется `WebAPISettings`, а не `WebAPISettingsModel`.

Они не включены в каталог полных пар `<Имя>Model`/`<Имя>Result`. Правила их добавления пока не определены.

## Тип 3 — наборы для стандартной функциональности

В историческом проекте есть данные и компоненты, относящиеся к стандартной функциональности приложения. Они образуют отдельный тип содержимого и не относятся автоматически ни к шаблону `DomainObject`, ни к парам HTTP request/response.

### Правило предложения

- Набор предлагается при точном упоминании одного из согласованных имён или псевдонимов.
- Поиск по свободному описанию назначения для этого типа пока не согласован.
- В предложении указываются фактические файлы набора и точный путь к исходной папке.
- Само упоминание не означает автоматического добавления файлов.
- Правила переноса исходного кода, изменения namespace и добавления зависимостей для этого типа пока не согласованы.

### Согласованные имена, псевдонимы и исходные папки

| Точное упоминание | Также распознаётся | Исходная папка | Найденные файлы |
| --- | --- | --- | --- |
| `SignalR` | — | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/SignalR` | `ChatHub.cs`, `CommandHub.cs`, `HubChatSignalRRepository.cs`, `SignalRtcHub.cs`, `HubCommandSignalRRepository.cs` |
| `Claim` | `Claims` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/Claim` | `ClaimConvertItem.cs`, `ClaimsViewModel.cs`, `ClaimItems.cs`, `ClaimItem.cs` |
| `JwtService` | `Jwt` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/Infrastructure` | `JwtService.cs` |
| `ValidationStartupFilter` | `StartupFilter` | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/StartupFilter` | `SettingValidationStartupFilter.cs` |
| `Urls` | — | `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared` | `Urls.cs` |

Например, при точном упоминании `Jwt` Codex предлагает найденный компонент `JwtService.cs` и показывает папку `Sources/old/WebAPI.Monitor/src/Monitor.Service.Shared/Infrastructure`. Решение о добавлении и способе переноса принимается отдельно.

## Вопросы, оставшиеся по <Service>.Model

1. Входят ли в «все манипуляции» интерфейсы репозиториев и прикладные сервисы либо только операции, принадлежащие данным и не зависящие от хранения и транспорта?
2. Нужно ли автоматически добавлять общие базовые и связанные типы выбранной пары request/response либо сначала показывать их Parad для отдельного подтверждения?

## Следующий проект для обсуждения

Начато обсуждение проекта `Entity`, связанного с БД. Исторический пример первого профиля:

```text
Sources/old/WebAPI.Monitor/src/Monitor.Model.Sqlite.CodeFirst.ExportImport
```

### Первый шаг создания EF-проекта

Проект создаётся в контексте solution и использует два уже существующих либо добавляемых на этом шаге проекта:

```text
Solution
├─ SelectParam
├─ <Service>.Model
└─ проект <Service> + <Provider> + <Approach>
      ├─ ProjectReference → SelectParam
      └─ ProjectReference → <Service>.Model
```

В начале шага Машина должна:

1. Определить или спросить, какой проект является Domain Model.
2. Найти в solution `SelectParam`; если его нет, предложить добавить уже созданную библиотеку либо создать её в этом же solution.
3. Определить или спросить имя базы данных по шаблону `<Service>Db`.
4. В проекте EF-реализации создать папку с именем базы данных.
5. Для каждого `DomainObject` из `<Service>.Model/Domain` создать внутри папки базы отдельную папку типа и файл `Entity`.

Имя БД задаёт общий корневой префикс связанной группы. Суффикс `Db` отбрасывается для получения `<Service>`:

```text
MonitorDb
└─ <Service> = Monitor
   ├─ Domain project: Monitor.Model
   ├─ Domain namespace: Monitor.Model
   ├─ EF namespace: Monitor.<Provider>.<Approach>
   └─ DbContext: MonitorDbContext

InventoryDb
└─ <Service> = Inventory
   ├─ Domain project: Inventory.Model
   ├─ Domain namespace: Inventory.Model
   ├─ EF namespace: Inventory.<Provider>.<Approach>
   └─ DbContext: InventoryDbContext
```

Связанные проекты начинаются с того же `<Service>`. Для текущего профиля полное имя EF-проекта:

```text
Monitor.Model.Sqlite.CodeFirst.ExportImport
```

Его namespace остаётся:

```text
Monitor.Sqlite.CodeFirst
```

Обязательность суффикса `ExportImport` для других будущих EF-проектов пока не определена.

Пример для базы `monitordb` и модели `CommandResult`:

```text
<EF-проект>/
└─ monitordb/
   └─ CommandResult/
      └─ CommandResult.cs
```

Во всём EF-проекте, независимо от расположения файла, используется один namespace:

```text
<Service>.<Provider>.<Approach>
```

Для текущего профиля:

```csharp
namespace Monitor.Sqlite.CodeFirst
```

Папки `monitordb` и `CommandResult` не становятся частями namespace.

Состав создаваемого `Entity`, правила описания БД и вопрос о необходимости парного класса `CommandResults.cs` в EF-проекте пока не согласованы. Они будут разбираться на следующих шагах без предварительного решения.

### Шаблон конфигурации Entity для EF Core

Для каждого `Entity` создаётся один отдельный файл полной Fluent API-конфигурации:

```text
<ИмяБД>/
└─ <Имя>/
   ├─ <Имя>.cs
   └─ <Имя>Configuration.cs
```

Основной класс `<Имя>.cs` не содержит `[Table]`, `[Key]`, `[DatabaseGenerated]` и другие Data Annotations, описывающие схему БД.

Пример `CommandResultConfiguration.cs`:

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Monitor.Sqlite.CodeFirst
{
    public sealed class CommandResultConfiguration
        : IEntityTypeConfiguration<CommandResult>
    {
        public void Configure(EntityTypeBuilder<CommandResult> builder)
        {
            builder.ToTable("CommandResult");

            builder.HasKey(p => p.ID);

            builder.Property(p => p.ID)
                .ValueGeneratedOnAdd();

            builder.Property(p => p.CommandUID)
                .HasMaxLength(100)
                .IsRequired();

            builder.Property(p => p.QueueCode)
                .HasMaxLength(50);
        }
    }
}
```

Все правила отображения одного `Entity` на БД находятся в его единственном файле `<Имя>Configuration.cs` и не распределяются между атрибутами класса, `DbContext` и несколькими конфигурациями.

В `DbContext` конфигурации подключаются одной общей операцией:

```csharp
protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    base.OnModelCreating(modelBuilder);

    modelBuilder.ApplyConfigurationsFromAssembly(
        typeof(MonitorSqliteDBContext).Assembly);
}
```

Это правило относится к EF Core. Исторический `CommandResultConfiguration : EntityTypeConfiguration<CommandResult>` использует API EF6 и в новый EF Core-шаблон не переносится.

### Шаблон Context для EF Core

Имя контекста формируется из уже согласованного имени БД:

```text
MonitorDb
└─ Context/MonitorDbContext.cs
```

Для проекта `Monitor.Model.Sqlite.CodeFirst.ExportImport` согласован следующий код:

```csharp
using Microsoft.EntityFrameworkCore;

namespace Monitor.Sqlite.CodeFirst
{
    public class MonitorDbContext : DbContext
    {
        public MonitorDbContext(
            DbContextOptions<MonitorDbContext> options)
            : base(options)
        {
        }

        public DbSet<CommandResult> CommandResultDatas { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            modelBuilder.ApplyConfigurationsFromAssembly(
                typeof(MonitorDbContext).Assembly);
        }
    }
}
```

Правила шаблона:

- файл находится в папке `Context`;
- имя `<Service>DbContext` получается из имени БД `<Service>Db` без повторного вопроса;
- весь код использует единый namespace проекта `<Service>.<Provider>.<Approach>`;
- `DbContextOptions` передаются через конструктор;
- `OnConfiguring` внутри контекста отсутствует;
- для каждого `Entity` добавляется `DbSet<<ИмяEntity>> <ИмяEntity>Datas`;
- суффикс `Datas` отличает `DbSet<Entity>` от парной коллекции `DomainObject` `<Имя>s`;
- конфигурация таблиц и столбцов находится в отдельных `<Имя>Configuration.cs`;
- `OnModelCreating` только подключает конфигурации текущей assembly;
- connection string, создание БД, migrations и seed data не помещаются в класс контекста;
- первоначальным созданием отсутствующей БД занимается отдельный `Context/DbInitializer.cs` по ранее согласованному правилу.

### Источник модели и migrations

Шаблон предназначен для рабочей базы данных. При изменении модели существующие данные должны сохраняться, поэтому изменения схемы оформляются migrations, а база не удаляется и не создаётся заново через `EnsureCreated()`.

Источником состава модели является `DomainObject` из `<Service>.Model/Domain`:

```text
DomainObject
    → синхронизация Entity
    → синхронизация <Имя>Configuration.cs
    → проверка mapper
    → сборка и проверка изменений модели
```

Изменение `DomainObject` само по себе не запускает migration. Машина должна показать необходимые изменения `Entity` и конфигурации и выполнить их в рамках согласованного шага, но остановиться до команд migrations.

Создание migration допускается только:

- по отдельному явному требованию Parad в чате;
- либо вручную Parad вне действий Машины.

Применение созданной migration к уже существующей БД также является отдельным действием и требует отдельного явного требования либо ручного запуска. Разрешение создать migration не означает разрешения применить её к существующей БД.

До первого запуска приложения должна быть явно создана, проверена и включена в проект migration `InitialCreate`. Генерация migration не выполняется внутри приложения.

При запуске вызывается:

```text
Context/DbInitializer.cs
└─ public static class DbInitializer
```

`DbInitializer` проверяет наличие БД:

```text
БД отсутствует
    → применить заранее подготовленные migrations
    → создать БД актуальной версии

БД существует
    → не применять pending migrations автоматически
```

Автоматическое применение подготовленной цепочки migrations разрешено только для первоначального создания отсутствующей БД. Для уже существующей БД сохраняется правило отдельного явного требования.

Автоматические варианты запрещены:

- не создавать migration только потому, что изменились `DomainObject`, `Entity` или конфигурация;
- не выполнять `dotnet ef database update` для существующей БД без отдельного требования;
- не применять pending migrations к существующей БД при обычном старте приложения;
- не использовать `EnsureCreated()` для рабочей БД, которая сопровождается migrations.

После синхронизации модели Машина только сообщает, что есть изменения схемы и migration ещё не создана или не применена к существующей БД. Точный способ проверки отсутствия БД для каждого provider будет согласован отдельно.

## Точка продолжения

Проект `Monitor.Model.Sqlite.CodeFirst.ExportImport` не закончен.

Последнее согласованное решение:

- создан точный шаблон `Context/MonitorDbContext.cs`;
- `DbSet` именуются `<ИмяEntity>Datas`;
- конфигурации подключаются через `ApplyConfigurationsFromAssembly`;
- обязанности `DbContext` отделены от `DbInitializer`.

При продолжении вернуться к составу EF-проекта после согласованного класса `MonitorDbContext`. Следующий компонент и его правила пока не выбраны.
