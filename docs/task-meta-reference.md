# Task Metadata Reference

The `src/task-meta.json` file defines your custom task — its name, inputs, outputs, and what services it needs. Manager for Tableau reads this file to build the UI and wire up parameters at runtime.

## Minimal Example

The simplest valid `task-meta.json` has a display name and at least one input or output:

```json
{
  "display_name": "Hello World",
  "inputs": [
    {
      "id": "name",
      "display_name": "Name",
      "type": "String",
      "is_list": false,
      "required": true
    }
  ],
  "outputs": []
}
```

## Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `display_name` | string | Yes | Name shown in the task list UI. |
| `description` | string | No | Short description of what the task does. |
| `group` | string | No | Group name for organizing tasks in the UI. |
| `group_index` | integer/null | No | Sort order within the group (lower = higher). Default: `null`. |
| `major_version` | integer | No | Task version number. Increment when changing inputs/outputs. Default: `1`. |
| `version_description` | string/null | No | Description of changes in this version (changelog). Default: `null`. |
| `uses` | string[] | No | Service dependencies — see below. |
| `inputs` | parameter[] | No | Input parameters the user fills in before running. |
| `outputs` | parameter[] | No | Output parameters the task produces. |

## Versioning

Custom tasks support versioning. When you upload a new version of your task to Manager for Tableau, it is stored alongside previous versions. Workflows that already reference an older version continue to use it, while new or updated workflows can use the new version.

### How versioning works

1. **Initial release** — your first upload has `major_version: 1`. You can omit it (defaults to `1`).
2. **Updating inputs/outputs** — when you change the `inputs` or `outputs` of your task (add, remove, or change parameter types), increment `major_version` in `task-meta.json`. This creates a new version alongside the existing one.
3. **Version description** — use `version_description` to document what changed in this version. This is shown in the UI as a changelog.
4. **Bug fixes** — if you fix a bug in your task logic without changing the inputs/outputs schema, you can re-upload with the same `major_version`. The new code replaces the old code for that version.

### When to increment `major_version`

| Change | Increment version? |
|--------|--------------------|
| Fix a bug in `main.py` logic | No — same version |
| Change a parameter's `description` or `display_name` | No — same version |
| Add a new input or output parameter | **Yes** |
| Remove an input or output parameter | **Yes** |
| Change a parameter's `type` (e.g. String to Integer) | **Yes** |
| Change `is_list` on a parameter | **Yes** |
| Add/remove/change `enum_values` | **Yes** |
| Change `object_properties` on an Object parameter | **Yes** |

### Example

Version 1 — initial release:
```json
{
  "display_name": "My Task",
  "major_version": 1,
  "inputs": [
    {"id": "name", "display_name": "Name", "type": "String", "is_list": false, "required": true}
  ],
  "outputs": [
    {"id": "result", "display_name": "Result", "type": "String", "is_list": false}
  ]
}
```

Version 2 — added a new output parameter:
```json
{
  "display_name": "My Task",
  "major_version": 2,
  "version_description": "Added processedCount output",
  "inputs": [
    {"id": "name", "display_name": "Name", "type": "String", "is_list": false, "required": true}
  ],
  "outputs": [
    {"id": "result", "display_name": "Result", "type": "String", "is_list": false},
    {"id": "processedCount", "display_name": "Processed Count", "type": "Integer", "is_list": false}
  ]
}
```

Workflows using version 1 continue to work unchanged. New workflows can choose version 2 to use the new `processedCount` output.

## Service Dependencies (`uses`)

The `uses` array declares which MFT services your task needs. If omitted or empty, no external services are connected.

| Value | What it enables |
|-------|-----------------|
| `"RestApi"` | `mft.tableau_api` — a connected Tableau Server Client (`TSC`) instance authenticated via Personal Access Token. |
| `"Repository"` | `mft.repository` — a read-only PostgreSQL connection to the Tableau Server repository database. |

```json
{
  "uses": ["RestApi", "Repository"]
}
```

## Parameter Fields

Each entry in `inputs` or `outputs` is a parameter object:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier. Must match `^[a-zA-Z][a-zA-Z\d_]*$` (letters, digits, underscores; cannot start with a digit or underscore). |
| `display_name` | string | Yes | Label shown in the UI. |
| `type` | string | Yes | One of the 11 parameter types listed below. |
| `description` | string | No | Help text shown to the user. |
| `required` | boolean | No | If `true`, the parameter must have a value. Defaults to `false`. |
| `is_list` | boolean | No | If `true`, the parameter accepts multiple values. Defaults to `false`. |
| `enum_values` | string[] | Enum only | List of allowed values. Required when `type` is `"Enum"`. |
| `object_properties` | parameter[] | Object only | Nested parameter definitions. Required when `type` is `"Object"`. |

## Parameter Types

| Type | JSON value example | Python type |
|------|-------------------|-------------|
| `String` | `"hello"` | `str` |
| `Integer` | `42` | `int` |
| `Double` | `3.14` | `float` |
| `Boolean` | `true` | `bool` |
| `Date` | `"2024-06-15"` | `datetime.date` |
| `DateTime` | `"2024-06-15T10:30:00"` | `datetime.datetime` |
| `TimeSpan` | `"01:30:00"` | `datetime.timedelta` |
| `Guid` | `"550e8400-e29b-41d4-a716-446655440000"` | `uuid.UUID` |
| `Enum` | `"Info"` | `str` (must match an `enum_values` entry) |
| `Binary` | *(base64 string)* | `bytes` |
| `Object` | `{...}` | `ParameterObjectHandler` (see below) |

## Enum Parameters

When `type` is `"Enum"`, you must provide `enum_values`:

```json
{
  "id": "logLevel",
  "display_name": "Log Level",
  "type": "Enum",
  "enum_values": ["Debug", "Info", "Warning", "Error"]
}
```

The value comparison is case-insensitive, but the stored value preserves the case the user provides.

## Object Parameters

When `type` is `"Object"`, you must provide `object_properties` — a list of parameters that define the object's fields:

```json
{
  "id": "config",
  "display_name": "Configuration",
  "type": "Object",
  "is_list": false,
  "object_properties": [
    {"id": "enabled", "display_name": "Enabled", "type": "Boolean", "is_list": false},
    {"id": "threshold", "display_name": "Threshold", "type": "Double", "is_list": false}
  ]
}
```

## List Parameters

Set `is_list` to `true` to accept multiple values. This works with any type, including Object:

```json
{
  "id": "tags",
  "display_name": "Tags",
  "type": "String",
  "is_list": true
}
```

```json
{
  "id": "items",
  "display_name": "Items",
  "type": "Object",
  "is_list": true,
  "object_properties": [
    {"id": "name", "display_name": "Name", "type": "String", "is_list": false, "required": true},
    {"id": "score", "display_name": "Score", "type": "Double", "is_list": false}
  ]
}
```

## Nested Objects

Objects can contain other objects. Here is a 2-level nesting example — an item list where each item has an address object:

```json
{
  "id": "items",
  "display_name": "Items",
  "type": "Object",
  "is_list": true,
  "object_properties": [
    {
      "id": "name",
      "display_name": "Name",
      "type": "String",
      "is_list": false,
      "required": true
    },
    {
      "id": "tags",
      "display_name": "Tags",
      "type": "String",
      "is_list": true
    },
    {
      "id": "address",
      "display_name": "Address",
      "type": "Object",
      "is_list": false,
      "object_properties": [
        {"id": "street", "display_name": "Street", "type": "String", "is_list": false},
        {"id": "city", "display_name": "City", "type": "String", "is_list": false},
        {"id": "zip_code", "display_name": "Zip Code", "type": "Integer", "is_list": false}
      ]
    }
  ]
}
```

## Complete Real-World Example

A task that processes a list of items with nested addresses, a configuration object, and produces summary output with statistics:

```json
{
  "display_name": "Process Items",
  "description": "Reads items with addresses, filters by threshold, outputs statistics",
  "group": "Data Tools",
  "group_index": null,
  "major_version": 1,
  "version_description": null,
  "uses": ["RestApi"],
  "inputs": [
    {
      "id": "items",
      "display_name": "Items",
      "type": "Object",
      "is_list": true,
      "object_properties": [
        {"id": "name", "display_name": "Name", "type": "String", "is_list": false, "required": true},
        {"id": "score", "display_name": "Score", "type": "Double", "is_list": false},
        {"id": "tags", "display_name": "Tags", "type": "String", "is_list": true},
        {
          "id": "address",
          "display_name": "Address",
          "type": "Object",
          "is_list": false,
          "object_properties": [
            {"id": "street", "display_name": "Street", "type": "String", "is_list": false},
            {"id": "city", "display_name": "City", "type": "String", "is_list": false},
            {"id": "zip_code", "display_name": "Zip Code", "type": "Integer", "is_list": false}
          ]
        }
      ]
    },
    {
      "id": "config",
      "display_name": "Configuration",
      "type": "Object",
      "is_list": false,
      "object_properties": [
        {"id": "enabled", "display_name": "Enabled", "type": "Boolean", "is_list": false},
        {"id": "threshold", "display_name": "Threshold", "type": "Double", "is_list": false},
        {"id": "run_date", "display_name": "Run Date", "type": "Date", "is_list": false}
      ]
    },
    {
      "id": "logLevel",
      "display_name": "Log Level",
      "type": "Enum",
      "enum_values": ["Debug", "Info", "Warning", "Error"]
    }
  ],
  "outputs": [
    {"id": "summary", "display_name": "Summary", "type": "String", "is_list": false},
    {"id": "processed_names", "display_name": "Processed Names", "type": "String", "is_list": true},
    {
      "id": "stats",
      "display_name": "Statistics",
      "type": "Object",
      "is_list": false,
      "object_properties": [
        {"id": "total_count", "display_name": "Total Count", "type": "Integer", "is_list": false},
        {"id": "avg_score", "display_name": "Average Score", "type": "Double", "is_list": false},
        {"id": "all_tags", "display_name": "All Tags", "type": "String", "is_list": true}
      ]
    }
  ]
}
```

See [input-output-guide.md](input-output-guide.md) for how to read and write these parameters in Python.
