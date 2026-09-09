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
16. Имя проекта, содержащего `Entity`, пока не определено и будет согласовано отдельно.
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
<Имя>/
├─ <Имя>.cs
└─ <Имя>s.cs
```

- `<Имя>.cs` содержит `public class <Имя>` по шаблону `DomainObject`;
- `<Имя>s.cs` содержит полный согласованный парный класс `public class <Имя>s : ObservableCollection<<Имя>>`;
- папка, оба файла и оба класса получают имена, производные от переданного `<Имя>`;
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
<ИмяОбъекта>/
├─ <ИмяОбъекта>.cs
└─ <ИмяОбъекта>s.cs
```

К каждому объекту независимо применяются правила полей, обязательного `Code`, конструктора, сравнения по `Code`, парной коллекции и namespace `<Service>.Model`.

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

После уточнения состава `<Service>.Model` определить отдельный проект контрактов репозитория либо сразу проект реализации репозитория и его зависимости.
