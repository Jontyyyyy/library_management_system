# Deploying for Free

Two pieces, both genuinely free with no credit card:

| Piece | Service | Why |
|---|---|---|
| Database | [TiDB Cloud](https://tidbcloud.com) — Starter plan | MySQL-compatible (your code doesn't change), 5 GB storage free forever, no card required |
| App | [Render](https://render.com) — Free web service | Deploys straight from GitHub, no card required |

**The one trade-off:** Render's free tier spins your app down after 15 minutes with no traffic. The next visitor waits ~30–60 seconds while it wakes up, then it's normal speed. Fine for a portfolio/demo project; annoying for something you want instantly snappy 24/7 (more on upgrading that away at the bottom).

This whole walkthrough takes about 20–25 minutes.

---

## Part 1 — Push the project to GitHub

Render deploys from a GitHub repo, so the code needs to live there first.

1. Create a free account at [github.com](https://github.com) if you don't have one.
2. Click **New repository** (top right → the **+** menu). Name it `library-management-system`, keep it **Public** or **Private** (either works), don't add a README (you already have one) → **Create repository**.
3. On your own machine, in the project folder, run:

```bash
cd library_management_system
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/library-management-system.git
git push -u origin main
```

Your `.gitignore` already keeps `__pycache__/` and any local `.env` out of the repo, so `config.py`'s placeholder values are the only thing that goes up — no real password ever gets committed, because you'll set the real one as an environment variable in Render (Part 4).

---

## Part 2 — Create your free database (TiDB Cloud)

1. Go to [tidbcloud.com](https://tidbcloud.com) and sign up (no card needed).
2. Create a new cluster and choose the **Starter** plan (the free one). Any region close to you is fine.
3. Once it's created, open the cluster and click **Connect**.
4. From the connect panel, note down:
   - **Host** (looks like `gateway01.<region>.prod.aws.tidbcloud.com`)
   - **Port** — `4000`
   - **User** — this will look like `<random-prefix>.root`, not just `root`. Copy it exactly, prefix included.
   - **Password** — generate/reset one here and save it somewhere safe; TiDB Cloud won't show it again.

Keep this tab open — you'll paste these into Render in Part 4.

---

## Part 3 — Load the schema

Easiest way: TiDB Cloud's built-in web SQL editor, so you don't need MySQL installed locally.

1. In your cluster, open the **SQL Editor** (sometimes labeled **Chat2Query**) from the left sidebar.
2. Open `schema.sql` from the project, copy the whole file, paste it into the editor, and run it.
3. You should see the `books`, `members`, `transactions`, and `admins` tables get created, plus the sample data and the default `admin` login.

(If you'd rather use a local `mysql` client instead: connect with `mysql -u 'your.prefixed.user' -h <host> -P 4000 -p --ssl-mode=VERIFY_IDENTITY`, then run `source schema.sql`.)

---

## Part 4 — Deploy the app (Render)

1. Go to [render.com](https://render.com) and sign up (no card needed) — you can sign up directly with your GitHub account, which also handles repo access.
2. **New +** → **Web Service**.
3. Connect the `library-management-system` repo you pushed in Part 1.
4. Fill in:
   - **Name** — anything, e.g. `library-management-system`
   - **Runtime** — Python 3 (Render should auto-detect this from `requirements.txt`)
   - **Build Command** — `pip install -r requirements.txt`
   - **Start Command** — `gunicorn app:app`
   - **Instance Type** — **Free**
5. Open **Advanced** (or **Environment**) and add these environment variables:

| Key | Value |
|---|---|
| `DB_HOST` | the Host from Part 2 |
| `DB_PORT` | `4000` |
| `DB_USER` | the prefixed User from Part 2 |
| `DB_PASSWORD` | the password from Part 2 |
| `DB_NAME` | `library_db` |
| `DB_SSL` | `true` |
| `SECRET_KEY` | a random string — generate one locally with `python -c "import secrets; print(secrets.token_hex(32))"` and paste the output |

6. Click **Create Web Service**. Render will install dependencies, build, and deploy — watch the logs; the first deploy takes a couple of minutes.

---

## Part 5 — Verify it's live

1. Once the build finishes, Render gives you a URL like `https://library-management-system-xxxx.onrender.com`.
2. Open it. If it's been idle, the first load takes up to a minute — that's the free-tier spin-up, not a bug.
3. Log in with `admin` / `admin123`, and try adding a book or issuing a loan to confirm it's really talking to your TiDB database.

**Change the default password soon** — anyone who reads this guide knows those credentials. Easiest way: generate a new hash locally —

```bash
python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-new-password'))"
```

— then in TiDB Cloud's SQL Editor run:

```sql
UPDATE admins SET password = 'PASTE_THE_HASH_HERE' WHERE username = 'admin';
```

---

## Good to know

- **Redeploying**: every `git push` to `main` auto-redeploys on Render. No manual step.
- **Free tier limits**: Render gives 750 free instance-hours/month (plenty for one always-idle-sometimes app) and TiDB Cloud's free quota (5 GB storage, 50M request units/month) is far more than a project like this will use.
- **If it won't connect to the database**: double-check `DB_SSL=true` is set and that `DB_USER` includes the prefix exactly as shown in TiDB Cloud — that's the most common typo.
- **Outgrowing free**: if the 30–60s cold start becomes annoying, Render's cheapest always-on tier is about $7/month — same repo, same setup, you'd just change the instance type. Nothing else about this guide changes.
