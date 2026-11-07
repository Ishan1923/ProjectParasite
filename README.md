# ProjectParasite

Use one computer's keyboard (and later mouse) to control another computer over
the local network, while you keep using the first one normally.

- **Server**: the machine whose keyboard and mouse you use. It runs `server.py`
  and is the only authority: it decides what is sent, and approves connections.
- **Client**: the machine being controlled. It runs `client.py`, connects to the
  server, waits for approval, then receives input events.

Today the server is tested on macOS and the client on Linux (Pop!_OS). Steps
that differ by operating system are labelled **(server, macOS)** or
**(client, Linux)**.

> **Status: prototype.** The connection, token check, server-side approval and
> message protocol work. Injecting real keystrokes on the client and capturing
> them on the server are still being built, so for now received events are only printed.

---

## ⚠️ WARNING: read this before using

This tool is designed to **type and click on a computer for you**. That is a
powerful capability, so understand what you are enabling.

**Client side (Linux)**
- `setup-permissions.sh` lets the user logged in at the client machine open
  `/dev/uinput`. After that, **any program running as that user can type and
  click as them**, in any window, including terminals and password prompts.
- Only run software you trust on that account.
- **Never** use `chmod 666 /dev/uinput`. It lets every account and process
  on the machine inject input.
- Undo it any time: `./setup-permissions.sh --uninstall`, then reboot.

**Server side (macOS)**
- When keyboard capture is added, macOS will require **Accessibility** and
  **Input Monitoring** permission. That lets the app see everything you type,
  **including passwords**, while it runs. Grant it only to a build you trust,
  and revoke it in System Settings → Privacy & Security when you are done.

**Network**
- Anyone who can reach the server **and** knows the token **and** gets your
  `y` approval can send input to the client. Treat `PARASITE_TOKEN`
  like a password: long, random, never committed to git, never shared.
- Run it only on a network you trust. **Do not** use public or shared Wi-Fi
  (cafés, hostels, guest networks).
- **Do not** port-forward port 8000 on your router.
- Bind the server to its LAN IP (as shown below), not `0.0.0.0`.
- Traffic is plain WebSocket (`ws://`), **not encrypted**. Keystrokes, including
  passwords typed while the keyboard is routed to the client, can be read by
  anyone who can sniff your LAN. TLS is not implemented yet.
- Always answer `n` to an approval prompt you did not expect.

---

## Requirements

- Server and client on the same LAN (not a guest network)
- [`uv`](https://docs.astral.sh/uv/) on both machines
- The project folder on both machines, with an **identical `protocol.py`**

On both machines, from the project root:

```bash
uv sync
```

Starting from scratch: `uv add fastapi "uvicorn[standard]" pydantic websockets`
(the server needs fastapi and uvicorn, the client needs websockets, both need
pydantic). On the client you will also need `uv add evdev` once the injector is added.

## 1. Create the shared token

Pick a long random value and set the **same** one on both machines. The server
and client both refuse to start without it.

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

In every terminal you use to run the server or client:

```bash
export PARASITE_TOKEN="paste-the-value-here"
```

Check it is set with `printenv PARASITE_TOKEN` (empty output means it is not).
The variable lasts only for that terminal. Do not commit it.

## 2. Client (Linux): grant input permission (one time)

Run this **on the client machine, from its desktop session, as your normal
user** (do not use `sudo`; the script calls it for you):

```bash
chmod +x setup-permissions.sh
./setup-permissions.sh
```

It explains what it will change and asks `y/N`. Afterwards, verify:

```bash
./setup-permissions.sh --check     # every line should say "ok"
```

Other options:

| Command | What it does |
|---|---|
| `./setup-permissions.sh --help` (or `-h`) | Detailed, plain instructions |
| `./setup-permissions.sh --check` | Report status only, change nothing |
| `./setup-permissions.sh -y` | Install without the confirmation prompt |
| `./setup-permissions.sh --uninstall` | Remove everything the script added |

## 3. Server: start it

Find the server's LAN IP **(server, macOS)**:

```bash
ipconfig getifaddr en0      # use en1 if this prints nothing
```

From the project root (use the real IP, no `<` `>` brackets):

```bash
export PARASITE_TOKEN="..."
uv run uvicorn projectparasite.server:app --host 192.168.x.x --port 8000
```

If the OS asks whether to allow incoming connections, allow it.
Leave this terminal open: it is where you approve connections.

## 4. Client: start it

From the project root, with the same token set:

```bash
export PARASITE_TOKEN="..."
uv run python -m projectparasite.client 192.168.x.x    # the server's IP
```

On the server you will see:

```
Accept connection from <client name>? (y/n):
```

Type `y` to approve. The client prints `Connection accepted by server.` and
then waits for events. Typing `n` rejects it.

## Getting instructions and help

- Permission script: `./setup-permissions.sh --help`
- Check permission status: `./setup-permissions.sh --check`
- Run the protocol tests: `uv run python src/projectparasite/test_protocol.py`

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `KeyError: 'PARASITE_TOKEN'` | The variable is not set in *this* terminal. Run the `export` line. |
| `ModuleNotFoundError: fastapi` | Run with `uv run ...`, not a bare `uvicorn`. Check `uv sync`. |
| `Connection refused` / timeout | Server not running, wrong IP, or not on the same network. Try `ping <SERVER_IP>` from the client. |
| Client prints "bad token" | The token differs between the machines. |
| Server keeps waiting after the client quit | The `y/n` prompt blocks until you press Enter. Press Enter. |
| `PermissionError: /dev/uinput` | Run `./setup-permissions.sh --check`. If it fails, log out and back in, and run it from the desktop session, not plain SSH. |
| `No such file: /dev/uinput` | `sudo modprobe uinput` |
| `zsh: no such file or directory: <...>` | Do not type the angle brackets; replace the whole placeholder. |

## Uninstall

```bash
./setup-permissions.sh --uninstall     # on the client, then reboot
```

On the server (macOS), remove the app's Accessibility / Input Monitoring entries
in System Settings → Privacy & Security.