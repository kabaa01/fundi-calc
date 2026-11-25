# Fundi Calc

Plain tools for people in the field: the right cable and breaker, solar size, and borehole pump check, with Kenyan rules and where they come from.
Free for customers. Shops and installers pay to get their name, WhatsApp number and EPRA licence on every quote.

## Put it online (GitHub user: kabaa01)

Do these in order. Full steps with pictures of what to click are in the chat message that came with this zip.

1. Open `fundi-calc-admin-PRIVATE/admin.html` in Chrome and press **Make my keys**. Copy the **public key**. Save the private key file somewhere safe. Never upload the private key or the admin folder.
2. Open `config.json` in Notepad. Fill in `operatorWa` (your WhatsApp number as `2547XXXXXXXX`), `till` (your Buy Goods till), and paste the public key after `"publicKey":`. Keep `gateAll` as `false`.
3. Go to https://github.com/new. Owner `kabaa01`, name `fundi-calc`, **Public**. Do not tick any extra files. Create it.
4. Upload everything that is INSIDE `fundi-calc-repo` (not the folder itself) so that `index.html` sits at the top level. Include the hidden items `.github`, `.gitignore` and `.nojekyll`.
5. **Settings > Pages > Source: Deploy from a branch > main / (root) > Save.** After a minute the app is at **https://kabaa01.github.io/fundi-calc/**
6. **Settings > Actions > General > Workflow permissions: Read and write > Save.** Then open the **Actions** tab, choose **Watch laws and standards**, and press **Run workflow** once.

## Get paid and give access

Do not put the file `admin/admin.html` on GitHub. It lives in the separate private folder `fundi-calc-admin-PRIVATE`. Keep it on your own computer.

**One time**
1. Open `admin.html` in Chrome. Press **Make my keys**.
2. Copy the **public key** into `config.json` as `"publicKey": { ... }` and commit.
3. Save the **private key** file somewhere safe (a password manager is best). Never share it. If you lose it, make new keys and send everyone new codes.

**Each time a shop or installer pays**
1. They open the app, choose a plan, pay your till, type the M-Pesa code, and tap Send. You get a WhatsApp message that starts `Fundi Calc shop order FC-...`.
2. Open `admin.html`. Paste your private key (step 2). Paste their WhatsApp order message and your till messages (step 3). Press **Check payment**.
3. The page checks that the M-Pesa code is in YOUR till messages, the amount is enough, and the code was never used before. It never trusts a screenshot.
4. If it says "Payment found and correct", press **Issue access code**. Press **Open WhatsApp** and send the message. Installers: first check their EPRA licence on EPRA's own list and tick the box.
5. They paste the code under **Already paid?** in the Shops or Installers tab. Their name, WhatsApp and licence now show on their quotes. The code stops working after the date inside it. Monthly plans: send a new code next month.
6. Free pilot: the page issues a code with no payment. It lasts 3 days for shops and 30 days for installers. A business can have one free pilot only.

**What this protects, and what it does not**
- A code cannot be forged without your private key, and a changed code is refused.
- The check happens inside the user's phone. A skilled person could change the page on their own phone to skip it. The tools themselves are free anyway. What the code unlocks is a shop's or installer's branding and lead routing. To lock the whole app for real, you need a small server. See "Next step".
- One code can be shared. That puts the owner's name on every quote, so sharing is easy to spot. Keep codes to 31 days.

## Kiswahili

Every screen, error message, rule and WhatsApp or SMS share text is in English and Kiswahili. Use the **SW / EN** button at the top of the app.
- The words and sentences are in `i18n/sw.txt`. One line each: `English => Kiswahili`. Lines that start with `re:` are patterns for text with numbers in it. `$1` keeps the number as typed and `~1` also translates it.
- After you edit it, run `node tools/sync-i18n.mjs`. That saves the words inside `index.html`.
- The Kiswahili for each rule is in `rules.json` (`x_sw`). A new rule without `x_sw` shows in English until you add it.
- Terms follow what Kenyans already see: EPRA's own Kiswahili service charter (leseni, mkandarasi, mafundi, nishati) and Kiswahili shop listings (kigeuzi, betri, kebo, soketi, vivunja mzunguko, paneli za jua). I wrote the sentences. Please have a Kenyan Kiswahili speaker read them before launch, especially the consent text and the legal rules.
- Order messages that arrive on your WhatsApp stay in English on purpose, so the admin page can read them.

## Keeping the rules up to date

- The rules are in `rules.json`. Edit it on GitHub and commit. The app loads it every time it opens with internet, and the **Check for updates** button on the rules page loads it again. There is also a saved copy inside `index.html`. Run `node tools/sync-rules.mjs` to refresh that copy.
- Every Monday a robot (`.github/workflows/watch-rules.yml`) opens each source link. It opens an **Issue** on your repo if a link is broken or an official page changed. It cannot understand the change, so a person must read each Issue, check the law, and update `rules.json`.
- Kenya Law and some news pages load with JavaScript, so a change inside them can be missed. Read EPRA, NCA, KEBS and WRA yourself every few months.

## Works with no signal

`sw.js` saves the app on the phone after the first visit. After that it opens and runs without signal. Updates arrive the next time the phone has data. If you change `index.html`, change the version name in `sw.js` (`fundi-calc-v1` to `fundi-calc-v2`) so phones fetch the new copy.

## Privacy

- Never put customer names, phone numbers or M-Pesa codes in this repo. It is public.
- The admin ledger stays in your browser. Download the CSV and keep it offline.
- Register with the Office of the Data Protection Commissioner (odpc.go.ke) before you collect customer details.

## Cable sizes

The cable and breaker table comes from published BS 7671 ratings, the base of the Kenya wiring standard KS 662. The table, the checks and what is not covered are in `docs/CABLE-TABLE-SOURCES.md`. It is still software. Only a licensed contractor can design a real installation.

## Tests

`node tests/qa.js`, `node tests/qa_access.js`, `node tests/qa_i18n.js` and `node tests/qa_fuzz.js` run on every push (see **Actions** tab). They check the maths, access codes, payment matching, rule updates, reading level, and 20,000 rounds of garbage input.
Browser tests need Python and Playwright: `python3 tests/qa_browser.py`, `python3 tests/qa_lang.py` (Kiswahili and English complete, switching works), `python3 tests/i18n_inventory.py out.json sw` (lists any English left in Kiswahili), `FC_ADMIN=path/to/admin.html python3 tests/qa_access_browser.py`, and `PART=layout python3 tests/stress.py` (also `PART=fuzz` and `PART=misc`). They check screen layout, colour contrast, labels, double taps, slow signal, offline use and hostile settings.

## Next step: real automatic payment checks

Safaricom's Daraja API can call a small server when a payment lands. That server can check the payment and make the access code at once, with no manual step. This needs a server and a Daraja account, and it is not built here.
