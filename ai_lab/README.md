# ai_lab/ — AI Experimentation (AI developer)

**Owner:** AI developer. Offline workspace for building the models that `backend/app/ai/` serves.
**Not deployed** — production only loads the *artifacts* this produces.

## Layout

| Folder | Purpose |
|--------|---------|
| `datasets/raw/` | Original, untouched data (attractions data, landmark images). Git-ignored. |
| `datasets/processed/` | Cleaned/split data ready for training. Git-ignored. |
| `notebooks/` | EDA and prototyping (Jupyter) |
| `training/` | Scripts: `build_kb.py` (RAG index), `train_cnn.py` (image model), `evaluate.py` (metrics) |
| `models/` | Saved artifacts (CNN weights, vectorizers, etc.) loaded by `backend/app/ai/`. Git-ignored except `.gitkeep`. |

## Rules

- **Reproducibility:** every artifact in `models/` must be regenerable from a script in `training/`.
  Document dataset sources & licenses in `datasets/README.md` (add when data lands).
- **Data & models are git-ignored** (see repo `.gitignore`) — they're large and/or licensed. Share
  them out-of-band and keep the build scripts in git.
- Keep experimentation here; only clean, load-ready code goes into `backend/app/ai/`.
