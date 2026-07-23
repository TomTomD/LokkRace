# LokkRace — web app (prototype)

A static, client-side version of LokkRace intended for hosting on **GitHub Pages**
(or any static host). No server, no backend, no login: the app runs entirely in
the browser, and all data lives in a **data bundle** (a JSON file) that the
organizer holds. Possession of the file *is* the access control.

## Status

Working prototype — the **full event flow** is built:

1. **Registrering** — add kayakers + bib numbers; live start list.
2. **Start & Mål** — START, live clock + per-kayaker countdown, **MÅL!** button
   (or press **M**) to stamp crossings, secretary records the bib order.
3. **Matchning** — pair each crossing time with a kayaker (pre-filled from the
   secretary's order), warns on duplicates, computes results + improvement.
4. **Resultat** — improvement leaderboard ("most improved wins"), season report,
   then save (folds best times into the roster + exports the updated bundle).

Domain logic (`js/racebase.js`) is a full port of the Python `racebase.py`.
In-progress race state is snapshotted to `localStorage`, so a refresh mid-event
loses nothing. The club logo is bundled locally (`img/`) so the app works offline.

## Run locally

ES modules must be served over HTTP (not opened as `file://`). Any static server
works; Python is easiest:

```bash
cd web
python -m http.server 8000
# then open http://localhost:8000/
```

Run the tests by opening <http://localhost:8000/tests/test.html> in a browser —
it shows a green pass/fail summary (no toolchain needed).

## Deploy to GitHub Pages

Deployment is automated by `.github/workflows/pages.yml`, which publishes this
`web/` folder on every push to `main` that touches `web/**`.

One-time setup: in the repo, **Settings → Pages → Source**, choose
**"GitHub Actions"** (not "Deploy from a branch" — that only allows `/` or
`/docs`, not a subfolder). After that the workflow deploys automatically; you
can also trigger it manually from the Actions tab (workflow_dispatch).

## Data bundle format

Persisted to `localStorage` on every change, and exported/imported as a JSON file
via the header buttons. The bundle is the **roster carried across events** — each
kayaker's `race_history` is what the season reports (improvement, most-improved)
are computed from, so loading last week's bundle carries the season forward.

```json
{
  "version": 1,
  "participants": [
    {
      "name": "Anna",
      "best_time_seconds": 900,
      "number": 14,
      "race_history": [
        { "race": "20260603-180000", "time_seconds": 905, "number": 14, "improvement": 5 }
      ]
    }
  ]
}
```

## Encryption (the shared file is passphrase-protected)

Exported files are **encrypted** with a passphrase (AES-GCM, key derived via
PBKDF2 using the browser's Web Crypto API) — the JSON above is the *decrypted*
content. On disk an exported file looks like
`{ "lokkrace_encrypted": 1, "salt": …, "iv": …, "ciphertext": … }`.

- **Öppna data** asks for the passphrase and decrypts in the browser; the wrong
  passphrase simply can't open it. **Exportera data** re-encrypts with the same
  passphrase.
- Because the file is ciphertext, it's safe to host/share anywhere (Drive, a
  public link, email) — **access = whoever has the passphrase**. It's a single
  shared passphrase (no per-user accounts); to revoke access, change it and
  re-share the file.
- `localStorage` on the operator's own device is *not* encrypted (trusted device).
- Plaintext bundles (e.g. the migration output below) still import fine.

## Migrating from the desktop app

The desktop app stores one file per kayaker in `data/kanotister/*.json` (plus
human-readable `data/races/*.txt`, which the web app doesn't need). Convert the
whole folder into one bundle once:

```bash
python tools/convert_desktop_data.py path/to/data lokkrace-data.json
```

Then load `lokkrace-data.json` with **Öppna data**. From then on, use the
bundle — export it after each event to carry the season forward.

## Usage flow (target)

1. **Registrering** — add kayakers + bib numbers to this competition. *(built)*
2. **Start** — live per-kayaker countdown to their handicap start (start = 0).
3. **+4. Start & Mål (one screen)** — while waiting, a secretary taps **MÅL!**
   for each goal-line crossing and records the order (numbers).
4. — *(shares the screen with step 3)*
5. **Matchning** — reconcile crossing times ↔ numbers; compute result + improvement.
6. **Resultat** — the improvement leaderboard ("most improved wins"); export the
   updated bundle.
