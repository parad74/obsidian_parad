Полная последовательность:

```
1. Созданы Entity
2. Созданы EntityConfiguration
3. Создан DbContext
4. Проект собирается
5. Явно создаётся migration InitialCreate
6. Migration проверяется и сохраняется в проекте
7. Запускается приложение
8. DbInitializer.Initialize проверяет наличие БД
9. Если БД отсутствует — применяет готовые migrations и создаёт БД
10. После создания при необходимости добавляет начальные данные
```

Команда до первого запуска:

```
dotnet ef migrations add InitialCreate `
    --context MonitorSqliteDBContext
```