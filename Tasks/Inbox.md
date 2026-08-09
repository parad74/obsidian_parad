# Inbox

```tasks
path includes Tasks/Items
not done
status.type is not CANCELLED
group by function "Проект: " + task.file.folder.slice(0, -1).split('/').pop()
group by status.name
sort by due
sort by path
```
