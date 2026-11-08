# Coffee Rush: Anime Edition — Complete Game Blueprint

## Product identity
The Unwritten Café • Tagline: Where the Stories Brew. Genre: anime-inspired barista time-management + story mini-game. Target: café rewards members and anime/story fans. Goal: earn a high score, join a public nickname leaderboard, and accumulate capped demo loyalty points.

## Product navigation
**Home → Member registration/login → Game (five story + brew cycles) → Results → Rankings → Rewards.** Secondary tools: Design studio (colors, practice timer, dialogue), Staff demo voucher validation, Sign out.

## Gameplay
1. Select Ranked (30-second standard first order; 28, 26, 24, 22 afterwards) or Practice (25/30/45/60-second first order; no earned points).
2. Server chooses five different original characters from six.
3. Each character speaks two short story lines, with no countdown running.
4. Press Start Brewing. Order ticket has five ingredients; select one option for every field.
5. Serve before the server countdown expires; get an exact/partial/expired evaluation and farewell line.
6. Repeat until all five guests are served. Results show game score, perfect orders, weekly rank, points earned, and updated member record.

## Original story characters and sample drinks
| Character | Identity | Order | Story focus |
|---|---|---|---|
| Kaien | Starlight Guardian | Starlight Iced Latte | A guardian learning the value of rest |
| Rumi | Horizon Chaser | Caramel Cloud Frappé | A traveler learns friends matter more than treasure |
| Renji | Wayward Blade | Wanderer Double Espresso | A wanderer searches for direction |
| Sora | Sky Librarian | Cinnamon Crown Cappuccino | A librarian gathers unwritten dreams |
| Mika | Neon Inventor | Neon Iced Mocha | An inventor learns to try again |
| Yori | Moonlit Musician | Moonlight Vanilla Latte | A musician writes unsent letters through songs |

All original character dialogue is defined centrally in `server.py` and passed to the web client through `/api/config`. Original SVG portraits are in `public/app.js` (`portraitSVG`). The user may locally override one opening story line through Design studio.

## Scoring (validated on server)
- Exact drink: +100.
- Speed: +0 to +50 for an exact drink, based on the real time elapsed since server activated the order.
- Perfect combo: +25 for each further exact drink in an uninterrupted streak.
- Partial drink: +20 for each correctly chosen field.
- Expired timer: 0.
- Maximum theoretical single round: 150 + 4×175 = **850**.
- Only the best ranked five-order score per member is used for each leaderboard period. Rankings are available for current Toronto week, current Toronto month, and all time. Real members across all browsers sharing this server count; sample bots are not used in Community Edition.

## Rewards and loyalty safeguards
- 5 points when a ranked round finishes.
- 10 additional points if the ranked score is 500+.
- 5 additional points for all five drinks perfect.
- Maximum **30 points earned per Toronto calendar day**, enforced in the SQLite database.
- Redemption prices: syrup upgrade (10), extra espresso shot (15), cookie with drink (25), 10% off one drink (40). All are samples and not accepted for real-life purchases.
- One-time voucher IDs start with `CR-`. Staff demo PIN (optional environment variable) can mark an unused voucher as used once.
- Practice mode changes are not valid for ranked competition or real member points.

## Technology, development, and demonstration
- HTML/CSS/JS in `public/` for mobile- and desktop-friendly browser UI. Original vector character portraits are generated inline with SVG. No external fonts, media dependencies, or paid APIs.
- Python standard library `http.server` + SQLite for accounts, authenticated sessions, scoring, competition, reward records, and voucher verification. Passwords are salted PBKDF2 hash values; session tokens are random and stored only by hashed identifier. Sessions are held in HTTP-only cookies. Please use HTTPS before external deployment.
- Three design tools: visual palette selection; configurable **practice** countdown; editable opening story. Color and dialogue updates save in browser localStorage. Ranked mode stays fixed to preserve fair scores.
- Home, story, timed brewing, feedback, results, rankings, rewards, member modal, design editor, staff validation screens.
- API test harness under `tests/` verifies login, scoring and reward caps.

## Operational workflow for a café concept
An optional café poster QR code would take customers to a **hosted HTTPS deployment**, not to the classroom local IP. Members would create privacy-conscious nickname profiles and play during or between visits. A commercial launch would link a verified café loyalty account, implement audit and redemption controls, validate vouchers through the real POS, enforce rate limits and moderation, and publish privacy rules. None of these commercial launch capabilities is promised by this prototype.

## Risks and production roadmap
1. **Account security/privacy:** A public service requires HTTPS, better authentication, anti-brute-force, account recovery/deletion, and privacy compliance.
2. **Fraud / cheating:** Server validation reduces casual score manipulation but a production reward platform also needs anomaly analysis, abuse monitoring, verified loyalty members, and POS-based redemption.
3. **System downtime / cost:** A real hosted service needs uptime, server monitoring, automatic backups, paid hosting, and support ownership.
4. **IP licensing:** Named franchise anime characters and official designs require rights clearance for commercial use. This game uses original characters instead.
5. **Accessibility / fairness:** Improve keyboard, screen reader, sound alternatives, translations and leaderboard moderation with real user testing.

## Software design walk-through (class)
**1. Customize:** Explain how CSS custom properties `--accent` and theme selectors change colors in `style.css`. Toggle in Design studio.

**2. Build a mechanic:** Open `public/app.js`; explain `renderBrew` drawing ingredients and the countdown, `serve` submitting choices, and `renderFeedback` displaying actual scored results.

**3. Connect an online feature:** Open `server.py`; explain `Handler.do_POST`, especially `/api/round/serve`, `/api/round/advance`, and `/api/rewards/redeem`, to show why other members see the same leaderboard. Explain the SQLite tables `users`, `scores`, `points_earned`, `vouchers`.

**4. Demonstrate the product:** Open the game in a browser, create two demo accounts, complete a ranked round, visit Rankings, redeem a sample reward, and switch to practice to show design changes.
