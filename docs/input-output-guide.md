# Input/Output Guide

This guide shows how to read input parameters and write output parameters in your `main.py` task.

## Basic Pattern

All input/output access goes through the `mft` instance passed to your `run()` function:

```python
from mft import MFT

def run(mft: MFT) -> None:
    # Read an input
    name = mft.input.get_string("name")

    # Your logic
    result = f"Hello, {name}!"

    # Write an output
    mft.output.set_string("greeting", result)
```

## Reading Inputs (Getter Methods)

Each parameter type has a corresponding getter that returns a single value, and a list getter that returns a `list`:

| Type | Single getter | Return type | List getter | Return type |
|------|--------------|-------------|-------------|-------------|
| String | `get_string(id)` | `str \| None` | `get_string_list(id)` | `list[str]` |
| Integer | `get_integer(id)` | `int \| None` | `get_integer_list(id)` | `list[int]` |
| Double | `get_double(id)` | `float \| None` | `get_double_list(id)` | `list[float]` |
| Boolean | `get_boolean(id)` | `bool \| None` | `get_boolean_list(id)` | `list[bool]` |
| Date | `get_date(id)` | `datetime.date \| None` | `get_date_list(id)` | `list[datetime.date]` |
| DateTime | `get_datetime(id)` | `datetime.datetime \| None` | `get_datetime_list(id)` | `list[datetime.datetime]` |
| TimeSpan | `get_timespan(id)` | `datetime.timedelta \| None` | `get_timespan_list(id)` | `list[datetime.timedelta]` |
| Guid | `get_guid(id)` | `uuid.UUID \| None` | `get_guid_list(id)` | `list[uuid.UUID]` |
| Enum | `get_enum(id)` | `str \| None` | `get_enum_list(id)` | `list[str]` |
| Binary | `get_binary(id)` | `bytes \| None` | `get_binary_list(id)` | `list[bytes]` |
| Object | `get_object(id)` | `ParameterObjectHandler \| None` | `get_objects(id)` | `Iterator[ParameterObjectHandler]` |

Single getters return `None` if the parameter has no value set. List getters return an empty list.

## Writing Outputs (Setter Methods)

| Type | Single setter | Value type | List setter | Value type |
|------|--------------|------------|-------------|------------|
| String | `set_string(id, value)` | `str` | `set_string_list(id, values)` | `list[str]` |
| Integer | `set_integer(id, value)` | `int` | `set_integer_list(id, values)` | `list[int]` |
| Double | `set_double(id, value)` | `float` | `set_double_list(id, values)` | `list[float]` |
| Boolean | `set_boolean(id, value)` | `bool` | `set_boolean_list(id, values)` | `list[bool]` |
| Date | `set_date(id, value)` | `datetime.date` | `set_date_list(id, values)` | `list[datetime.date]` |
| DateTime | `set_datetime(id, value)` | `datetime.datetime` | `set_datetime_list(id, values)` | `list[datetime.datetime]` |
| TimeSpan | `set_timespan(id, value)` | `datetime.timedelta` | `set_timespan_list(id, values)` | `list[datetime.timedelta]` |
| Guid | `set_guid(id, value)` | `uuid.UUID` | `set_guid_list(id, values)` | `list[uuid.UUID]` |
| Enum | `set_enum(id, value)` | `str` | `set_enum_list(id, values)` | `list[str]` |
| Binary | `set_binary(id, value)` | `bytes` | `set_binary_list(id, values)` | `list[bytes]` |
| Object | `set_object(id, writer)` | `Callable` | `set_object_list(id, writers)` | `list[Callable]` |

Each parameter can only be set once. Setting a parameter that has already been set raises an error.

## Reading Objects

`get_object(id)` returns a `ParameterObjectHandler` — a nested handler you can call the same getter methods on:

```python
config = mft.input.get_object("config")
enabled = config.get_boolean("enabled")
threshold = config.get_double("threshold")
run_date = config.get_date("run_date")
```

## Reading Object Lists

Use `get_objects(id)` to iterate over a list of objects:

```python
for item in mft.input.get_objects("items"):
    name = item.get_string("name")
    score = item.get_double("score")
    tags = list(item.get_string_list("tags"))
    print(f"{name}: {score}, tags={tags}")
```

## Writing Objects

Use `set_object(id, writer)` with a callback function. The callback receives a `ParameterObjectHandler` and sets fields on it:

```python
def write_stats(stats):
    stats.set_integer("total_count", 42)
    stats.set_double("avg_score", 3.14)
    stats.set_string_list("all_tags", ["alpha", "beta"])

mft.output.set_object("stats", write_stats)
```

## Writing Object Lists

Use `set_object_list(id, writers)` with a list of callback functions — one per object. Use a closure factory to capture per-item data:

```python
def make_writer(name, value):
    def writer(obj):
        obj.set_string("name", name)
        obj.set_double("score", value)
    return writer

writers = [
    make_writer("Alice", 9.5),
    make_writer("Bob", 7.2),
]
mft.output.set_object_list("results", writers)
```

## Deeply Nested Objects

Chain `get_object()` calls to traverse nested structures:

```python
for item in mft.input.get_objects("items"):
    address = item.get_object("address")
    street = address.get_string("street")
    city = address.get_string("city")
    zip_code = address.get_integer("zip_code")
```

For writing, nest callbacks:

```python
def write_item(item):
    item.set_string("name", "Alice")
    item.set_double("score", 9.5)
    item.set_object("address", lambda addr: (
        addr.set_string("street", "123 Main St"),
        addr.set_string("city", "Springfield"),
        addr.set_integer("zip_code", 62701),
    ))

mft.output.set_object_list("items", [write_item])
```

> **Note:** The lambda body uses a tuple expression `(a, b, c)` to execute multiple setter calls in one expression. Alternatively, define a named function like the closure factory pattern above.

## Using the Tableau API

To use the Tableau Server REST API, add `"RestApi"` to the `uses` array in your `task-meta.json`:

```json
{ "uses": ["RestApi"] }
```

Then access the connected [Tableau Server Client](https://tableau.github.io/server-client-python/) via `mft.tableau_api`:

```python
def run(mft: MFT) -> None:
    server = mft.tableau_api.server

    # Example: list all projects
    all_projects, pagination = server.projects.get()
    for project in all_projects:
        print(f"{project.name} ({project.id})")
```

The `server` object is a fully authenticated `tableauserverclient.Server` instance. MFT handles authentication and cleanup automatically.

## Using the Repository

To query the Tableau Server PostgreSQL repository, add `"Repository"` to `uses`:

```json
{ "uses": ["Repository"] }
```

Then use `mft.repository`:

```python
def run(mft: MFT) -> None:
    # execute() returns a list of tuples
    rows = mft.repository.execute(
        "SELECT id, name FROM public.projects WHERE name LIKE %s",
        ("Data%",)
    )
    for row in rows:
        print(f"ID: {row[0]}, Name: {row[1]}")

    # execute_dict() returns a list of dicts
    rows = mft.repository.execute_dict(
        "SELECT id, name FROM public.projects"
    )
    for row in rows:
        print(f"ID: {row['id']}, Name: {row['name']}")
```

The repository connection is read-only. MFT handles connection setup and cleanup.

## Complete Example

A full `main.py` that reads a list of items with nested addresses, reads configuration, and writes summary output:

```python
from mft import MFT


def run(mft: MFT) -> None:
    # Read config (single Object)
    config = mft.input.get_object("config")
    enabled = config.get_boolean("enabled")
    threshold = config.get_double("threshold")
    run_date = config.get_date("run_date")

    # Read items (Object list with nested address)
    all_names = []
    all_tags = []
    total_score = 0.0
    item_count = 0

    for item in mft.input.get_objects("items"):
        name = item.get_string("name")
        score = item.get_double("score")
        tags = list(item.get_string_list("tags"))

        # Nested object
        address = item.get_object("address")
        city = address.get_string("city")

        all_names.append(name)
        all_tags.extend(tags)
        total_score += score
        item_count += 1

    avg_score = total_score / item_count if item_count > 0 else 0.0

    # Write simple outputs
    summary = f"Processed {item_count} items on {run_date}"
    mft.output.set_string("summary", summary)
    mft.output.set_string_list("processed_names", all_names)

    # Write nested output object
    def write_stats(stats):
        stats.set_integer("total_count", item_count)
        stats.set_double("avg_score", round(avg_score, 2))
        stats.set_string_list("all_tags", all_tags)

    mft.output.set_object("stats", write_stats)


# --- Boilerplate (do not modify) ---
if __name__ == "__main__":
    task = MFT.init()
    try:
        run(task)
        MFT.Ok()
    except Exception as e:
        MFT.Err(str(e))
```
