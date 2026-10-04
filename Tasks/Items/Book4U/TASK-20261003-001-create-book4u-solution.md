---
type: task
id: TASK-20261003-001
created: 2026-10-03
project: Book4U
---

# TASK-20261003-001 — Создать стартовый solution Book4U

## Проект: Book4U

- [r] Создать Book4U.sln с Model, SelectParam и Code First ExportImport 🆔 TASK-20261003-001

## Цель

Создать автономный стартовый solution по сохранённым правилам и готовому образцу CommandResult.

## Описание

Parad выбрала параметры по одному в текущем чате:

| Параметр | Значение |
| --- | --- |
| Сервис / папка / solution | Book4U / Sources/Book4U / Book4U.sln |
| Model / SelectParam | netstandard2.0 |
| ExportImport | Book4U.Model.Sqlite.CodeFirst.ExportImport, netcoreapp3.1 |
| EF / провайдер | EF Core 3.1.9 / Microsoft.EntityFrameworkCore.Sqlite 3.1.9 |
| Model: Annotations | System.ComponentModel.Annotations 4.7.0 |
| ExportImport: Logging | Microsoft.Extensions.Logging 3.1.9 |
| Design-time пакет / локальный инструмент | Microsoft.EntityFrameworkCore.Design 3.1.9, PrivateAssets=all / dotnet-ef 3.1.9 |
| SelectParam: зависимости | EntityFramework 6.4.0, Microsoft.Windows.Compatibility 3.1.1 |
| Логическое имя БД / контекст | Book4UDb / Book4UDbContext |
| Подключение | Data Source=book4u.db |

Имя файла относительное по прямому выбору Parad; путь определяется рабочим каталогом процесса. Строка подключения сама не создаёт БД.

Стартовый состав: готовые CommandResult/CommandResults, перечисления, пять интерфейсов и NoEntityAttribute в Model; Entity, конфигурация, DbSet, MappingEF и RepositoryEF в ExportImport. Локальный проект SelectParam входит в solution. Предметное описание новых объектов не передано; для готового стартового образца Excel не требуется.

## Критерии приёмки

- Три проекта находятся внутри Sources/Book4U и включены в Book4U.sln.
- ProjectReference локальные, namespaces и имена подключения адаптированы к Book4U; контекст — Book4UDbContext.
- Готовый состав образца сохранён; ID — технический PK, Code — прикладной ключ.
- Удаление по Code удаляет все совпадения; обновление по ID/Code сохраняет ID БД согласно текущему кубику.
- Solution собран, результат проверки сообщён Parad.
- Проверена design-time готовность; необходимая фабрика добавляется без отдельного согласования и не дублирует существующий рабочий способ создания контекста. Ещё не разрешённые зависимости согласуются отдельно. После готовности выдаются точные команды InitialCreate и database update.

## Ограничения

- Не создавать тестовые проекты, автоматизированные тесты, предметные модели и Excel без соответствующего входа.
- Migrations и БД не создавать и не применять без отдельных запросов Parad.
- Git-действия выполняются по явному запросу Parad; запрос «закомить код на gitHub» разрешает сохранение кода Book4U, адрес GitHub уточняется.
- Исходные эталоны и исторические проекты не изменять.

## Артефакты

- [[Commands/Create Project Domain Model by Step]]
- [[Commands/Create Data Objects by Step]]
- [[Commands/Add Code First Fields by Step]]
- [[Documents/Architectures/LibProject/netstandard2.0/Monitor.Model]]
- [[Documents/Architectures/LibProject/netstandard2.0/SelectParam]]
- [[Documents/Architectures/LibProject/netcoreapp3.1/Monitor.Model.Sqlite.CodeFirst.ExportImport]]
- [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository]]

## Код и GitHub

- Рабочая папка: Sources/Book4U.
- Источник: Sources/Architectures/LibProject; текущая версия эталона — cd037d3.
- Создан отдельный Git-репозиторий Sources/Book4U, ветка main.
- Коммит: 228d9b1 — [TASK-20261003-001] Create Book4U solution with SQLite Code First migration.
- GitHub: https://github.com/parad74/Book4U — приватный репозиторий. Коммит 228d9b1 отправлен в main; настроено отслеживание origin/main.
- Коммит на GitHub: https://github.com/parad74/Book4U/commit/228d9b1

## Результат

Текущее состояние: Parad сообщила, что выполнила миграцию и создала БД; продолжается вычитка кода. По её замечанию согласованный вопрос о строке подключения SQLite сохранён в [[Wiki/HowToDo/Create Project Domain Model by Step#Строка подключения SQLite]], ссылки добавлены в команду создания и карточку ExportImport. Выбор относительного имени файла не означает размещение в корне проекта. Ниже сохранены результаты предыдущих этапов подготовки.

Создан Sources/Book4U/Book4U.sln и три локальных проекта. Сборка dotnet build Sources/Book4U/Book4U.sln --no-restore --nologo -v:minimal успешна: 0 предупреждений, 0 ошибок.

Первое восстановление через api.nuget.org завершилось NU1301 (SSL/учётные данные песочницы). Выполнено успешное локальное восстановление из C:/Users/Parad/.nuget/packages, без сетевого обращения и изменения версий: dotnet restore Sources/Book4U/Book4U.sln --source C:/Users/Parad/.nuget/packages -p:NuGetAudit=false. Отключение NuGetAudit действует только для этой offline-команды, не записано в проекты; актуальный сетевой аудит пакетов не выполнялся.

Проверены три локальных ProjectReference, выбранные framework/версии, имена и namespaces, 74 совпадающих свойства CommandResult с ID первым, пять интерфейсов Model, NoEntityAttribute, сохранение ID в ApplyChanges и удаление всех совпадений Code. Предметные поля образца (включая MonitorAddress) не переименовывались. ISelectParams.cs в копии SelectParam помещён в Interface по Sources/AGENTS.md; его код и остальная библиотека сохранены без изменений. Адаптированные классы и члены Model/ExportImport отмечены Generated=2026-10-03, Unread, Full.

Стартовый комплект передан для вычитки. Заглушка ToSimpleDomainObject сохранена согласно образцу. Реальная БД и migrations не создавались; работа CRUD с БД не проверялась. Эталон не изменён, Git Book4U не инициализирован.

По ответу Parad «добавь нужные пакеты» добавлен Microsoft.EntityFrameworkCore.Design 3.1.9 с PrivateAssets=all в ExportImport; dotnet-ef 3.1.9 установлен как локальный инструмент, Sources/Book4U/.config/dotnet-tools.json. Глобальный инструмент не устанавливался. dotnet ef --version подтвердил 3.1.9. После offline restore в кэш Parad сборка вне песочницы успешна: 0 предупреждений, 0 ошибок. Песочница не давала записывать bin/obj; восстановление и сборка в одной пользовательской среде устранили различие кэшей.

По запросу Parad «добавь все что требуется до - для миграции» добавлена Context/Book4UDbContextFactory.cs, реализующая IDesignTimeDbContextFactory<Book4UDbContext>. Фабрика получает строку из существующего ConnectionSqliteBook4UDB и настраивает UseSqlite; DbInitializer, Migrate и EnsureCreated не вызывает. Это заменяет прежнее ожидание согласования фабрики.

После добавления фабрики solution собран: 0 предупреждений, 0 ошибок. dotnet ef dbcontext info успешно создал контекст: Provider name — Microsoft.EntityFrameworkCore.Sqlite, Database name — main, Data source — book4u.db. Подготовка завершена; фабрика передана на вычитку с Unread/Full. Миграции и БД не создавались.

Команды для следующих отдельных действий из PowerShell (подготовлены, не выполнены):

```powershell
Set-Location 'W:\obsidian\_parad\Sources\Book4U'
$efProject = 'Book4U.Model.Sqlite.CodeFirst.ExportImport/Book4U.Model.Sqlite.CodeFirst.ExportImport.csproj'
$efContext = 'Book4U.Sqlite.CodeFirst.Book4UDbContext'

# Создать начальную миграцию
dotnet ef migrations add InitialCreate --project $efProject --startup-project $efProject --context $efContext --output-dir Migrations

# Применить миграцию и создать БД
dotnet ef database update --project $efProject --startup-project $efProject --context $efContext
```

## Журнал

- 2026-10-03 — Parad запросила полный стартовый solution и последовательно выбрала параметры; имя Book4U задано ранее. Создана одна карточка результата, Doing. Следующее действие — адаптировать копии готовых проектов, собрать solution и проверить design-time готовность.

- 2026-10-03 — Создан и собран стартовый Book4U, 0 предупреждений/ошибок; статическая сверка состава пройдена. Design-time подготовка требует отдельно согласованных дополнений. Карточка переведена в Question и on_hold до ответа Parad; итоговые файлы предоставлены для вычитки.

- 2026-10-03 — По запросу Parad добавлены Design 3.1.9 и локальный dotnet-ef 3.1.9. Инструмент запускается, solution собран: 0 предупреждений/ошибок. Design-time проверка подтвердила необходимость фабрики Book4UDbContext; согласование этого кода остаётся следующим шагом. Пакеты установлены, migrations и БД не создавались. Question/on_hold до решения о фабрике.

- 2026-10-03 — Parad разрешила всю подготовку до миграции. Карточка возвращена из on_hold в Doing; добавлена design-time фабрика, сборка и dbcontext info успешны. Команды InitialCreate/database update сохранены без выполнения. Статус Review для вычитки результата.

- 2026-10-03 — По замечанию Parad при вычитке Book4U вопрос о размещении SQLite заменён выбором строки подключения: только имя файла с пояснением рабочего каталога либо полный путь. Сохранены независимый выбор имени БД и файла, порядок вопросов и отсутствие повторного согласования заданных параметров. Обновлены пользовательская инструкция, команда создания и карточка ExportImport. После проверки правки переданы на Review; вычитка продолжается.

- 2026-10-03 — Parad отменила автоматические комментарии CodeReview при первой генерации, создании, миграциях и добавлении данных. Теперь маркировка включается только явной просьбой «при изменениях пометь как TODO» / «при дополнениях пометь как TODO» для указанной работы. Основное правило обновлено в разделе «Показ кода и отметки вычитки» кубика; синхронизированы три команды, пользовательская инструкция, карточки Model/ExportImport и действующий документ точных шаблонов. Формат, Full/Changes и подтверждение Read сохранены для явно включённой маркировки. Существующий код Book4U в рамках этой правки инструкций не изменялся. Проверены связанные формулировки и diff; Review, вычитка продолжается.

- 2026-10-03 — По явному запросу Parad удалены все 288 строки TODO: CodeReview с Generated=2026-10-03, Status=Unread, Scope=Full из 24 исходных файлов Book4U. Побайтовая проверка подтвердила, что удалены только эти отдельные строки; остальное содержимое сохранено.

Проверка после удаления меток: совпадений в C#-файлах Book4U не осталось; сборка solution успешна, 0 предупреждений и 0 ошибок. Карточка возвращена в Review для продолжающейся вычитки.

- 2026-10-03 — По запросу «закомить код на gitHub» создан локальный Git Book4U и коммит 228d9b1 (42 файла, включая миграцию). Добавлен .gitignore для bin/obj, .vs, локальных БД и секретов; рабочее дерево чистое. Проверка типовых секретов не нашла совпадений. diff --check показал существующие пробелы в скопированном коде; ради коммита форматирование не менялось. GitHub CLI отсутствует; открыта страница входа GitHub через computer-use. Ожидаются адрес/выбор приватного parad74/Book4U и вход пользователя в GitHub. Question/on_hold до продолжения публикации.

- 2026-10-03 — Parad подтвердила отправку в предложенный parad74/Book4U. Браузер остаётся на форме входа GitHub. Проверка git ls-remote не дала подтверждённого результата; повторная попытка зависла и была прервана до remote add/push. Дальнейшие обращения этим способом остановлены; требуется вход пользователя в открытой вкладке GitHub. Локальный коммит сохранён.

- 2026-10-03 — После входа Parad в GitHub подтверждён пустой приватный parad74/Book4U. Добавлен origin, коммит 228d9b1 успешно отправлен в main через пользовательскую среду Git. Для различия владельцев использован разовый safe.directory только для Book4U, глобальные настройки не менялись. Ветка отслеживает origin/main, рабочее дерево чистое. Публикация завершена; Review для продолжающейся вычитки кода.

- 2026-10-03 — По явному запросу Parad добавлено правило: необходимая design-time фабрика при создании solution с ExportImport входит в подготовку без отдельного согласования, использует выбранные провайдер и подключение, не дублирует рабочий способ создания контекста. После неё проверяются сборка и создание контекста без изменения БД. Заменено прежнее требование отдельного согласования фабрики в команде создания, пользовательской инструкции, карточке ExportImport и критерии этой задачи; исторические записи сохранены. Правила зависимостей и отдельных запросов на создание/применение migrations сохранены. Проверены diff и связанные формулировки; Review.

- 2026-10-03 — По замечанию Parad закреплено различие единичного DomainObject/Entity и отдельной ObservableCollection в кубике и связанных командах/карточках. Убрано несогласованное IEquatable из шести моделей Book4U и эталонного CommandResult; методы Equals/GetHashCode по Code сохранены. Проверены коллекции, интерфейсы и реализации репозиториев, мапперы и DbSet: единичные и множественные контракты разделены, зависимостей этих моделей от IEquatable не найдено. В текущем Book4U не найдено вызовов Contains/Remove/Distinct либо хеш-коллекций над этими DomainObject; единственный Remove в EF относится к Entity CommandResult по ID. Внутренний IEquatable<Signature> библиотеки SelectParam не относится к моделям и сохранён. Сборки Book4U и эталонного Monitor.Model успешны: 0 предупреждений/ошибок. Это статическая проверка и сборка, не проверка CRUD с реальной БД. Миграции и БД не изменялись. Review для продолжения вычитки.
