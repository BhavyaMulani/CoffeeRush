# THE UNWRITTEN CAFÉ — COFFEE RUSH: ANIME EDITION
**Complete playable classroom game package • Release 1.1 — Edge launch fix**

**Where the Stories Brew**

## The two ways to play

**1. Solo demo — open instantly (easiest)**
Double-click `Play_Offline_Demo.html`. It runs without installing anything and has the complete five-customer game, character dialogue, local demonstration scores, points, rewards, and creator studio. All Solo demo data is saved in that *one browser*. It is designed for an instant classroom presentation.

**2. Community Edition — shared leaderboard + member accounts (recommended)**
This is the more complete version in the `public/` folder backed by `server.py`. Create accounts with usernames and passwords, play full rounds, and compete with other accounts using the same server. Scores and vouchers are stored in SQLite. It also works with no internet connection when run on your own computer.

## Windows quick start — Community Edition

1. Make sure **Python 3.10 or newer** is installed from https://www.python.org/downloads/ (check "Add Python to PATH" during installation).
2. Unzip the full project folder first. **Do not run it from inside the ZIP.**
3. Double-click `START_WINDOWS.bat`. **Keep the console window open.** The game now waits for its server to start successfully before opening Edge. If the server fails, the window displays an error instead of opening a blank page.
4. If the browser doesn't open automatically, copy **http://127.0.0.1:18765/** into Edge **after** the console says `Your game is running at:`.
5. Use **Create account**, pick a nickname (3–18 letters/numbers/underscores), and choose a password (at least eight characters). Then click **Play ranked rush**.
6. Leave the server terminal running while anyone is playing. Close it to shut down the local server.

**If Windows cannot find Python:** Double-click `Play_Offline_Demo.html` for the complete offline demo (no installation). For community accounts, install Python 3.10+ first. Advanced users can run `py -3 server.py`, which defaults to port `8765`, then open http://127.0.0.1:8765.

## macOS or Linux quick start

Open Terminal in the extracted folder, then run:

```bash
python3 server.py
```

Open http://127.0.0.1:8765 in a browser, or use `START_MAC_LINUX.command`, which starts on port `18765` and attempts to open a browser automatically. On macOS, you may need to run `chmod +x START_MAC_LINUX.command` first.

**No pip installs or paid software required.** The server uses Python's built-in SQLite and HTTP libraries; the browser game uses HTML, CSS and JavaScript. It does not require the internet or external APIs.

## How members play

- Register once with a public nickname and password (only on your own game server).
- Choose **Ranked** for the shared community leaderboard or **Practice** for testing designs. Practice does not earn points.
- Each of five unique visitors tells two short original story lines. Press **Start brewing** when ready. The countdown never runs during story dialogue.
- Read the order ticket; choose **base, temperature, milk, syrup, and topping**. Faster exact orders get more game points. A streak earns a bonus.
- After five drinks, review your **score, weekly rank, reward points, and badges**.
- Visit **Rankings** for weekly/monthly/all-time best scores. These entries are genuine accounts on the same community server—not fake sample competitors.
- Visit **Rewards** to trade demo points for demo vouchers.

## Reward economy

| Event | Loyalty points |
|---|---:|
| Complete a ranked five-order rush | +5 |
| Score at least 500 | +10 |
| Make five perfect drinks | +5 |
| Maximum earned per member per Toronto-calendar day | **30** |

The server independently checks gameplay scores, timers, and loyalty grants; the browser cannot directly post a score or change its point balance. Ranked timer is **30 seconds for the first order**, reducing by two seconds each successive order. Practice mode allows **25/30/45/60 seconds**, has no ranking, and doesn't award points.

**Example catalogue (demo only):** syrup upgrade (10), extra espresso shot (15), cookie with a drink (25), 10% off one drink (40). These are illustrative and **not valid for purchases**.

## Optional staff demo: one-time vouchers

The online game includes a sample staff validation screen. To enable it, set a staff PIN *before running the server*. For example, on Windows Command Prompt:

```bat
set COFFEE_RUSH_STAFF_PIN=replace-with-a-private-pin
py -3 server.py
```

On macOS/Linux:

```bash
COFFEE_RUSH_STAFF_PIN='replace-with-a-private-pin' python3 server.py
```

Open the **Rewards** page, enter the voucher code and configured PIN, and validate. A sample voucher can be marked as used only once. **This is classroom demonstration functionality, not a secure production POS/retail voucher system.** Never use the example PIN verbatim.

## Different phones/computers — same leaderboard

Running the game at `127.0.0.1` allows only the host computer to connect. If the devices are on the **same trusted classroom Wi-Fi**, the computer running the server can listen on the local network:

```bash
# macOS/Linux
COFFEE_RUSH_HOST=0.0.0.0 COFFEE_RUSH_PORT=18765 python3 server.py
```

Windows Command Prompt:

```bat
set COFFEE_RUSH_HOST=0.0.0.0
set COFFEE_RUSH_PORT=18765
py -3 server.py
```

Then, on other devices, open `http://YOUR-COMPUTER-LAN-IP:18765`. Your computer's firewall must permit local connections. Only use a trusted private network. Do **not** expose the built-in HTTP server directly to the public internet, especially for real user passwords or commercial vouchers. For internet deployment, a developer should configure HTTPS, robust authentication, rate limiting, backups, monitoring, and POS integration behind a production-grade web server.

## What's included

- `public/index.html` — responsive game screens and layout
- `public/style.css` — visual style, original color palettes, mobile layout
- `public/app.js` — playable browser client, stories, brew interface, studio, rewards, rankings
- `server.py` — Python server with SQLite data, authentication, rankings and scoring
- `Play_Offline_Demo.html` — one-file standalone version for offline class demo
- `GAME_BLUEPRINT.md` — detailed design/specifications, game flow, characters, API, risks
- `START_WINDOWS.bat`, `START_MAC_LINUX.command` — easy launchers
- `tests/` — API smoke tests

The community database `coffee_rush.sqlite3` is created automatically when first run. **Keep a backup** if you want to retain your members and scores. Never share the live database publicly; it contains user account hashes.

## Important limitations

This is a **runnable, self-hosted classroom product** with real, server-shared demo accounts and rankings. It is **not** a hosted website and is **not** integrated with a real café register, purchase verification, payment system, or professional identity provider. Real-world redeemable discounts need staff controls, legal/financial review, fraud prevention and consent/privacy review. The Python standard-library server is built for demos and trusted local networks, not production-grade public internet traffic. There is no automated password recovery, account deletion interface, or content moderation system. Don't register with passwords used on other services; do not collect customer personal details.

The game features **original** anime-inspired characters, artwork and dialogue; it does not contain copyrighted anime character images, scenes or official stories. If you want to commercially use Gojo, Luffy or Zoro, obtain the relevant intellectual-property permissions first.

## What to show your professor

**USER MODE:** Register member → Play ranked → Read two story scenes → Brew five orders → See score & ranking → Redeem a sample voucher.

**DESIGN MODE:** Go to Design studio → Change theme → Change practice timer → Rewrite a character's first dialogue → Save → Launch Practice → See your changes.

**CODE WALKTHROUGH:** In `public/app.js`, show `renderStory`, `renderBrew`, `serve`, and `renderStudio`. In `server.py`, show `/api/round/serve`, `/api/round/advance`, and `/api/rewards/redeem` to explain server-calculated points, rankings and persistence.

Press **Ctrl+C** in the server terminal to stop the game.

## Edge opens but no game appears

1. **Simplest:** Download the standalone `Play_Offline_Demo.html` and open it from the Downloads folder with Edge; do not try to open it in an online file preview.
2. **Community version:** Extract the ZIP completely. Do not open `public/index.html` directly, because it needs the Python server. Run `START_WINDOWS.bat` instead and **keep the command window open**.
3. Wait until the console displays `Your game is running at: http://127.0.0.1:18765/`. Then paste exactly that address into Edge. Do not type `file:///...` for the community version.
4. If Edge still shows a blank page, press `Ctrl+Shift+R` to refresh, or try opening the same address in Chrome.
5. If that fails, take a screenshot of the Edge window **and the text in the black command window**. The error message will tell us what needs fixing.

The standalone version saves locally in one browser. The community version uses accounts and shared leaderboard data on the local server.
