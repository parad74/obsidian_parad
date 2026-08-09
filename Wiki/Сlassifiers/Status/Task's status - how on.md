**Tasks — это отдельная система custom statuses**, и для неё нужны две вещи одновременно:

1. Tasks должен знать, что означает символ внутри `[ ]`.
2. Тема или CSS-snippet должен уметь этот символ красиво рисовать. Документация Tasks прямо разделяет логику статуса и его визуальное оформление.
3. Но если оставить стандартную тему Obsidian без дополнительного CSS, они могут выглядеть почти одинаково или не так, как ожидаешь. Tasks прямо указывает, что custom statuses требуют темы или CSS-snippet с поддержкой custom checkboxes.

Сначала зайди:

**Settings → Tasks → Statuses / Custom Statuses**

### А внешний вид дадим через CSS

Создай файл, например:

```
.obsidian/
└── snippets/
    └── task-statuses.css
```

И включи его:

**Settings → Appearance → CSS snippets → task-statuses**

или **Settings → Appearance → CSS snippets → Reload snippets → включить `task-statuses`**.

Минимальный вариант может быть таким:

```
/* In progress */
li.task-list-item[data-task="/"] input[type="checkbox"] {
    border-radius: 50%;
    border-width: 2px;
}

/* Waiting / question */
li.task-list-item[data-task="?"] input[type="checkbox"] {
    border-style: dashed;
}

/* Cancelled */
li.task-list-item[data-task="-"] {
    opacity: 0.6;
}

li.task-list-item[data-task="-"] .task-list-item-checkbox {
    text-decoration: line-through;
}
```


- [ ] Todo — подготовить документ
- [/] Doing — сейчас пишу спецификацию
- [~] InProgress — разработка уже начата
- [r] Review — отправлено на проверку
- [v] Checked — результат проверен
- [x] Done — работа завершена
- [w] Waiting — ждём ответ клиента
- [b] Blocked — нет доступа к API
- [<] Scheduling — назначить дату встречи
- [?] Question — уточнить требования
- [!] Important — проверить перед релизом
- [-] Cancelled — задача отменена