# TourMateAI — Backend Implementation Guide (Learning Edition)

> A deep, file-by-file walkthrough of the backend as it exists today: the Flask app
> factory, the mock AI endpoints, and the full MySQL database layer (SQLAlchemy models +
> Flask-Migrate). Written to **teach**, not just document — every concept is explained.
>
> Covers two work sessions:
> 1. **Phase 0.5** — a runnable Flask app serving *mock* `/api/ai/*` endpoints.
> 2. **Feature 1.2** — the real MySQL database schema (8 tables) via SQLAlchemy + Flask-Migrate.

---

## Table of contents

1. [The big picture](#1-the-big-picture)
2. [Mental models you need first](#2-mental-models-you-need-first)
3. [Directory map of what exists](#3-directory-map-of-what-exists)
4. [File-by-file walkthrough](#4-file-by-file-walkthrough)
   - [run.py](#41-backendrunpy--the-entry-point)
   - [app/__init__.py](#42-appinitpy--the-application-factory)
   - [app/config.py](#43-appconfigpy--configuration)
   - [app/extensions.py](#44-appextensionspy--extension-singletons)
   - [app/ai/](#45-appai--the-ai-package-mock-for-now)
   - [app/models/](#46-appmodels--the-database-layer)
   - [app/seed.py](#47-appseedpy--sample-data)
   - [requirements.txt](#48-requirementstxt)
   - [migrations/](#49-migrations--flask-migrate--alembic)
   - [.env / .env.example](#410-env--envexample)
5. [How a request flows through the app](#5-how-a-request-flows-through-the-app)
6. [The Flask-Migrate workflow (cheat sheet)](#6-the-flask-migrate-workflow-cheat-sheet)
7. [How to view the database in a GUI (MySQL Workbench)](#7-how-to-view-the-database-in-a-gui-mysql-workbench)
8. [Command reference](#8-command-reference)
9. [Glossary](#9-glossary)

---

## 1. The big picture

TourMateAI's backend is a **single Flask application** (a "modular monolith" — one deployable
program, internally split into modules). It has three jobs:

1. Serve HTTP/JSON endpoints to the React frontend.
2. Talk to a **MySQL** database through an ORM (SQLAlchemy).
3. Host the **AI package** (`app/ai/`) behind `/api/ai/*` — currently returning *mock*
   responses so the frontend can be built before the real AI models exist.

Here's the shape of it today:

```
                          ┌─────────────────────────────────────────────┐
   Browser / React  ──►   │                Flask app                     │
   (HTTP requests)        │                                              │
                          │  create_app()  ← the "application factory"   │
                          │    ├─ loads Config (reads .env)              │
                          │    ├─ db.init_app()      → SQLAlchemy         │
                          │    ├─ migrate.init_app() → Flask-Migrate      │
                          │    ├─ registers ai_bp  → /api/ai/*  (mock)    │
                          │    └─ /health                                 │
                          │                                              │
                          │  models/  ── SQLAlchemy ORM classes ──┐      │
                          └──────────────────────────────────────┼──────┘
                                                                  │
                                                          ┌───────▼────────┐
                                                          │  MySQL 8.0     │
                                                          │  db: tourmateai│
                                                          │  8 tables      │
                                                          └────────────────┘
```

**Two things meet in this backend but stay separated:**

- The **web/business side** (config, models, routes, services) — normally your teammate's.
- The **AI side** (`app/ai/`) — yours. It only communicates through JSON contracts
  (`docs/api-contract.md`). Neither side reaches into the other's code.

Right now the web side has its **foundation** (config + database models + migrations), and the
AI side has **mock endpoints**. Real web routes and real AI models come in later phases.

---

## 2. Mental models you need first

If these five ideas click, every file below will make sense.

### (a) The "application factory" pattern
Instead of creating the Flask `app` object at module top-level, we create it inside a function
`create_app()`. Why? Because it lets us build **different apps from the same code** — e.g. a real
app that talks to MySQL, and a throwaway test app that talks to an in-memory SQLite database — by
passing a different config. It also avoids "import-time side effects" (code that runs just because
a file was imported), which are a classic source of bugs.

### (b) Blueprints
A **Blueprint** is a group of related routes you can register onto an app as a unit. Our AI
endpoints live in a blueprint (`ai_bp`) so the whole AI feature can be "plugged in" with one line:
`app.register_blueprint(ai_bp, url_prefix="/api/ai")`. This is exactly the boundary that lets the
AI and web tracks develop independently.

### (c) Extension singletons
Flask extensions like SQLAlchemy (`db`) and Migrate (`migrate`) are created **once**, in their own
module, *without* an app. Later, inside the factory, we "bind" them to the app with
`db.init_app(app)`. This two-step dance (create empty → bind later) is what prevents **circular
imports**: your model files import `db` from `extensions.py`, and the factory also imports `db` —
but nobody imports the factory, so there's no import loop.

### (d) ORM (Object-Relational Mapping)
SQLAlchemy lets you work with **Python classes instead of SQL**. A class = a table, an instance =
a row, an attribute = a column. `User.query.count()` becomes `SELECT COUNT(*) FROM Users`. You get
Python objects back instead of raw tuples. Relationships (`user.interactions`) auto-generate the
JOINs.

### (e) Migrations
As your models change over time, the database must change to match. **Flask-Migrate** (built on
**Alembic**) compares your models to the live database and generates a **migration script** —
a versioned Python file describing the exact `CREATE TABLE` / `ALTER TABLE` steps. Running
`flask db upgrade` applies them. This means the schema is **reproducible and version-controlled**:
your teammate runs the same migrations and gets an identical database.

---

## 3. Directory map of what exists

```
backend/
├── run.py                      # entry point: `python run.py` starts the dev server
├── requirements.txt            # pinned Python dependencies
├── venv/                       # virtual environment (git-ignored)
├── migrations/                 # Flask-Migrate / Alembic (generated)
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 963291c89037_initial_schema.py   # the initial "create all tables" migration
└── app/
    ├── __init__.py             # create_app() — the application factory
    ├── config.py               # env-driven configuration (builds the MySQL URI)
    ├── extensions.py           # db = SQLAlchemy(), migrate = Migrate()
    ├── seed.py                 # `flask seed-db` command → 15 sample attractions
    ├── ai/                     # the AI package (mounted at /api/ai/*)
    │   ├── __init__.py         # exports ai_bp
    │   └── blueprint.py        # mock /recommend, /chat, /identify, /health
    └── models/                 # SQLAlchemy models (one file per table)
        ├── __init__.py         # re-exports every model
        ├── user.py             # User
        ├── attraction.py       # Attraction
        ├── interaction.py      # Interaction (+ InteractionType enum)
        ├── itinerary.py        # Itinerary + ItineraryItem
        ├── feedback.py         # Feedback
        ├── chat_log.py         # ChatLog
        └── uploaded_image.py   # UploadedImage
```

---

## 4. File-by-file walkthrough

### 4.1 `backend/run.py` — the entry point

```python
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "development") != "production"
    app.run(host="0.0.0.0", port=port, debug=debug)
```

**What it does:** imports the factory, builds an app, and — *only when run directly* — starts
Flask's built-in development web server.

**Line by line:**
- `from app import create_app` — `app` here is the **package** `backend/app/`, and `create_app`
  is the function exported by its `__init__.py`.
- `app = create_app()` — this module-level `app` variable is important beyond `python run.py`: the
  `flask` command-line tool looks for it. That's why we run `flask --app run.py db upgrade` — Flask
  imports `run.py`, finds `app`, and uses it.
- `if __name__ == "__main__":` — the standard Python idiom meaning "only run this block when this
  file is executed directly, not when it's imported." So `flask` (which *imports* run.py) does not
  accidentally boot a second web server.
- `PORT` / `FLASK_ENV` from the environment — lets us change the port or turn debug off without
  editing code. `debug=True` gives auto-reload + detailed error pages in development.
- `host="0.0.0.0"` — listen on all network interfaces (so `127.0.0.1` and your LAN IP both work).

> ⚠️ This is a **development** server only. Production uses a real WSGI server (gunicorn/waitress) —
> that's a Phase 8 concern.

---

### 4.2 `app/__init__.py` — the application factory

```python
from flask import Flask, jsonify
from flask_cors import CORS

from .ai import ai_bp
from .config import Config
from .extensions import db, migrate
from .seed import register_cli


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app)

    db.init_app(app)
    migrate.init_app(app, db)

    from . import models  # noqa: F401

    app.register_blueprint(ai_bp, url_prefix="/api/ai")
    register_cli(app)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "tourmateai-backend"})

    return app
```

This is the **heart of the backend**. Walkthrough:

- `def create_app(config_class=Config)` — the factory. Takes a config class so tests can pass a
  different one (we used a SQLite `TestConfig` to validate the models without touching MySQL).
- `app = Flask(__name__)` — creates the Flask application. `__name__` tells Flask where the package
  root is (for locating templates/static files).
- `app.config.from_object(config_class)` — copies all UPPERCASE attributes from `Config` into
  `app.config` (so `SQLALCHEMY_DATABASE_URI`, `SECRET_KEY`, etc. become active settings).
- `CORS(app)` — enables **Cross-Origin Resource Sharing**. The React dev server runs on a different
  origin (e.g. `http://localhost:5173`) than the API (`:5000`). Browsers block cross-origin calls
  by default; this header-adding extension permits them. (Dev-only convenience; production locks it
  down.)
- `db.init_app(app)` — **binds** the SQLAlchemy extension to this app (remember: `db` was created
  empty in `extensions.py`). After this, models can run queries within an app context.
- `migrate.init_app(app, db)` — binds Flask-Migrate, giving us the `flask db …` commands.
- `from . import models` — **imports the models package so SQLAlchemy "sees" every table.** This is
  subtle but critical: a model class only registers itself with SQLAlchemy's metadata *when its
  module is imported*. If we never imported them, `flask db migrate` would find "no tables" and
  generate an empty migration. The `# noqa: F401` tells linters "yes, this import is unused on
  purpose — it's for its side effect."
- `app.register_blueprint(ai_bp, url_prefix="/api/ai")` — plugs the AI blueprint in. Every route in
  that blueprint gets the `/api/ai` prefix (so blueprint route `/chat` → real URL `/api/ai/chat`).
- `register_cli(app)` — attaches our custom `flask seed-db` command (defined in `seed.py`).
- `@app.get("/health")` — a tiny liveness endpoint. Load balancers / uptime checks hit this to ask
  "is the server alive?" It returns JSON `{"status":"ok",...}`.
- `return app` — hands the fully-assembled app back to `run.py` (or to `flask`).

**History:** this file started life as a *placeholder* that only mounted the AI mock. In Feature 1.2
we grew it into the real factory (config + db + migrate + models + seed) — while keeping the AI
mount byte-for-byte compatible, so nothing on the AI side broke.

---

### 4.3 `app/config.py` — configuration

```python
import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

_BACKEND_DIR = Path(__file__).resolve().parents[1]   # backend/
_REPO_ROOT = _BACKEND_DIR.parent                     # repo root

load_dotenv(_REPO_ROOT / ".env")
load_dotenv(_BACKEND_DIR / ".env", override=True)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")

    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "tourmateai")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

**Purpose:** centralize all settings and read secrets from `.env` (never hard-coded).

- `Path(__file__).resolve().parents[1]` — `__file__` is this file's path; `.parents[1]` walks up
  two levels (`app/` → `backend/`). We compute paths so `.env` loads correctly no matter what
  directory you launch from.
- `load_dotenv(...)` — python-dotenv reads a `.env` file and pushes its `KEY=value` lines into
  `os.environ`. We load the repo-root `.env` first, then `backend/.env` with `override=True` so a
  backend-local file can override the shared one if it exists.
- `os.environ.get("DB_USER", "root")` — read an env var, falling back to a default if absent.
- **The connection URI** is the single most important line. Its anatomy:
  ```
  mysql+pymysql://  root  :  <password>  @  localhost : 3306 / tourmateai
  └─dialect+driver┘ └user┘   └password┘    └─host──┘ └port┘ └database┘
  ```
  - `mysql` = the database dialect (SQLAlchemy speaks many: postgresql, sqlite, …).
  - `pymysql` = the specific Python driver library that talks the MySQL wire protocol.
  - `quote_plus(DB_PASSWORD)` = URL-encodes the password, so special characters like `@` or `#` in
    a password don't break the URI's structure.
- `SQLALCHEMY_TRACK_MODIFICATIONS = False` — disables a Flask-SQLAlchemy signalling feature we don't
  use; leaving it on wastes memory and prints a warning.

> **Why a class?** `from_object(Config)` copies the class's UPPERCASE attributes into `app.config`.
> Subclasses (`DevConfig`, `ProdConfig`) can later override individual values — a common pattern.

---

### 4.4 `app/extensions.py` — extension singletons

```python
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
```

Four lines, one big idea. These two objects are created **without an app** and live in their own
module so that:

1. **Model files** (`models/user.py` etc.) can do `from ..extensions import db` and use
   `db.Model`, `db.Column`, … .
2. **The factory** can do `from .extensions import db, migrate` and call `db.init_app(app)`.

Because `extensions.py` imports nothing from `app/__init__.py`, there's **no circular import**.
If instead we defined `db` inside `__init__.py`, then `models` would import `__init__`, and
`__init__` imports `models` → an import loop that crashes. This module breaks that loop.

`db` is your gateway to everything database: `db.Model` (base class for models), `db.Column`,
`db.session` (the unit of work for reads/writes), `db.relationship`, `db.create_all()`, etc.

---

### 4.5 `app/ai/` — the AI package (mock for now)

This is **your** territory. It's a self-contained package the web app mounts as a blueprint.

**`app/ai/__init__.py`**
```python
from .blueprint import ai_bp
__all__ = ["ai_bp"]
```
Just re-exports the blueprint so the factory can `from .ai import ai_bp`.

**`app/ai/blueprint.py`** — defines three mock endpoints plus a health check:

```python
ai_bp = Blueprint("ai", __name__)
IDENTIFY_CONFIDENCE_THRESHOLD = 0.5

@ai_bp.get("/health")           #  → GET  /api/ai/health
@ai_bp.post("/recommend")       #  → POST /api/ai/recommend
@ai_bp.post("/chat")            #  → POST /api/ai/chat
@ai_bp.post("/identify")        #  → POST /api/ai/identify  (multipart image)
```

Key teaching points:
- **`Blueprint("ai", __name__)`** — creates the group. The `url_prefix="/api/ai"` is applied later
  by the factory, so routes here are written *relative* (`/chat`, not `/api/ai/chat`).
- **"Lightly dynamic" mocks** — they don't run real ML, but they *echo request data back* so the
  frontend can prove its wiring works. Examples:
  - `/recommend` reflects your `interests` into each recommendation's `reason`.
  - `/chat` echoes `session_id` and `message` into the reply, and returns `sources: []`-style data
    (the RAG contract always returns `sources`).
  - `/identify` reads the uploaded file, echoes its filename, and supports a low-confidence branch
    (`?confidence=0.2` → `{"landmark": null, "message": "Not recognized"}`) so the "not recognized"
    UI can be built.
- **Input validation** — `/chat` returns HTTP 400 if `message` is empty; `/identify` returns 400 if
  no file is attached. Mocks still enforce the contract's error shapes (`{"error": "..."}`).
- **`request.get_json(silent=True) or {}`** — safely parse the JSON body; `silent=True` returns
  `None` instead of raising on bad/missing JSON, and `or {}` gives an empty dict fallback.

When the real models land (Phases 3–5), only the *insides* of these functions change — the URLs and
JSON shapes stay identical, so the frontend never needs rewriting. That's the whole point of the
contract-first boundary.

---

### 4.6 `app/models/` — the database layer

Each file defines one (or two) **model classes**. A model class maps to a table; its attributes map
to columns. All inherit from `db.Model`.

#### The pattern, using `attraction.py` as the template

```python
from datetime import datetime
from ..extensions import db

class Attraction(db.Model):
    __tablename__ = "Attractions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(80), index=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    image_url = db.Column(db.String(500))
    avg_rating = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    interactions = db.relationship("Interaction", back_populates="attraction",
                                   cascade="all, delete-orphan")
    itinerary_items = db.relationship("ItineraryItem", back_populates="attraction",
                                      cascade="all, delete-orphan")
    feedback = db.relationship("Feedback", back_populates="attraction",
                               cascade="all, delete-orphan")
```

Decoding every piece:
- **`__tablename__ = "Attractions"`** — the real table name in MySQL. (Without it, SQLAlchemy would
  guess. We set it explicitly so the SQL is predictable.)
- **`db.Column(type, ...options)`** — one column. Types used across our models:
  - `db.Integer` — whole numbers (IDs, foreign keys, day_number).
  - `db.String(n)` — `VARCHAR(n)`, short text with a length limit.
  - `db.Text` — long text, no fixed limit (descriptions, comments).
  - `db.Float` — decimals (lat/lng, rating).
  - `db.DateTime` / `db.Date` — timestamps / calendar dates.
  - `db.JSON` — a native MySQL JSON column (used for `User.preferences` and
    `UploadedImage.recognition_result`).
  - `db.Enum(PyEnum)` — a fixed set of allowed values (see Interaction below).
- **Column options:**
  - `primary_key=True` — the unique row identifier; MySQL auto-increments it.
  - `nullable=False` — the column is required (`NOT NULL`).
  - `unique=True` — no two rows may share this value (e.g. `email`, `firebase_uid`).
  - `index=True` — build a database **index** on this column so lookups/filters are fast.
  - `default=…` — value used when you don't supply one. `default=datetime.utcnow` (note: passed
    **without** `()` — we hand SQLAlchemy the *function*, and it calls it fresh at each insert, so
    every row gets its own timestamp).
- **`db.relationship(...)`** — this is **not a column**; it's a Python-level convenience that lets
  you navigate between related objects (`attraction.feedback` gives you a list of `Feedback`
  objects). It reads/writes via the foreign keys defined on the *other* table.
  - `back_populates="attraction"` — names the matching relationship on the other class, keeping both
    sides in sync (set one, the other updates).
  - `cascade="all, delete-orphan"` — if you delete an Attraction through the ORM, its related
    children (feedback, interactions, itinerary items) are deleted too, and any child "orphaned"
    from its parent is removed. This mirrors the database-level `ON DELETE CASCADE`.

#### Foreign keys, using `interaction.py`

```python
import enum
from datetime import datetime
from ..extensions import db

class InteractionType(enum.Enum):
    view = "view"
    like = "like"
    visit = "visit"

class Interaction(db.Model):
    __tablename__ = "Interactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,
                        db.ForeignKey("Users.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    attraction_id = db.Column(db.Integer,
                        db.ForeignKey("Attractions.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    interaction_type = db.Column(db.Enum(InteractionType), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="interactions")
    attraction = db.relationship("Attraction", back_populates="interactions")

    __table_args__ = (
        db.Index("ix_interactions_user_attraction", "user_id", "attraction_id"),
    )
```

- **`db.ForeignKey("Users.id", ondelete="CASCADE")`** — declares that `user_id` must equal some
  existing `Users.id`. This is the constraint that makes the database **reject** an interaction for
  a non-existent user (exactly what we proved in the FK test). `ondelete="CASCADE"` means: if that
  user is deleted, delete their interactions automatically — enforced by MySQL itself, not just the
  ORM.
- **`InteractionType(enum.Enum)`** — a Python enum with three members. `db.Enum(InteractionType)`
  turns it into a MySQL `ENUM('view','like','visit')` column, so the database only allows those
  three strings. In Python you assign `InteractionType.view`; in SQL it's stored as `'view'`.
- **`__table_args__ = (db.Index("ix_...", "user_id", "attraction_id"),)`** — a **composite index**
  across two columns. The recommender will frequently query "all interactions for user X" or
  "for user X and attraction Y"; this index makes those queries fast. (It's a tuple — note the
  trailing comma.)

#### One-to-many & the parent side, using `user.py`

`User` is a **parent** to many child tables. Each `db.relationship` here has a matching
`ForeignKey` + `back_populates` on the child:

```python
interactions   = db.relationship("Interaction",  back_populates="user", cascade="all, delete-orphan")
itineraries    = db.relationship("Itinerary",     back_populates="user", cascade="all, delete-orphan")
feedback       = db.relationship("Feedback",      back_populates="user", cascade="all, delete-orphan")
chat_logs      = db.relationship("ChatLog",       back_populates="user", cascade="all, delete-orphan")
uploaded_images= db.relationship("UploadedImage", back_populates="user", cascade="all, delete-orphan")
```

So `some_user.itineraries` returns a list of that user's `Itinerary` objects, and deleting the user
cascades to all of them. `User.preferences` is a `db.JSON` column — you store a Python dict like
`{"interests": ["beach"], "budget": "medium", "duration_days": 3}` and get the same dict back.

#### Two models in one file, using `itinerary.py`

`Itinerary` (the trip) and `ItineraryItem` (a stop within the trip) live together because they're
tightly coupled. `ItineraryItem` has **two** foreign keys — `itinerary_id` (its parent trip) and
`attraction_id` (which place it points to) — plus `day_number` and `order_index` to sequence the
plan. The `Itinerary.items` relationship even sorts them:
`order_by="ItineraryItem.day_number, ItineraryItem.order_index"`.

#### The remaining models (same pattern, quick tour)
- **`feedback.py`** — `Feedback`: `rating` (1–5 integer) + `comment` (text), tied to a user and an
  attraction.
- **`chat_log.py`** — `ChatLog`: one row per chatbot turn. `message` is required; `response` is
  nullable because your teammate's chatbot fills it in later.
- **`uploaded_image.py`** — `UploadedImage`: `image_url` + a `recognition_result` JSON column the
  vision model populates.

#### `app/models/__init__.py` — the collector

```python
from ..extensions import db
from .attraction import Attraction
from .chat_log import ChatLog
from .feedback import Feedback
from .interaction import Interaction, InteractionType
from .itinerary import Itinerary, ItineraryItem
from .uploaded_image import UploadedImage
from .user import User

__all__ = ["db", "User", "Attraction", "Interaction", "InteractionType",
           "Itinerary", "ItineraryItem", "Feedback", "ChatLog", "UploadedImage"]
```

Importing this one package imports **all** model modules, which is what registers every table with
SQLAlchemy's metadata. That's why the factory does `from . import models` — one line, all tables
visible to Alembic. `__all__` documents the public names and controls `from app.models import *`.

---

### 4.7 `app/seed.py` — sample data

```python
import click
from flask.cli import with_appcontext
from .extensions import db
from .models import Attraction

SAMPLE_ATTRACTIONS = [ {"name": "Sigiriya Rock Fortress", "category": "Heritage",
                        "latitude": 7.9570, "longitude": 80.7603, "description": "..."}, ... ]  # 15 items

@click.command("seed-db")
@with_appcontext
def seed_db_command():
    """Insert sample Sri Lankan attractions (idempotent)."""
    existing = Attraction.query.count()
    if existing:
        click.echo(f"Attractions already present ({existing} rows); skipping seed.")
        return
    db.session.add_all(Attraction(**data) for data in SAMPLE_ATTRACTIONS)
    db.session.commit()
    click.echo(f"Seeded {len(SAMPLE_ATTRACTIONS)} attractions.")

def register_cli(app):
    app.cli.add_command(seed_db_command)
```

- **`@click.command("seed-db")`** — Flask uses **Click** for CLI commands. This registers a new
  subcommand you run as `flask seed-db`.
- **`@with_appcontext`** — pushes an "application context" so the command can use `db.session` and
  the models. (Database work needs to know *which app* it belongs to.)
- **Idempotent** — it first counts existing rows and skips if the table is already seeded, so you
  can run it repeatedly without creating duplicates.
- **`Attraction(**data)`** — Python "dict unpacking": turns `{"name": "...", "category": "..."}`
  into keyword arguments `Attraction(name="...", category="...")`.
- **`db.session.add_all(...)` + `db.session.commit()`** — stage all rows in the session's
  "unit of work", then flush them to the database in one transaction. Nothing is written until
  `commit()`.
- **`register_cli(app)`** — called by the factory to attach the command.

The 15 seeded attractions are real Sri Lankan sites (Sigiriya, Kandy Temple, Galle Fort, Ella,
Yala, Adam's Peak, Dambulla, Nuwara Eliya, Mirissa, Anuradhapura, Polonnaruwa, Horton Plains,
Trincomalee, Unawatuna, Pinnawala) with approximate coordinates and short descriptions — enough
real data to build the frontend and later the recommender against.

---

### 4.8 `requirements.txt`

The pinned dependency list. The database-relevant entries:
```
Flask-SQLAlchemy==3.1.1        # the ORM integration for Flask (gives us db.Model, db.session)
Flask-Migrate==4.1.0           # migrations (wraps Alembic) → the `flask db …` commands
PyMySQL==1.2.0                 # the pure-Python MySQL driver named in the connection URI
SQLAlchemy==2.0.51             # the underlying ORM/SQL toolkit
python-dotenv==1.2.2           # loads the .env file
```
Versions are **pinned** (`==`) so everyone installs the exact same versions. Only *direct*
dependencies are listed; pip resolves the transitive ones.

---

### 4.9 `migrations/` — Flask-Migrate / Alembic

This folder was **generated** by `flask db init`; you rarely edit it by hand (except the version
scripts). Contents:

- **`alembic.ini`** — Alembic's config file (logging, script location).
- **`env.py`** — the script Alembic runs on every migrate/upgrade. Flask-Migrate's version wires
  Alembic to *your app's* `db.metadata` and connection, so autogenerate knows about your models.
- **`script.py.mako`** — the template new migration files are generated from.
- **`versions/963291c89037_initial_schema.py`** — **the actual migration.** Its filename starts
  with a random **revision id** (`963291c89037`). Inside are two functions:
  - `upgrade()` — the `op.create_table(...)` / `op.create_index(...)` calls that build all 8 tables
    with their columns, foreign keys, and indexes. This is what `flask db upgrade` ran.
  - `downgrade()` — the reverse (`op.drop_table(...)`), so you can roll back with `flask db
    downgrade`.

**How the initial migration was produced:**
1. `flask db init` → created the `migrations/` folder (once per project).
2. `flask db migrate -m "initial schema"` → Alembic compared "models say 8 tables" vs
   "database has 0 tables" and wrote the `upgrade()`/`downgrade()` for the difference.
3. `flask db upgrade` → executed `upgrade()` against MySQL, creating everything, and recorded the
   revision id in a bookkeeping table called **`alembic_version`** (that's the 9th table you'll see
   — it just stores "which migration is currently applied").

**Commit this folder to git.** Your teammate clones the repo, runs `flask db upgrade`, and gets an
identical schema without you sending them any SQL.

---

### 4.10 `.env` / `.env.example`

- **`.env.example`** (committed) — a template listing every variable name with blank/sample values.
  It documents *what* configuration exists without leaking secrets.
- **`.env`** (git-ignored, you created it) — your real local values, including the MySQL password.
  The backend reads it via `python-dotenv` in `config.py`. **Never commit this.** Your teammate
  keeps their own `.env` with their own MySQL password.

The database-relevant keys:
```
DB_HOST=localhost
DB_PORT=3306
DB_NAME=tourmateai
DB_USER=root
DB_PASSWORD=********      # your local MySQL password
SECRET_KEY=...
```

---

## 5. How a request flows through the app

Take `POST /api/ai/recommend` as an example end-to-end trace:

1. Browser sends `POST http://localhost:5000/api/ai/recommend` with a JSON body.
2. Flask's dev server (started by `run.py`) receives it.
3. Flask matches the URL: `/api/ai` (blueprint prefix) + `/recommend` (route) → the `recommend()`
   function in `app/ai/blueprint.py`.
4. That function parses the JSON, builds a mock response echoing your interests, and returns
   `jsonify({...})`.
5. Flask serializes it to a JSON HTTP response and sends it back.

A database-backed endpoint (coming later) would additionally, in step 4, use `db.session` /
`SomeModel.query...` to read or write MySQL through SQLAlchemy, which turns your Python into SQL,
sends it over the PyMySQL driver to MySQL, and maps the result rows back into model objects.

---

## 6. The Flask-Migrate workflow (cheat sheet)

Whenever you **change a model** (add a column, new table, etc.), the loop is:

```bash
# 1. edit your model files (add/remove columns, tables, indexes)

# 2. generate a migration describing the change
flask --app run.py db migrate -m "add phone to users"

# 3. REVIEW the generated file in migrations/versions/ (autogenerate isn't perfect!)

# 4. apply it to your database
flask --app run.py db upgrade
```

Other useful commands:
```bash
flask --app run.py db downgrade     # undo the last migration
flask --app run.py db current       # show which revision is applied
flask --app run.py db history       # list all migrations
```

On Windows PowerShell you can set the app once so you don't repeat `--app run.py`:
```powershell
$env:FLASK_APP = "run.py"
flask db upgrade
```

> **Golden rule:** always open and read the autogenerated migration before `upgrade`. Alembic can
> miss things (e.g. certain column type changes) or generate drops you didn't intend.

---

## 7. How to view the database in a GUI (MySQL Workbench)

You already have **MySQL Workbench 8.0** installed at
`C:\Program Files\MySQL\MySQL Workbench 8.0\MySQLWorkbench.exe`. It came with your MySQL install.

### Step 1 — Open Workbench
Press the Windows key, type **"MySQL Workbench"**, open it. (Or double-click the exe path above.)

### Step 2 — Connect to your local MySQL
On the home screen you'll likely see a connection tile named **"Local instance MySQL80"**.
- **If it's there:** click it. When prompted, enter your MySQL **root password** (the same one in
  your `.env`). Tick "Save password in vault" so you don't retype it.
- **If it's NOT there:** click the **➕** next to "MySQL Connections" and fill in:
  - Connection Name: `TourMateAI`
  - Hostname: `127.0.0.1`  •  Port: `3306`
  - Username: `root`
  - Click **"Store in Vault..."** and enter your password.
  - Click **Test Connection** (should say success), then **OK**, then click the new tile.

### Step 3 — Find the `tourmateai` database
- On the left is the **SCHEMAS** panel. Click the little **refresh** icon at its top if the list
  looks stale.
- You'll see **`tourmateai`** in the list. Click the arrow to expand it → expand **Tables**.
- You should see your 8 tables (shown lowercase on Windows): `attractions`, `chatlogs`,
  `feedback`, `interactions`, `itineraries`, `itineraryitems`, `uploadedimages`, `users`
  (plus `alembic_version`).

### Step 4 — View the data in a table
- Hover over **`attractions`** → click the **grid/table icon** that appears (tooltip:
  "Select Rows - Limit 1000"). A results grid opens showing your 15 seeded attractions.
- You can edit cells inline and click **Apply** to write changes (careful — that's live data).

### Step 5 — Run your own SQL (optional)
Click the **SQL editor** (the first toolbar icon, "Create a new SQL tab"), then type and run
(Ctrl+Enter or the ⚡ lightning icon):
```sql
USE tourmateai;

-- all attractions
SELECT id, name, category, latitude, longitude FROM Attractions ORDER BY id;

-- inspect the exact table definition, incl. foreign keys
SHOW CREATE TABLE ItineraryItems;

-- list every foreign key in the database
SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'tourmateai' AND REFERENCED_TABLE_NAME IS NOT NULL;
```

### Step 6 — See relationships visually (optional, nice for learning)
Workbench can reverse-engineer a diagram (ER diagram) from your live database:
- Menu **Database → Reverse Engineer…** (Ctrl+R).
- Pick your connection → Next through the wizard → select the `tourmateai` schema → Finish.
- You'll get an **EER diagram** with all tables and the foreign-key lines between them — a great
  way to *see* how Users → Interactions → Attractions connect.

> **Alternatives if you ever want them:** **DBeaver** (free, works with any database),
> **phpMyAdmin** (web-based), or the command line: `mysql -u root -p tourmateai`.
>
> **Case note:** on Windows, MySQL stores table names lowercased by default, but SQL is
> case-insensitive for table names here — so `SELECT * FROM Attractions` and `FROM attractions`
> both work.

---

## 8. Command reference

```powershell
# --- one-time setup ---
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt

# --- database lifecycle ---
$env:FLASK_APP = "run.py"
flask db upgrade            # create/update all tables to the latest migration
flask seed-db               # insert the 15 sample attractions (idempotent)

# --- when you change a model ---
flask db migrate -m "describe change"   # generate migration (then REVIEW it)
flask db upgrade                        # apply it

# --- run the app ---
python run.py              # dev server on http://localhost:5000
#   GET  /health
#   GET  /api/ai/health
#   POST /api/ai/recommend | /api/ai/chat | /api/ai/identify   (mock)
```

---

## 9. Glossary

| Term | Meaning |
|------|---------|
| **ORM** | Object-Relational Mapping — work with Python classes/objects instead of raw SQL. |
| **SQLAlchemy** | The Python ORM/SQL toolkit doing that mapping. |
| **Flask-SQLAlchemy** | Thin Flask integration that gives us `db.Model`, `db.session`, etc. |
| **Alembic** | The migration engine that diffs models vs DB and writes migration scripts. |
| **Flask-Migrate** | Flask wrapper around Alembic → the `flask db …` commands. |
| **PyMySQL** | Pure-Python driver that actually speaks to MySQL over the network. |
| **Application factory** | The `create_app()` function that builds a configured Flask app. |
| **Blueprint** | A registrable group of routes (our `ai_bp`). |
| **Extension singleton** | An extension object (`db`, `migrate`) created once, bound to the app later. |
| **Migration** | A versioned script describing a schema change (create/alter/drop). |
| **Foreign key (FK)** | A column that must reference an existing row in another table. |
| **ON DELETE CASCADE** | Deleting a parent row auto-deletes its child rows. |
| **Index** | A database structure that speeds up lookups on a column (or set of columns). |
| **Primary key** | The unique identifier column of a row (`id`, auto-incremented). |
| **`.env`** | Git-ignored file holding local secrets/config (DB password, keys). |
| **CORS** | Browser mechanism that must be permitted for the React app to call the API. |
| **`db.session`** | SQLAlchemy's "unit of work" — you `add()` objects then `commit()`. |
| **`alembic_version`** | Bookkeeping table storing which migration is currently applied. |

---

*Generated as a learning companion to the TourMateAI backend. As the code evolves (real web routes,
real AI models, auth), extend this guide so it stays the single place to understand the backend.*
