# Examples

Complete examples showing how to build custom tasks with the MFT framework. Each example includes both the `task-meta.json` definition and the `main.py` implementation.

For the full API reference, see [task-meta-reference.md](task-meta-reference.md) and [input-output-guide.md](input-output-guide.md).

## Example 1: Simple String Processing

A task that takes a name and greeting style, and produces a formatted greeting.

**`src/task-meta.json`**:
```json
{
  "display_name": "Greeting Generator",
  "description": "Generates a formatted greeting message",
  "group": "Custom Tasks",
  "group_index": null,
  "uses": [],
  "inputs": [
    {
      "id": "name",
      "display_name": "Name",
      "type": "String",
      "required": true,
      "is_list": false
    },
    {
      "id": "style",
      "display_name": "Greeting Style",
      "type": "Enum",
      "enum_values": ["Formal", "Casual", "Enthusiastic"],
      "is_list": false
    }
  ],
  "outputs": [
    {
      "id": "greeting",
      "display_name": "Greeting",
      "type": "String",
      "is_list": false
    }
  ]
}
```

**`main.py`**:
```python
from mft import MFT


def run(mft: MFT) -> None:
    name = mft.input.get_string("name")
    style = mft.input.get_enum("style") or "Casual"

    if style == "Formal":
        greeting = f"Dear {name}, it is a pleasure to address you."
    elif style == "Enthusiastic":
        greeting = f"Hey {name}!! Great to see you!!!"
    else:
        greeting = f"Hi {name}, how are you?"

    mft.output.set_string("greeting", greeting)


# --- Boilerplate (do not modify) ---
if __name__ == "__main__":
    try:
        task = MFT.init()
    except Exception as e:
        MFT.Err(str(e), error_id="InitError")
    try:
        run(task)
        MFT.Ok()
    except Exception as e:
        MFT.Err(str(e))
```

## Example 2: Tableau API — Export Workbook List

A task that queries the Tableau REST API and exports workbook information.

**`src/task-meta.json`**:
```json
{
  "display_name": "Export Workbook List",
  "description": "Lists all workbooks on the Tableau site with owner and project info",
  "group": "Tableau Reports",
  "group_index": null,
  "uses": ["RestApi"],
  "inputs": [
    {
      "id": "projectFilter",
      "display_name": "Project Name Filter",
      "type": "String",
      "description": "Only include workbooks in this project (leave empty for all)",
      "required": false,
      "is_list": false
    }
  ],
  "outputs": [
    {
      "id": "workbookCount",
      "display_name": "Workbook Count",
      "type": "Integer",
      "is_list": false
    },
    {
      "id": "workbookNames",
      "display_name": "Workbook Names",
      "type": "String",
      "is_list": true
    }
  ]
}
```

**`main.py`**:
```python
from mft import MFT


def run(mft: MFT) -> None:
    project_filter = mft.input.get_string("projectFilter")
    server = mft.tableau_api.server

    all_workbooks, _ = server.workbooks.get()

    if project_filter:
        all_workbooks = [wb for wb in all_workbooks if wb.project_name == project_filter]

    names = [wb.name for wb in all_workbooks]

    mft.output.set_integer("workbookCount", len(names))
    mft.output.set_string_list("workbookNames", names)


# --- Boilerplate (do not modify) ---
if __name__ == "__main__":
    try:
        task = MFT.init()
    except Exception as e:
        MFT.Err(str(e), error_id="InitError")
    try:
        run(task)
        MFT.Ok()
    except Exception as e:
        MFT.Err(str(e))
```

## Example 3: Repository Query — Stale Content Report (Over Simplified)

A task that queries the Tableau Repository to find workbooks not viewed recently.

**`src/task-meta.json`**:
```json
{
  "display_name": "Stale Content Report",
  "description": "Finds workbooks not viewed in the last N days",
  "group": "Tableau Reports",
  "group_index": null,
  "major_version": 1,
  "uses": ["Repository"],
  "inputs": [
    {
      "id": "staleDays",
      "display_name": "Days Since Last View",
      "type": "Integer",
      "description": "Number of days without a view to consider a workbook stale",
      "required": true,
      "is_list": false
    }
  ],
  "outputs": [
    {
      "id": "staleCount",
      "display_name": "Stale Workbook Count",
      "type": "Integer",
      "is_list": false
    },
    {
      "id": "staleWorkbooks",
      "display_name": "Stale Workbooks",
      "type": "Object",
      "is_list": true,
      "object_properties": [
        { "id": "name", "display_name": "Name", "type": "String", "is_list": false },
        { "id": "project", "display_name": "Project", "type": "String", "is_list": false },
        { "id": "lastViewed", "display_name": "Last Viewed", "type": "DateTime", "is_list": false }
      ]
    }
  ]
}
```

**`main.py`**:
```python
from datetime import datetime, timedelta
from mft import MFT


def run(mft: MFT) -> None:
    stale_days = mft.input.get_integer("staleDays")
    cutoff = datetime.now() - timedelta(days=stale_days)

    rows = mft.repository.execute_dict(
        """
        SELECT w.name, p.name AS project_name, v.last_view_time
        FROM workbooks w
        JOIN projects p ON w.project_id = p.id
        LEFT JOIN most_recent_view_for_workbooks v ON w.id = v.workbook_id
        WHERE v.last_view_time IS NULL OR v.last_view_time < %s
        ORDER BY v.last_view_time ASC NULLS FIRST
        """,
        (cutoff,),
    )

    mft.output.set_integer("staleCount", len(rows))

    writers = []
    for row in rows:
        def make_writer(r):
            def writer(obj):
                obj.set_string("name", r["name"])
                obj.set_string("project", r["project_name"])
                if r["last_view_time"]:
                    obj.set_datetime("lastViewed", r["last_view_time"])
            return writer
        writers.append(make_writer(row))

    mft.output.set_object_list("staleWorkbooks", writers)


# --- Boilerplate (do not modify) ---
if __name__ == "__main__":
    try:
        task = MFT.init()
    except Exception as e:
        MFT.Err(str(e), error_id="InitError")
    try:
        run(task)
        MFT.Ok()
    except Exception as e:
        MFT.Err(str(e))
```

## Example 4: Working with Nested Objects

A task that processes configuration with deeply nested structures.

**`src/task-meta.json`** (inputs only, abbreviated):
```json
{
  "display_name": "Process Orders",
  "uses": [],
  "inputs": [
    {
      "id": "orders",
      "display_name": "Orders",
      "type": "Object",
      "is_list": true,
      "object_properties": [
        { "id": "orderId", "display_name": "Order ID", "type": "Guid", "is_list": false, "required": true },
        { "id": "amount", "display_name": "Amount", "type": "Double", "is_list": false },
        { "id": "orderDate", "display_name": "Order Date", "type": "Date", "is_list": false },
        { "id": "tags", "display_name": "Tags", "type": "String", "is_list": true },
        {
          "id": "shippingAddress",
          "display_name": "Shipping Address",
          "type": "Object",
          "is_list": false,
          "object_properties": [
            { "id": "street", "display_name": "Street", "type": "String", "is_list": false },
            { "id": "city", "display_name": "City", "type": "String", "is_list": false },
            { "id": "zip", "display_name": "ZIP", "type": "String", "is_list": false }
          ]
        }
      ]
    }
  ],
  "outputs": [
    { "id": "totalAmount", "display_name": "Total Amount", "type": "Double", "is_list": false },
    { "id": "cities", "display_name": "Unique Cities", "type": "String", "is_list": true }
  ]
}
```

**`main.py`**:
```python
from mft import MFT


def run(mft: MFT) -> None:
    total = 0.0
    cities = set()

    for order in mft.input.get_objects("orders"):
        order_id = order.get_guid("orderId")
        amount = order.get_double("amount") or 0.0
        order_date = order.get_date("orderDate")
        tags = list(order.get_string_list("tags"))

        # Read nested object
        address = order.get_object("shippingAddress")
        if address:
            city = address.get_string("city")
            if city:
                cities.add(city)

        total += amount
        print(f"Order {order_id}: ${amount:.2f} on {order_date}, tags={tags}")

    mft.output.set_double("totalAmount", round(total, 2))
    mft.output.set_string_list("cities", sorted(cities))


# --- Boilerplate (do not modify) ---
if __name__ == "__main__":
    try:
        task = MFT.init()
    except Exception as e:
        MFT.Err(str(e), error_id="InitError")
    try:
        run(task)
        MFT.Ok()
    except Exception as e:
        MFT.Err(str(e))
```

## Example 5: Using Both REST API and Repository Together

**`src/task-meta.json`** (top-level only):
```json
{
  "display_name": "Site Usage Audit",
  "description": "Combines REST API user info with repository view statistics",
  "uses": ["RestApi", "Repository"],
  "inputs": [],
  "outputs": [
    { "id": "report", "display_name": "Report", "type": "String", "is_list": false }
  ]
}
```

**`main.py`**:
```python
from mft import MFT


def run(mft: MFT) -> None:
    # Get users via REST API
    server = mft.tableau_api.server
    all_users, _ = server.users.get()
    user_count = len(all_users)

    # Get view stats via Repository
    rows = mft.repository.execute(
        "SELECT COUNT(*) AS total_views FROM hist_views"
    )
    total_views = rows[0][0] if rows else 0

    report = f"Site has {user_count} users and {total_views} total historical views."
    mft.output.set_string("report", report)


# --- Boilerplate (do not modify) ---
if __name__ == "__main__":
    try:
        task = MFT.init()
    except Exception as e:
        MFT.Err(str(e), error_id="InitError")
    try:
        run(task)
        MFT.Ok()
    except Exception as e:
        MFT.Err(str(e))
```
