# Create Data Objects by Step — v2

## Когда применять

При создании и дополнении объектов по запросу и фактическому коду; слова «по кубику» не обязательны. Сначала прочитай [[Documents/Architectures/Data Model Harness]] и [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository]]. Подключение кубика не создаёт отдельный генератор или навык.

## Выполнение

1. Определи источник и запрошенные части. Восстанови существующие классы, проекты, пути и профиль. Входы этапов: [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Рабочий контекст и пути]].
2. Определи состав и недостающие зависимости по [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Гибкий состав работы и согласование модели]]. Если требуются новые проекты, используй начальные вопросы из Wiki; не выбирай их параметры молча.
3. Разбери вход по [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Источники данных и нормализация]] и подготовь Excel по правилам согласования кубика. Не записывай зависящий код до возврата утверждённой книги и разрешения её неоднозначностей.
4. Выполни выбранные этапы по [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Результат этапов]]; для дополнения полей, Mapper и Repository используй [[Commands/Add Code First Fields by Step]]. Применяй [[Documents/Architectures/Data Model Principles]] и нужные [[Documents/Architectures/Data Model Examples]].
5. Проверь результат по [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Проверка и состояние]] и передай код по [[Documents/Architectures/Cubes/DotNet/DomainObject - Entity - MappingEF - Repository#Показ кода и отметки вычитки]].

## Возобновление

При продолжении проверь фактические solution, .csproj, код и существующую рабочую задачу. Восстанови утверждённый Excel, согласованный состав, созданные файлы и нерешённые вопросы. Не повторяй выполненную генерацию; незавершённый согласованный комплект закончи одним проходом. Отдельного паспорта или обязательного формата заметок нет.
