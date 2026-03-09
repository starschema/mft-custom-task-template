# Custom Task Template for Manager for Tableau

This template is the starting point for building custom workflow tasks that run inside **Manager for Tableau (MFT)**. It includes a devcontainer, a skeleton `main.py`, and a sample `task-meta.json` ready to be customized.

## Quick Start

1. **Clone this repo** and open it in VS Code (or any editor with devcontainer support).
2. **Reopen in Container** — the devcontainer installs Python, the .NET runtime, and the `mft` package automatically.
3. **Edit `src/task-meta.json`** — define your task's display name, inputs, outputs, and service dependencies. See [docs/task-meta-reference.md](docs/task-meta-reference.md) for the full field reference.
4. **Validate your metadata**:
   ```bash
   mft validate-meta
   ```
5. **Generate an input file** for local testing:
   ```bash
   mft generate-input
   ```
   This creates `dev-files/input.json` with `TODO:` placeholders. Fill in real values.
6. **Validate your input file**:
   ```bash
   mft validate-input
   ```
   This checks for leftover `TODO:` markers, type mismatches, missing required fields, bad formats (dates, GUIDs, etc.), and unknown keys. Fix any errors before running the task.
7. **Write your task logic** in `main.py` inside the `run()` function. See [docs/input-output-guide.md](docs/input-output-guide.md) for how to read inputs and write outputs.
8. **Run locally in dev mode**:
   ```bash
   python main.py dev --server https://your-mft-server --token YOUR_REFRESH_TOKEN --server-id YOUR_SERVER_ID --site your-site
   ```
   Dev mode converts `dev-files/input.json` to the binary format, runs your task, then converts the binary output back to `dev-files/output.json` so you can inspect results.

   | Argument | Description |
   |----------|-------------|
   | `dev` | Positional argument that activates dev mode. |
   | `--server` | Your Manager for Tableau server URL (e.g. `https://mft.example.com`). |
   | `--token` | MFT Personal Access Token (refresh token) for authentication. Create one in the MFT web UI. |
   | `--server-id` | The Tableau Server ID registered in Manager for Tableau. |
   | `--site` | Tableau site content URL. |
   | `--input-file` | *(Optional)* Path to input JSON. Defaults to `./dev-files/input.json`. |

   > If your task does not use `RestApi` or `Repository` services, the `--server`, `--token`, `--server-id`, and `--site` arguments are still required but their values are not used — you can pass placeholder values.

   > **Auto-validation:** When running in dev mode, `MFT.init()` automatically validates your input JSON against `task-meta.json` before converting it to binary format. If validation fails, you get a clear error listing every problem — the same checks that `mft validate-input` performs. Bad input never reaches the converter.

   > **Token persistence:** The `--token` refresh token is single-use — each API call consumes it and returns a new one. The `mft` package handles this automatically: after each token refresh, the new token is saved to `dev-files/.mft_token`. On subsequent runs with the same `--token` value, the persisted token is used. This means you provide the token once and can re-run your task as many times as needed. If you generate a new PAT in the MFT web UI, pass the new value via `--token` and the old persisted token is replaced.

9. **Package your task** when ready:
   ```bash
   mft package
   ```
   This creates a `.mft` file you can upload to Manager for Tableau.

## Project Structure

```
CustomTaskTemplate/
  .devcontainer/        # Docker + VS Code devcontainer config
    Dockerfile
    devcontainer.json
  src/
    task-meta.json      # Task metadata (inputs, outputs, services)
    requirements.txt    # Your pip dependencies (mft is pre-installed)
  dev-files/            # Local dev files (input.json, output.json) — gitignored
  docs/                 # Documentation
    task-meta-reference.md
    input-output-guide.md
  main.py               # Entry point — implement run() here
```

For larger tasks, you can split your code into multiple files:

```
my-custom-task/
  src/
    task-meta.json
    requirements.txt
  main.py               # Entry point — imports from helpers
  helpers.py            # Helper module at project root
  src/
    utils.py            # Or organize modules under src/
    lib/
      __init__.py
      parser.py
```

All `.py` files at the project root and all files under `src/` (except `task-meta.json` and `requirements.txt`) are included in the `.mft` package automatically.

## CLI Reference

| Command | Description |
|---------|-------------|
| `mft validate-meta` | Validate `src/task-meta.json` and print a summary. |
| `mft validate-meta path/to/meta.json` | Validate a specific file. |
| `mft generate-input` | Generate `dev-files/input.json` from metadata with TODO placeholders. |
| `mft generate-input path/to/meta.json ./my-input.json` | Use explicit meta and output paths. |
| `mft validate-input` | Validate `dev-files/input.json` against metadata (types, formats, required fields, TODOs). |
| `mft validate-input ./my-input.json path/to/meta.json` | Use explicit input and meta paths. |
| `mft package` | Package the task into a `.mft` file (filename derived from `display_name`). |
| `mft package my_task.mft` | Package with a custom filename. |

### What `mft package` includes and excludes

`mft package` creates a clean deployment artifact from your working directory. It automatically excludes files that should never be uploaded to the server:

**Included:**
- `task-meta.json` — task definition (from `src/` or project root, placed at archive root)
- `main.py` — entry point
- `requirements.txt` — pip dependencies (from `src/` or project root)
- Additional `.py` files at the project root (helper modules)
- All files under `src/` subdirectories (except `task-meta.json` and `requirements.txt`)

**Excluded (automatic safety rules):**
- **Secrets and credentials** — `.env` and all variants (`.env.local`, `.env.staging`, etc.), `credentials.json`, `secrets.json`
- **Dev/test files** — `dev-files/` (your local test input/output), `.pytest_cache/`, `.tox/`, `.nox/`
- **IDE and tooling** — `.devcontainer/`, `.vscode/`, `.git/`, `.github/`, `.mypy_cache/`
- **Build artifacts** — `__pycache__/`, `.pyc`, `.pyo`, `.eggs/`, `*.egg-info/`
- **Documentation** — `docs/`
- **Non-code root files** — `README.md`, `.gitignore`, `.dockerignore`, etc. (only `.py` files are included from the project root)
- **Symlinks** — skipped entirely to prevent path traversal

This ensures your `.mft` archive contains only what the engine needs to run your task, without accidentally shipping sensitive data like API tokens, database passwords, or test credentials that may be in your working directory.

## Deploying to Manager for Tableau

Once your task is packaged with `mft package`, you upload the `.mft` file to Manager for Tableau through the web UI. The backend then:

1. **Registers the task** — extracts `task-meta.json` to learn the task's display name, group, parameters, and service dependencies. The task appears in the workflow editor UI.
2. **Stores the archive** — keeps the `.mft` file for when a workflow triggers the task.
3. **At execution time**, creates and runs a Docker container:
   - Starts from a base image with Python, .NET runtime, and `mft` pre-installed.
   - Mounts the extracted `.mft` archive into the container.
   - Installs your dependencies with `pip install -r requirements.txt`.
   - Sets environment variables (`MFT_SERVER_URL`, `MFT_AUTH_TOKEN`, `MFT_INPUT_FILE`, `MFT_OUTPUT_FILE`, etc.).
   - Writes the binary input parameter file with values from the workflow.
   - Runs `python main.py`.
   - After exit: reads the binary output parameter file and the status file.

Your task code runs identically to dev mode — the same `run()` function, the same `mft.input` / `mft.output` / `mft.tableau_api` / `mft.repository` APIs. The only difference is that configuration comes from environment variables instead of CLI arguments.

## Versioning

Custom tasks support versioning. When you need to change the inputs or outputs of your task or you implement a more significant logical change, increment `major_version` in `task-meta.json` and upload the new `.mft` file. The new version is stored alongside previous versions — workflows using the old version continue to work unchanged, while new or updated workflows can select the new version.

- **Bug fixes** (no input/output changes): delete the existing version in the Manager for Tableau UI first, then re-upload with the same `major_version`. Re-uploading without deleting first is rejected to prevent accidental overwrites.
- **`version_description`**: optionally describe what changed. This is shown in the UI.

See [docs/task-meta-reference.md](docs/task-meta-reference.md#versioning) for detailed versioning guidelines and examples.

## Debugging

Enable detailed MFT logs by adding this at the top of your `main.py`:

```python
import logging
logging.basicConfig()
logging.getLogger("mft").setLevel(logging.DEBUG)
```

When running in dev mode, the following files are created in `dev-files/`:

| File | Description |
|------|-------------|
| `input.json` | Your input data (you edit this). |
| `input.parameterFile` | Binary conversion of input.json (auto-generated). |
| `output.parameterFile` | Binary output written by your task (auto-generated). |
| `output.json` | JSON conversion of the binary output (auto-generated). |
| `status.json` | Task result — `{"status": "Completed", ...}` or `{"status": "Failed", "error": {...}}` (auto-generated). |
| `.mft_token` | Persisted refresh token for dev mode (auto-managed, gitignored). |

Inspect `output.json` to verify your task produces the correct results, and `status.json` to check for errors.

## Frequently Asked Questions

### Do I need to install [mft](https://pypi.org/project/mft-fortableau/) manually?

No. The devcontainer Dockerfile runs `pip install mft-fortableau` automatically. If you add Python dependencies your task needs, put them in `src/requirements.txt` — they are installed by the `postCreateCommand` when the container starts, and also bundled into the `.mft` package.

### What Python version is supported?

The devcontainer uses Python 3.13. The `mft` package requires Python 3.10 or later.

### Why does the container need .NET?

The `mft` package includes a C# binary (JsonConverter) that converts between JSON and the binary parameter format used by the workflow engine. In dev mode, this conversion happens automatically so you can work with readable JSON files. The .NET 8 runtime is required to execute this binary. You do not need to interact with it directly.

### Can I use my own Python libraries?

Yes. Add them to `src/requirements.txt`. They will be installed in the devcontainer on startup and bundled into the `.mft` package. The `mft` package itself already includes `requests`, `tableauserverclient`, and `psycopg2-binary`, so you do not need to list those.

### What does `MFT.Ok()` / `MFT.Err()` actually do?

They finalize the task execution:
1. Close input/output binary streams.
2. Disconnect any active services (Tableau API, Repository).
3. Write a status JSON (`{"status": "Completed", ...}` or `{"status": "Failed", ...}`).
4. Exit the process with code 0 (Ok) or 1 (Err).

If your task crashes without calling either, MFT's `atexit` safety net writes a `Failed` status with an `UnexpectedExit` error automatically.

### What happens if I forget to call `MFT.Ok()` or `MFT.Err()`?

The boilerplate in `main.py` handles this — `MFT.Ok()` is called after your `run()` function returns, and `MFT.Err()` is called if an exception is raised. As an extra safety net, MFT registers an `atexit` handler that writes a failure status if neither was called before the process exits.

### Can I read an input parameter that wasn't provided?

Yes. Single-value getters (`get_string()`, `get_integer()`, etc.) return `None` if the parameter has no value. List getters (`get_string_list()`, etc.) return an empty list. You should check for `None` on required parameters in your logic if needed.

### What is the `id` pattern for parameters?

Parameter IDs must match `^[a-zA-Z][a-zA-Z\d_]*$` — start with a letter, then letters, digits, or underscores. Examples: `name`, `itemCount`, `zip_code`. Invalid: `_private`, `2fast`, `my-param` (hyphens not allowed).

### Can I print to stdout for debugging?

Yes. In dev mode, `print()` output goes to your terminal as usual. In production, stdout is captured by the workflow engine. Use `print()` freely for debugging — it does not interfere with the status output (which is written to a separate file or clearly formatted JSON).

### Can I set an output parameter more than once?

No. Each output parameter can only be written once. Calling a setter a second time for the same `id` will raise an error. Make sure your logic computes the final value before writing it.

### How do I write a list of objects as output?

Use `set_object_list()` with a list of writer callbacks. Each callback receives a `ParameterObjectHandler` and sets the fields for one object. Use a closure factory to capture per-item data:

```python
def make_writer(name, score):
    def writer(obj):
        obj.set_string("name", name)
        obj.set_double("score", score)
    return writer

writers = [make_writer("Alice", 9.5), make_writer("Bob", 7.2)]
mft.output.set_object_list("results", writers)
```

### Why do I need `--server`, `--token`, etc. even if my task doesn't use the API?

In dev mode, these arguments are always required because MFT initializes the backend connection regardless — it may be needed for internal operations. If your task does not use `RestApi` or `Repository`, the credentials are never actually used, so you can pass placeholder values.

### What is the `.mft` file format?

It is a standard ZIP archive with the extension `.mft`. It contains `task-meta.json`, `main.py`, `requirements.txt`, any additional `.py` files from the project root, and all files under `src/` (except `task-meta.json` and `requirements.txt` which are promoted to the root). Non-runtime directories (`.devcontainer`, `dev-files`, `docs`, `__pycache__`) are excluded. You can inspect it with any ZIP tool.

### How does authentication work in dev mode vs production?

- **Dev mode**: You provide an MFT Personal Access Token (refresh token) via `--token`. The `mft` package exchanges it for a short-lived access token (JWT) via the MFT server API, and auto-refreshes it when it expires.
- **Production**: The workflow engine provides a short-lived action token via environment variable. No refresh is needed — the token is valid for the duration of the task execution.

In both cases, your task code does not handle authentication directly — `mft.tableau_api` and `mft.repository` get their credentials automatically from the MFT backend.

## Next Steps

- [Examples](docs/examples.md) — 5 complete examples covering string processing, Tableau API, Repository queries, nested objects, and combined services
- [Task Metadata Reference](docs/task-meta-reference.md) — all `task-meta.json` fields and parameter types
- [Input/Output Guide](docs/input-output-guide.md) — how to read inputs, write outputs, use objects and lists
