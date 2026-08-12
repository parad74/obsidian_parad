# Today

[[Tasks/ToDo|ToDo]] · [[Tasks/InProcess|InProcess]] · [[Tasks/OnHold|OnHold]] · [[Tasks/Cancelled|Cancelled]]

## В работе сейчас

Задачи в состояниях `Doing`, `InProgress`, `Review` и `Checked`.

```tasks
path includes Tasks/Items
status.type is IN_PROGRESS
group by heading
group by status.name
sort by due
sort by path
```

## На сегодня

Все задачи, у которых сегодня дата начала, планирования или срока. Статус не ограничивается.

```tasks
path includes Tasks/Items
happens today
status.type is not ON_HOLD
status.type is not CANCELLED
group by heading
group by status.name
sort by status.type
sort by due
sort by path
```

## Выполнено сегодня

Задачи, переведённые в `Done` сегодня и имеющие дату завершения `✅`.

```tasks
path includes Tasks/Items
done today
group by heading
sort by done reverse
sort by path
```
