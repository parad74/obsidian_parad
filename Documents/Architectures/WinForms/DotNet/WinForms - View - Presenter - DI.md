---
type: architecture
platform: WinForms
runtime_family: DotNet
target_framework: ask-before-generation
di_container: ask-before-generation
---

# WinForms - View - Presenter - DI

## Краткое описание

Современная архитектура WinForms на выбираемой версии .NET. View реализуется формой или `UserControl`, публикует события и ничего не знает о Presenter. Presenter получает интерфейс View через конструктор, подписывается на события и управляет поведением приложения. Конкретный DI-контейнер выбирается перед созданием проекта.

## Когда использовать

- Создаётся новое WinForms-приложение на современном .NET.
- Требуется визуальный WinForms Designer.
- Нужна слабая связанность View и Presenter.
- Архитектура должна поддерживать несколько независимых пар View–Presenter и вкладки.

## Технологии

- Современный .NET с Windows-целевой платформой, например `net8.0-windows` или `net9.0-windows` для совместимых версий Visual Studio 2022.
- Windows Forms.
- Выбираемый DI-контейнер.
- Паттерн View–Presenter с событиями View.
- Обязательный проект `Common.MessageOperation` с `ILog`, `LogImport`, `LogMessageOperation` и связанными типами.

## Базовый состав solution

- `Main` — точка входа, composition root и первая пара View–Presenter.
- `Common.View` — общие контракты View, если они нужны нескольким парам.
- `Common.Presenter` — общие контракты или базовые элементы Presenter, если они действительно переиспользуются.
- `Common.MessageOperation` — обязательное логирование.
- Дополнительные проекты создаются только при наличии прикладной необходимости.

## Обязательные правила

1. Первая пара всегда называется `Form1 : Form, IMainView` и `MainPresenter`.
2. `Form1` реализует `IMainView` и публикует события пользовательских действий.
3. `Form1` не принимает, не хранит и не вызывает `MainPresenter`.
4. `MainPresenter` получает `IMainView` и `ILog` через конструктор.
5. `MainPresenter` подписывается на события View и изменяет View только через `IMainView`.
6. Composition root использует согласованные экземпляры View и Presenter, активирует подписки Presenter и запускает тот же экземпляр `Form1`, который передан в `MainPresenter` как `IMainView`.
7. Логирование через `Common.MessageOperation` присутствует всегда.
8. Дополнительная пара View–Presenter может быть отдельной формой или `UserControl`, размещённым непосредственно на форме либо внутри `TabPage`.
9. WinForms Designer не должен зависеть от запуска DI-контейнера или прикладных сервисов.
10. Все объявления `public interface` находятся в папке `Interface/` соответствующего проекта.
11. Реализации `IView` и производных интерфейсов находятся в папке `View/`, а реализации `IPresenter` и производных интерфейсов — в папке `Presenter/` соответствующего проекта.

## Минимальный демонстрационный сценарий

На `Form1` создаются:

- одно текстовое поле;
- кнопка `Save`;
- кнопка `Clear`.

`IMainView` публикует события `SaveRequested` и `ClearRequested` и предоставляет значение текстового поля через свой контракт. `MainPresenter` хранит текст во внутренней переменной. При `SaveRequested` он сохраняет текущее значение, при `ClearRequested` очищает переменную и поле. Обе операции записываются в `ILog`.

## Несколько View–Presenter

Для первой пары используется `Form1` и `MainPresenter`. Для каждой дополнительной пары по умолчанию создаются отдельные `UserControl`, интерфейс View и Presenter. Размещение определяется конфигурацией проекта:

- непосредственно на `Form1`;
- внутри отдельной `TabPage`;
- как отдельная форма, если это требуется сценарием.

Каждый Presenter взаимодействует только со своим View и явно переданными сервисами.

## Вопросы перед созданием

1. Какая версия Visual Studio используется?
2. Какую версию .NET и целевой framework выбрать?
3. Какой DI-контейнер использовать?
4. Сколько пар View–Presenter требуется?
5. Сколько вкладок `TabControl` требуется и как они называются?
6. Какая пара View–Presenter находится на каждой вкладке или непосредственно на форме?
7. Какие поля нужно добавить в каждый View?
8. Какие кнопки и другие элементы управления нужны?
9. Какие события должен публиковать каждый View?
10. Какие операции должны выполнять Presenter?
11. Какие прикладные сервисы и внешние зависимости нужны?

Если версия Visual Studio, .NET или DI уже явно названа пользователем, повторно не спрашивать.

## Источник и эталон

- Концептуальный источник для выделения решения: `Sources/old/PreTestWCF/`.
- Пример исходного логирования: `Sources/old/PreTestWCF/Model/Log/`.
- Эталонная реализация: `Sources/Architectures/WinForms/DotNet/WinForms.dotnet.App1/`.

Современная эталонная реализация создана отдельно и не изменяет проект-источник или решения из `WinForms/DotNetFramework/`.

## Проверенная конфигурация эталона

- Solution: `WinForms.dotnet.App1.sln`.
- Visual Studio 2022 17.14.
- .NET 8, `net8.0-windows`; SDK 8.0.404 закреплён в `global.json`.
- Стандартный DI: `Microsoft.Extensions.DependencyInjection` 8.0.0 и простой `ServiceCollection` без Generic Host.
- Проекты: `Main`, `Common.View`, `Common.Presenter`, `Common.MessageOperation`.
- Одна пара `Form1 : Form, IMainView` и `MainPresenter`, без вкладок.
- Одно поле, кнопки `Save` и `Clear`, события `SaveRequested` и `ClearRequested`.
- DPI-режим `PerMonitorV2`.
- NuGet-зависимости подключаются через `PackageReference` и фиксируются в `packages.lock.json`; папка `Lib` не используется.
- Проверены Debug- и Release-сборки без предупреждений, запуск приложения, события View, обработка Presenter, общий экземпляр View в DI и запись операций в `ILog`.
