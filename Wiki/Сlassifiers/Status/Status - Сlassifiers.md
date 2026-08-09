[ ] => [~], name: 'Todo', type: 'TODO'
[x] => [ ], name: 'Done', type: 'DONE'
[-] → [ ]   Cancelled    CANCELLED
[!] → [/]   Important    TODO
[w] → [/]   Waiting      ON_HOLD
[?] → [/]   Question     ON_HOLD
[v] → [x]   Checked      IN_PROGRESS
[~] → [/]   InProgress   IN_PROGRESS
[r] → [v]   Review       IN_PROGRESS
[/] → [r]   Doing        IN_PROGRESS
[b] → [/]   Blocked      ON_HOLD
[<] → [ ]   Scheduling   ON_HOLD


Боковые состояния возвращаются разумно:
InProgress [~] ──→ Doing [/]
Waiting    [w] ──→ Doing [/]
Blocked    [b] ──→ Doing [/]
Question   [?] ──→ Doing [/]
Important  [!] ──→ Doing [/]

Scheduling [<] ──→ Todo [ ]
Cancelled  [-] ──→ Todo [ ]


Нормальный жизненный цикл задачи:

```
[ ] Todo
    ↓
[~] InProgress
    ↓
[/] Doing
    ↓
[r] Review
    ↓
[v] Checked
    ↓
[x] Done
```

