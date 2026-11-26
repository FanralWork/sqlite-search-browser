# SQLite Search Browser

A Tkinter desktop prototype for searching local SQLite databases and inspecting matching rows.

## Features

- Scans a selected directory for `.db`, `.sqlite`, and `.sqlite3` files.
- Searches the selected database scope or all listed databases.
- Displays tables and matching records and saves search preferences in `browser_settings.json`.

## Stack and architecture

`sqlite_search.py` contains the Tkinter interface and its SQLite access. The app enumerates tables and columns, searches them with the standard-library `sqlite3` module, and renders row details in Tkinter views.

## Setup and usage

Use Python with Tkinter installed. The app has no third-party Python packages.

```sh
python sqlite_search.py
```

On the database tab, select a folder of disposable test databases. On the search tab, enter one or more space-separated terms, choose exact or partial matching, and run the search. Double-click a result to inspect its stored row details. The interface is in Russian.

## Status and limitations

This prototype can write changes to SQLite. Use copies of test databases. Inline edits assume that the first column uniquely identifies a row. Several row or column management controls are placeholders and may display a success dialog. Searches run on the UI thread and rely on SQLite `ROWID` and identifier handling that can skip some schemas. Partial search follows SQLite's `LIKE` behavior. The settings file stores local database paths.

## Кратко для портфолио

Прототип настольного обозревателя нескольких локальных баз SQLite с поиском по таблицам и просмотром найденных строк. Редактирование требует доработки.
