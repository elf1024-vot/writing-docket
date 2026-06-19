# Installing the Writing System

This guide walks you through setup from a completely fresh Windows PC. You do **not**
need to be technical. You will install a few free programs, fill out one plain-English
document, and run a single command. Claude Code does the rest.

**Total time:** about 30–45 minutes the first time (most of it is downloads and one
reboot). The actual build at the end takes 5–15 minutes.

> **Before you begin — do not close the window.** Once you start the build (Step 6),
> leave Claude Code open and running until you see the green **Setup Complete** message.
> Closing it partway can leave the system half-built.

---

## What you're installing, and why

The writing system runs entirely on your own computer — nothing is uploaded to the
internet. To do that it needs four free pieces of software:

| Software | What it does | Required? |
|---|---|---|
| **Windows 10 (2004+) or Windows 11** | The operating system. WSL2 (below) needs this version or newer. | Yes |
| **WSL2** | "Windows Subsystem for Linux" — lets Docker run. Free, built into Windows. | Yes |
| **Docker Desktop** | Runs the database and web pages in tidy self-contained "containers." | Yes |
| **Python 3.9+** | Runs the small helper scripts (word count, the MCP connector). | Yes |
| **Claude Code** | The AI assistant that reads your plan and builds everything. | Yes |
| **Git** | Only needed if you install the skill from GitHub by URL. | Optional |

The build skill checks for all of these automatically and tells you exactly what's
missing. You can let it guide you, or install everything first using the steps below.

---

## Step 1 — Check your Windows version

1. Press **Windows key + R**, type `winver`, press **Enter**.
2. A box appears. Look for a line like **"Version 22H2 (OS Build 19045.xxxx)"**.
3. The build number (the `19045` part) must be **19041 or higher**.
   - **19041 or higher** → you're good, continue to Step 2.
   - **Lower than 19041** → run **Windows Update** (Start → Settings → Windows Update →
     Check for updates), install everything, restart, and check `winver` again.

---

## Step 2 — Install WSL2

WSL2 is free and built into Windows.

1. Click **Start**, type `PowerShell`.
2. Right-click **Windows PowerShell** → **Run as administrator** → **Yes**.
3. Type this and press Enter:
   ```powershell
   wsl --install
   ```
4. Wait for it to finish, then **restart your computer** when prompted. This reboot is
   required — WSL2 will not work until you restart.
5. After restarting, open PowerShell again and run `wsl --status`. You should see
   **"Default Version: 2"**. If it does, WSL2 is ready.

> If `wsl --install` says it's already installed, you're done — move on.

---

## Step 3 — Install Docker Desktop

1. Download the installer: **https://www.docker.com/products/docker-desktop/**
   (click "Download for Windows").
2. Run the downloaded **Docker Desktop Installer.exe**.
3. When asked, **keep "Use WSL 2 instead of Hyper-V" checked** (it's the default).
4. Finish the install and **start Docker Desktop** from the Start menu.
5. Accept the service agreement. You can skip the sign-in / "recommended settings"
   prompts — they're not needed.
6. Wait until the Docker whale icon in your system tray (bottom-right, near the clock)
   stops animating and shows **"Docker Desktop is running."**

> **Docker must be running every time you use the writing system.** If your database
> won't connect later, the usual cause is Docker Desktop simply isn't started. Open it
> from the Start menu and wait for the whale to settle.

---

## Step 4 — Install Python

1. Download Python: **https://www.python.org/downloads/** (click the big yellow
   "Download Python 3.x" button).
2. Run the installer. **Important:** on the first screen, check the box
   **"Add python.exe to PATH"** at the bottom *before* clicking Install.
3. Click **Install Now**, let it finish, click **Close**.
4. Verify: open PowerShell and run `python --version`. You should see `Python 3.x.x`.

The build also needs one small Python add-on for the database connector. Install it now:
```powershell
pip install psycopg2-binary
```

---

## Step 5 — Install Claude Code and the writing-docket skill

1. Install **Claude Code** if you haven't already: **https://claude.ai/code** — follow
   the instructions there and sign in with your Claude account (a Pro or Team
   subscription, or an API key).
2. Install the writing-docket skill. In Claude Code, run:
   ```
   claude skill install https://github.com/elf1024-vot/writing-docket
   ```
   (Installing by URL needs **Git** — if you don't have it, install from
   **https://git-scm.com/download/win** first, or install the skill from a local copy.)

---

## Step 6 — Create your plan document

The easiest way: in Claude Code, run **`/start-here`**. It interviews you in plain English
and writes the `docket-plan.md` for you — then you can review and tweak it.

Or write it by hand. It's a plain text file named **`docket-plan.md`**, all plain English —
no code, no special formatting required. Example:

```markdown
# My Writing Project

## Project
- Name: The Iron Compass
- Genre: Steampunk Mystery
- Author: Jane Smith

## Characters
- protagonist: Lady Vex — detective, mechanical arm, dry wit
- antagonist: The Archivist — faceless bureaucrat, controls information

## Books / Series
- Book 1: The Vanishing Guild

## Gates
- Use generic G1-G8
- Add: no anachronistic technology references

## TTS: no
## Synthesis tracking: no
```

You can skip the file entirely — the build will ask you everything in conversation.
The plan doc just saves typing and lets you prepare in advance.

---

## Step 7 — Run the build

In Claude Code, run:

```
/system-build docket-plan.md
```

(or just `/system-build` with no file to answer everything by conversation).

Then:

1. **Leave the window open.** You'll see the "DO NOT CLOSE THIS WINDOW" banner — heed it.
2. Claude runs a **pre-flight check** and prints a table showing each requirement passed.
   If something's missing, it tells you exactly what to fix, then you re-run the command.
3. Claude asks a few questions: project name, your name, genre (and offers
   genre-specific add-ons), standalone vs. series, where to put the folder, and what time
   to run the nightly backup.
4. Claude builds everything — database, web pages, AI prompts, backups — and starts it.
   The first run downloads Docker images, so this takes 5–15 minutes. That's normal.
5. When it's done you'll see a **Setup Complete** banner with your web links.

> **About those permission boxes.** A few times during setup, Claude Code will pop up a
> small box showing a command and asking *"Do you want to proceed?"* — sometimes with
> technical wording like *"manual approval required."* **This is normal. It's Claude Code
> asking before it sets things up on your computer — not an error.** Choose **Yes** each
> time. If the box offers a *"Yes, and don't ask again"* option, pick that and the rest of
> setup runs without stopping to ask.

---

## Step 8 — Finish up

1. **Restart Claude Desktop** (close it fully and reopen) so it picks up the new MCP
   connector for your project. *(This only matters if you use Claude Desktop; Claude Code
   picks it up on the next session.)*
2. Open your web UI in any browser: **http://localhost:8090** (the exact port is shown in
   your Setup Complete banner — it may be 8091 etc. if 8090 was busy).
3. You'll see starter **[EXAMPLE]** rows in each editor showing how every field is used.
   Replace them with your own characters, locations, and chapters.
4. Read the built-in help any time at **http://localhost:8090/faq.html** and
   **http://localhost:8090/readme.html**.

---

## Everyday use after install

| You want to… | Do this |
|---|---|
| Start writing | Make sure Docker Desktop is running, open the web UI, and use Claude Code |
| Get a scene brief before drafting | `/novel-plan` |
| Check everything is healthy | `/system-status` |
| Add genre features later | `/system-extend [project-name] [extension]` |
| Restore from a backup | `/system-restore [project-name]` |
| Update to a newer version | `/system-upgrade [project-name]` |
| Remove the system (keeps your writing) | `/system-uninstall [project-name]` |

> **Keep Docker Desktop running while you write**, and **keep Claude Code open** — the
> connector that lets Claude read your project database only works while Claude Code is
> running.

---

## Troubleshooting

**"Pre-flight failed: Windows build too old."**
Run Windows Update (Step 1), restart, try again. WSL2 genuinely requires build 19041+.

**"Docker is not running" or the web pages won't load.**
Open Docker Desktop from the Start menu and wait for the whale icon to stop animating,
then retry. Nine times out of ten this is the fix.

**`wsl --status` doesn't say "Version 2."**
Run `wsl --set-default-version 2` in an administrator PowerShell, then restart.

**`python` isn't recognized.**
You missed the "Add python.exe to PATH" checkbox during install. Re-run the Python
installer, choose **Modify**, and enable that option (or reinstall and check the box).

**Port 8090 is already in use.**
The build detects this and automatically uses the next free port (8091, 8092, …). Your
real address is always shown in the Setup Complete banner and saved in your project's
`.env` file as `UI_PORT`.

**The MCP / Claude can't read my database.**
Make sure Docker Desktop is running and Claude Code is open. If you use Claude Desktop,
restart it once after install. Then run `/system-status` to confirm all services are up.

**I lost my passwords.**
They live in the `.env` file inside your project folder (never committed, never shared).
The master password is like a root password — keep it safe. If the file is lost, the
build skill can rotate and re-provision credentials without losing your writing.

---

## Protecting your writing

The system runs a **nightly backup** automatically (you chose the time during setup) to a
`backups\` folder in your project. That protects against software problems.

It does **not** protect against your hard drive failing. Once a week, copy the entire
`backups\` folder to a USB drive or external disk. That's your hardware insurance. The
FAQ has step-by-step instructions under *"How do I protect my writing from hardware
failure?"*

---

## Enjoying the writing system?

This tool is built and maintained by E.L. Frederick. If it helps your writing, please
subscribe and follow along: **https://substack.com/@elfrederick**
