---
type: architecture
platform: WinForms
runtime_family: DotNetFramework
target_framework: net461
---

# WinForms - View - Presenter - DIUnity - IModule

## Краткое описание

Архитектура небольшого WinForms-приложения на .NET Framework 4.6.1. Форма реализует интерфейс View, получает Presenter через Unity и передаёт ему себя. Общие проекты View и Presenter подключаются как модули `IModule`. Решение предназначено в том числе для небольших тестовых и вспомогательных программ.

## Когда использовать

- Нужно создать или развивать WinForms-приложение на .NET Framework 4.6.1.
- Требуется визуальный WinForms Designer.
- Нужно сохранить совместимость с Unity и модульной инициализацией `IModule`.
- Важно быстро получить небольшое приложение с явно разделёнными View и Presenter.

## Технологии

- .NET Framework 4.6.1.
- Windows Forms.
- Unity: `Microsoft.Practices.Unity`.
- Модули: `Microsoft.Practices.Composite.Modularity.IModule`.
- Паттерн View–Presenter.
- Обязательное логирование через `ILog`, `LogImport` и операции сообщений.

## Состав solution

- `Main` — точка входа, `Form1`, `IMainView`, `MainPresenter`, прикладные сервисы и composition root.
- `Common.View` — базовый `IView` и модуль инициализации View, реализующий `IModule`.
- `Common.Presenter` — `IPresenter<T>`, `BasePresenter<T>` и модуль инициализации Presenter, реализующий `IModule`.
- `Common.MessageOperation` — `ILog`, `LogImport`, `LogMessage`, `LogMessages`, `LogMessageOperation` и связанные типы сообщений.
- `Lib` — все сторонние DLL, необходимые для сборки проекта.

Точное распределение дополнительных прикладных интерфейсов и сервисов определяется требованиями создаваемого приложения.

## Обязательные правила

1. Первая пара всегда называется `Form1 : Form, IMainView` и `MainPresenter`.
2. `Form1` получает `IMainPresenter` через конструктор.
3. В конструкторе форма устанавливает `presenter.View = this`.
4. Обработчики событий элементов формы вызывают операции Presenter.
5. `MainPresenter` наследуется от `BasePresenter<IMainView>` и работает с формой через `IMainView`.
6. `Program.Main` является composition root: настраивает модули, регистрирует зависимости в Unity, получает `IMainView` из контейнера и передаёт форму в `Application.Run`.
7. Логирование через `Common.MessageOperation` присутствует всегда.
8. Папка `Lib` присутствует всегда и содержит используемые сторонние DLL.
9. Дополнительная пара View–Presenter может быть отдельной формой или `UserControl`, размещённым непосредственно на форме либо внутри `TabPage`.
10. Все объявления `public interface` находятся в папке `Interface/` соответствующего проекта.
11. Реализации `IView` и производных интерфейсов находятся в папке `View/`, а реализации `IPresenter` и производных интерфейсов — в папке `Presenter/` соответствующего проекта.
12. Только в коде пользователя, который создаётся или изменяется в рамках проекта, для написанных вручную закрытых полей используется имя `_camelCase`, а при обращении к члену текущего экземпляра — явный префикс `this.`, например `this._log`. При обращении из производного класса к члену базового класса используется префикс `base.`, например `base.RequireView()`.
13. Исполняемый WinForms-проект содержит подключённый `app.manifest` с режимом System DPI Aware. Формы используют `AutoScaleMode.Dpi` с базовым значением 96 DPI, чтобы Windows не растягивала интерфейс как не-DPI-aware изображение.

## DPI и масштабирование

Для .NET Framework 4.6.1 используется системная DPI-awareness:

```xml
<dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true</dpiAware>
<dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">system</dpiAwareness>
```

- Manifest подключается в исполняемом `.csproj` через `ApplicationManifest`.
- Для формы задаются `AutoScaleMode.Dpi` и проектное значение `AutoScaleDimensions = 96F, 96F`.
- `PerMonitorV2` не считается правилом этой архитектуры, поскольку расширенная динамическая поддержка High DPI в WinForms относится к .NET Framework 4.7 и новее.
- После создания формы масштабирование проверяется на фактическом масштабе Windows пользователя, например 125%.

## Стиль доступа к членам класса

```csharp
private readonly ILog _log;

public MainPresenter(ILog log)
{
    this._log = log;
}

public void Save()
{
    IMainView view = base.RequireView();
    this._log.Add(LogMessageType.Information, "Текст сохранён.");
}
```

- Параметры методов и локальные переменные не получают префикс `_`.
- `this.` используется для полей и свойств текущего экземпляра, когда к ним обращается написанный вручную код.
- `base.` используется для доступных членов базового класса из производного класса.
- Правило не применяется к `*.Designer.cs`, автоматически сгенерированным файлам, сторонним библиотекам и неизменяемому коду старых проектов.

## Минимальный демонстрационный сценарий

На `Form1` создаются:

- одно текстовое поле;
- кнопка `Save`;
- кнопка `Clear`.

`MainPresenter` хранит введённый текст во внутренней переменной. `Save` переносит значение из View в переменную, `Clear` очищает сохранённое значение и поле. Обе операции записываются в `ILog`. Сценарий нужен для наглядной проверки взаимодействия Form, View, Presenter и логирования.

## Совместимые кубики

- [[Documents/Architectures/Cubes/DotNetFramework/Service - DIUnity]] — переносит хранение текста и операции `Save`/`Clear` из Presenter в отдельный проект `Common.Service`, подключаемый через Unity.

## Несколько View–Presenter

Для каждой дополнительной пары определяются:

- название View и Presenter;
- форма или `UserControl`;
- размещение непосредственно на форме или в конкретной вкладке;
- поля и отображаемые значения;
- кнопки и другие элементы управления;
- события View;
- операции Presenter.

## Вопросы перед созданием

1. Сколько пар View–Presenter требуется?
2. Сколько вкладок `TabControl` требуется и как они называются?
3. Какая пара View–Presenter находится на каждой вкладке или непосредственно на форме?
4. Какие поля нужно добавить в каждый View?
5. Какие кнопки и другие элементы управления нужны?
6. Какие пользовательские события и действия должны поддерживаться?
7. Какие прикладные сервисы и внешние зависимости нужно зарегистрировать?

Версию .NET и DI-контейнер для этой архитектуры не спрашивать: они зафиксированы названием решения.

## Источник и эталон

- Проект-источник: `Sources/old/PreTestWCF/`.
- Composition root: `Sources/old/PreTestWCF/Main/Program.cs`.
- Пример связи формы с Presenter: `Sources/old/PreTestWCF/Main/View/Form1.cs`.
- Базовый Presenter: `Sources/old/PreTestWCF/Common.Presenter/Interface/IPresenter.cs`.
- Исходное логирование: `Sources/old/PreTestWCF/Model/Log/`.
- Проверенная эталонная реализация: `Sources/Architectures/WinForms/DotNetFramework/WinForms.NETFramework.App1/`.
- Solution: `Sources/Architectures/WinForms/DotNetFramework/WinForms.NETFramework.App1/WinForms.NETFramework.App1.sln`.

Проект-источник используется для исследования и не изменяется при создании эталона.

## Проверка эталона

11 августа 2026 года эталон:

- успешно пересобран MSBuild 17.14 для .NET Framework 4.6.1 в конфигурациях `Debug` и `Release`;
- инициализировал `CommonViewModule` и `CommonPresenterModule`;
- создал `Form1` и `MainPresenter` через Unity;
- установил связь `MainPresenter.View` с тем же экземпляром `Form1`;
- выполнил `Save` и `Clear` через Presenter;
- добавил по одному сообщению в `ILog` для каждой операции.
