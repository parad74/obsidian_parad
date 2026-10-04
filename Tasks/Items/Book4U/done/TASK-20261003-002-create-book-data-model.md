---
type: task
id: TASK-20261003-002
created: 2026-10-03
project: Book4U
---

# TASK-20261003-002 — Создать предметную модель Book4U

## Проект: Book4U

- [x] Создать Room, Location, Book, Category и Author по описанию 🆔 TASK-20261003-002 ✅ 2026-10-03

## Цель

Разобрать Object Room.docx, согласовать модель в Excel и создать полный комплект объектов в существующем Book4U.

## Описание

Источник: Sources/AppData/test/Booksdb/inData/Object Room.docx. Запрос Parad: «файл с описанием данных модели — начали». Текущий проект из чата — Book4U. В источнике пять объектов, 28 свойств. Обязательное ID long добавляется первым к каждому объекту (итого 33 свойства). Эти классы в Book4U пока отсутствуют.

## Критерии приёмки

- Excel 2013: один лист на объект; исходные значения и предложения разделены, Attributes предусмотрен.
- Parad проверила и вернула утверждённую книгу до генерации.
- После утверждения созданы DomainObject/коллекции, Entity/конфигурации/DbSet, MappingEF, интерфейсы и реализации Repository для всех пяти объектов; solution собран.

## Ограничения

- Источник, существующие классы и БД не изменять при подготовке Excel.
- Не создавать и не применять migrations автоматически.
- Не ставить комментарии CodeReview без явной просьбы; не добавлять связи/FK между независимыми таблицами.
- Не переносить предметные поля CommandResult в новые объекты.

## Артефакты

- [[Commands/Create Data Objects by Step]]
- [[Commands/Add Code First Fields by Step]]
- [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository]]
- [[Tasks/Artifacts/TASK-20261003-002/book4u-data-model.xlsx]]

## Код и GitHub

- Коммит [5c1aace](https://github.com/parad74/Book4U/commit/5c1aace) — [TASK-20261003-002] Первая версия модели и репозиториев; отправлен в main.

- Solution: Sources/Book4U/Book4U.sln; https://github.com/parad74/Book4U.
- DomainObject: Sources/Book4U/Book4U.Model/Domain/<Object>/<Object>.cs, коллекция рядом; namespace Book4U.Model.
- Entity: Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/Book4UDb/<Object>/<Object>.cs, конфигурация рядом; namespace Book4U.Sqlite.CodeFirst.
- Context: Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/Context/Book4UDbContext.cs.
- MappingEF и RepositoryEF: одноимённые папки ExportImport; интерфейсы — Book4U.Model/Interface.
- Профиль: netstandard2.0 / netcoreapp3.1, EF Core SQLite 3.1.9.

## Результат

Миграция 20261003113005_AddBookDataModel применена по отдельному запросу Parad к существующей Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/book4u.db. Проверены пять новых таблиц (33 столбца), ID/PK, nullable и defaults, отсутствие FK, обе записи истории миграций и PRAGMA integrity_check = ok. CommandResult сохранён; до и после применения 0 записей. Ниже результаты предыдущих этапов.

Подготовлена миграция `20261003113005_AddBookDataModel`: создаёт Room, Location, Book, Category и Author. Обновлён snapshot и создан Designer. SQL проверен: только пять новых таблиц и запись migration history, существующие таблицы не изменяются; автогенерация только ID, Count имеет DEFAULT 0. Скрипт: [[Tasks/Artifacts/TASK-20261003-002/AddBookDataModel.sql]]. Сборка при генерации SQL успешна. Миграция к БД не применялась.

Текущий результат: по возвращённой и утверждённой книге создано 35 файлов (по 7 на объект) и добавлены 5 DbSet в Book4UDbContext. Сборка Book4U.sln успешна: 0 предупреждений, 0 ошибок. Статически сверены все 33 свойства DomainObject/Entity с Excel, defaults C#/БД, длины, nullable, маппинг, сохранение ID при обновлении и удаление всех совпадений Code. ToSimpleDomainObject остаётся согласованной заглушкой. Комментарии CodeReview не добавлялись. Миграции и существующая БД не изменялись; CRUD на реальной БД не проверялся. Для появления новых таблиц потребуется отдельно создать и применить миграцию. Коммит и push для этих изменений не выполнялись.

### Файлы для вычитки

- Room: [Room.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model/Domain/Room/Room.cs), [Rooms.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model/Domain/Room/Rooms.cs), [IRoomRepository.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model/Interface/IRoomRepository.cs), [Room.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/Book4UDb/Room/Room.cs), [RoomConfiguration.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/Book4UDb/Room/RoomConfiguration.cs), [RoomMapper.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/MappingEF/RoomMapper.cs), [RoomEFRepository.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/RepositoryEF/RoomEFRepository.cs).
- Location: [Location.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model/Domain/Location/Location.cs), [Locations.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model/Domain/Location/Locations.cs), [ILocationRepository.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model/Interface/ILocationRepository.cs), [Location.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/Book4UDb/Location/Location.cs), [LocationConfiguration.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/Book4UDb/Location/LocationConfiguration.cs), [LocationMapper.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/MappingEF/LocationMapper.cs), [LocationEFRepository.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/RepositoryEF/LocationEFRepository.cs).
- Book: [Book.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model/Domain/Book/Book.cs), [Books.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model/Domain/Book/Books.cs), [IBookRepository.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model/Interface/IBookRepository.cs), [Book.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/Book4UDb/Book/Book.cs), [BookConfiguration.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/Book4UDb/Book/BookConfiguration.cs), [BookMapper.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/MappingEF/BookMapper.cs), [BookEFRepository.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/RepositoryEF/BookEFRepository.cs).
- Category: [Category.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model/Domain/Category/Category.cs), [Categories.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model/Domain/Category/Categories.cs), [ICategoryRepository.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model/Interface/ICategoryRepository.cs), [Category.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/Book4UDb/Category/Category.cs), [CategoryConfiguration.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/Book4UDb/Category/CategoryConfiguration.cs), [CategoryMapper.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/MappingEF/CategoryMapper.cs), [CategoryEFRepository.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/RepositoryEF/CategoryEFRepository.cs).
- Author: [Author.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model/Domain/Author/Author.cs), [Authors.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model/Domain/Author/Authors.cs), [IAuthorRepository.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model/Interface/IAuthorRepository.cs), [Author.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/Book4UDb/Author/Author.cs), [AuthorConfiguration.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/Book4UDb/Author/AuthorConfiguration.cs), [AuthorMapper.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/MappingEF/AuthorMapper.cs), [AuthorEFRepository.cs](W:/obsidian/_parad/Sources/Book4U/Book4U.Model.Sqlite.CodeFirst.ExportImport/RepositoryEF/AuthorEFRepository.cs).

Результаты предыдущего этапа подготовки Excel:

Подготовлена книга Tasks/Artifacts/TASK-20261003-002/book4u-data-model.xlsx: пять листов, 33 свойства. Все листы проверены визуально; сохранённый XLSX сверен с 28 полями Word, проверены ID, типы, defaults и длины. Использованы стандартные таблицы и списки выбора без формул/макросов; запуск именно в Excel 2013 не выполнялся. Код и БД не изменялись. Ожидается возвращённая утверждённая книга перед генерацией. Предлагается переносить исходные defaults и в конструктор C#, и в DB default; для ID — ID=0 в C#, генерация БД без DB default. Nullable в источнике не указан: строки предлагаются nullable по текущему образцу, int и long — NOT NULL. Эти предложения согласуются в Excel, не считаются заданными источником.

## Журнал

- 2026-10-03 — Найден и прочитан Object Room.docx; начат разбор пяти объектов в Excel. Создана карточка самостоятельного результата, Doing.

- 2026-10-03 — Excel подготовлен и проверен. Вопросы о nullable строк и DB defaults вынесены в книгу. Карточка Question/on_hold до проверки и возврата Excel Parad.

- 2026-10-03 — Parad вернула book4u-data-model.xlsx с просьбой «продолжай»: модель утверждена. Исходные и предлагаемые значения проверены; изменений и дополнительных ответов нет. Полный состав пяти объектов, nullable строк и defaults C#/БД приняты как показано в книге. Doing; генерация всего комплекта без промежуточных согласований.

- 2026-10-03 — Создан полный комплект всех пяти объектов, сборка успешна. Состав и правила CRUD проверены статически, новые migrations не создавались. Файлы переданы Parad целиком по ссылкам для вычитки; Review.

- 2026-10-03 — По замечанию Parad закреплено различие единичного DomainObject/Entity и отдельной ObservableCollection в кубике и связанных командах/карточках. Убрано несогласованное IEquatable из шести моделей Book4U и эталонного CommandResult; методы Equals/GetHashCode по Code сохранены. Проверены коллекции, интерфейсы и реализации репозиториев, мапперы и DbSet: единичные и множественные контракты разделены, зависимостей этих моделей от IEquatable не найдено. В текущем Book4U не найдено вызовов Contains/Remove/Distinct либо хеш-коллекций над этими DomainObject; единственный Remove в EF относится к Entity CommandResult по ID. Внутренний IEquatable<Signature> библиотеки SelectParam не относится к моделям и сохранён. Сборки Book4U и эталонного Monitor.Model успешны: 0 предупреждений/ошибок. Это статическая проверка и сборка, не проверка CRUD с реальной БД. Миграции и БД не изменялись. Review для продолжения вычитки.

- 2026-10-03 — По запросу «подготовь миграцию» создана 20261003113005_AddBookDataModel. Проверены Up/Down и сгенерированный SQL; сборка успешна. В Up только пять новых таблиц, без FK/уникальных индексов/изменений CommandResult. Аннотация Sqlite:Autoincrement, добавленная EF 3.1.9 к Count в C# migration, не попадает на Count в SQL; итоговый столбец INTEGER NOT NULL DEFAULT 0. Database update не запускался. Review.

- 2026-10-03 — По запросу «сделай миграцию» проверены путь и InitialCreate в существующей БД. Из рабочей папки ExportImport выполнен database update AddBookDataModel: успешно. Новые таблицы и история подтверждены чтением SQLite, integrity_check = ok; исходная таблица сохранена. Review.

- 2026-10-03 — Parad подтвердила: «вижу таблицы в бд созданы». Пользовательская проверка создания таблиц пройдена; статус Checked. Подтверждение не означает вычитку всех классов или проверку всех операций CRUD.

- 2026-10-03 — По запросу Parad весь актуальный solution сохранён и отправлен в GitHub коммитом 5c1aace «Первая версия модели и репозиториев» (40 изменённых/новых файлов). Сохранена присутствующая пользовательская правка CommandResult: Equals/GetHashCode по OperationIndexCode; пять новых моделей остаются со сравнением по Code. Сборка перед коммитом успешна: 0 предупреждений/ошибок. БД, bin/obj и .vs исключены .gitignore. Push main успешен, рабочее дерево чистое. После пользовательской проверки таблиц и запрошенного сохранения первая версия завершена; Done.
