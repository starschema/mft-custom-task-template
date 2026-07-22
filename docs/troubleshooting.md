# Troubleshooting

Failures you are likely to meet when a task that runs fine locally is executed by Manager for Tableau. Custom tasks run inside a short-lived, isolated container, and most surprises come from that difference.

Every error below is quoted as it appears in the **task log** in the MFT web UI.

---

## `CERTIFICATE_VERIFY_FAILED` when connecting to Tableau Server

```
Task failed with error 'TaskError': Failed to connect to Tableau Server at https://tableau.example.com/:
HTTPSConnectionPool(host='tableau.example.com', port=443): Max retries exceeded with url: //api/2.4/auth/signin
(Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
unable to get local issuer certificate (_ssl.c:1032)')))
```

Your Tableau Server presents a certificate issued by an internal or corporate CA, and the task container does not trust it.

This is **not** something your task code did wrong, and it is expected that other parts of the product work fine against the same server — they run elsewhere. Two details explain it:

- The task container is created fresh for each run and does not inherit the application's certificate trust.
- `mft.tableau_api` signs in through `tableauserverclient` → `requests`, which validates against the **`certifi`** bundle (public CAs only) and never the operating system's trust store. So even an image with your CA installed via `update-ca-certificates` is not enough on its own.

**Ask your MFT administrator to set `CustomTaskExecution.CaCertificates`** to your CA's PEM in the server's `appsettings.json`. It applies to every custom task, so it is a one-time fix rather than something each task author repeats.

If you need to unblock yourself before that happens, ship the CA inside your own package:

1. Put the PEM in a **subdirectory** — for example `certs/corporate-ca.pem`.

   > This matters: `mft package` includes every file from subdirectories but only `.py` files from the project root. A `.pem` left in the root is silently dropped from the `.mft`, and the task then fails with `FileNotFoundError`.

2. At the very top of `main.py`, before `MFT.init()` and before any Tableau call:

   ```python
   import os, certifi

   _here = os.path.dirname(os.path.abspath(__file__))
   _bundle = "/tmp/ca-bundle.pem"
   with open(_bundle, "wb") as out:
       for src in (certifi.where(), os.path.join(_here, "certs", "corporate-ca.pem")):
           with open(src, "rb") as f:
               out.write(f.read())
               out.write(b"\n")
   os.environ["REQUESTS_CA_BUNDLE"] = _bundle
   os.environ["SSL_CERT_FILE"] = _bundle

   from mft import MFT
   ```

   Concatenating `certifi.where()` keeps the public CAs trusted, so any other HTTPS call your task makes still works. Your package is extracted to `/app/task`, which is also the working directory, so `certs/corporate-ca.pem` resolves next to `main.py`. You do not need to add `certifi` to `requirements.txt` — it arrives with the SDK.

### A similar-looking error that is *not* about trust

```
certificate verify failed: Missing Authority Key Identifier
certificate verify failed: unable to get issuer certificate
```

Here the server certificate is malformed or its chain is incomplete (OpenSSL 3 is stricter than older versions about missing extensions and intermediates). Adding a CA will not help — the certificate itself has to be corrected on Tableau Server. Confirm with:

```bash
openssl s_client -showcerts -connect tableau.example.com:443 </dev/null
```

---

## `Failed to fetch Tableau API credentials … (HTTP 500)`

```
Failed to fetch Tableau API credentials: Tableau API credentials request failed (HTTP 500):
Credential endpoints require HTTPS. The Docker container is connecting over plain HTTP...
```

Only tasks that use `mft.tableau_api` or `mft.repository` hit this, because only those request secrets from the backend. It is a **server configuration** matter, not a task bug — send it to your MFT administrator, who can resolve it with `CustomTask.RequireHttpsForCredentials` or by routing the internal callback over HTTPS.

> The one-time `TMClient server_url is not HTTPS -- credentials may be transmitted in plaintext` line in your log is only a warning. It appears for every task on an HTTP callback and blocks nothing. Despite the wording, it refers to the connection from your task back to the Manager for Tableau backend — **not** to Tableau Server — so it is never the cause of the certificate error described above.

---

## The task produces no status (`NoStatusFile`)

The container exited before your task reported a result. Usually the run command aborted earlier than `main.py`:

- **A dependency could not be installed.** Check the log for `pip install` errors. In restricted or air-gapped networks, PyPI may be unreachable — ask your administrator whether a pre-built image or an internal index is in use.
- **`main.py` crashed on import.** Anything raised before `MFT.init()` cannot be reported through the normal error path. Keep import-time work minimal.
- **The task exceeded `ExecutionTimeout`** and was stopped.

Always keep the `if __name__ == "__main__":` boilerplate from the template — `MFT.Ok()` / `MFT.Err()` are what write the status file.

---

## `[Errno 13] Permission denied`

The container may run as a non-root user. Write only to paths you are given: your own package directory and the workspace. Do not assume you can write to `/`, `/app`, or install system packages at runtime.

---

## It works locally but not in MFT

Local `dev` mode runs on your machine, with your network, your trust store, and your files. Inside MFT the task gets a clean container. The usual causes, in order:

1. A file that exists locally was not packaged — see the subdirectory rule above, and check the file list printed by `mft package`.
2. A dependency is missing from `requirements.txt` because it happened to be installed in your devcontainer.
3. A network path is reachable from your machine but not from the cluster or Docker host.
4. Certificate trust, as described at the top of this page.

Validate your inputs before packaging — it catches a large share of runtime failures:

```bash
mft validate-meta
mft validate-input
```
