# Pitch Recommendation MVP

Starter implementation for a baseball pitch recommendation dashboard backed by a FastAPI recommendation engine.

## Project Structure

```text
backend/
  app.py
  model/
    encoder.py
    metrics.py
    pitch_mappings.py
    recommend.py
frontend/
  app/
  components/
  lib/
```

## Run Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

## Run Frontend

```bash
source use-node.sh
cd frontend
npm run dev
```

Open `http://localhost:3000`.

This workspace includes a project-local Node/npm install under `.tools/node`. If you open a new shell from the project root, run:

```bash
source use-node.sh
npm --version
```

## Notebook Export Targets

Replace the sample model logic with notebook outputs in these places:

- Q-table loading: `backend/model/recommend.py`
- State encoding: `backend/model/encoder.py`
- Pitch metadata: `backend/model/pitch_mappings.py`
- Precomputed metrics: `backend/model/metrics.py`

The corrected notebook copy lives at:

```text
backend/Spring26BaseballProj_Corrected.ipynb
```

After training `agent_aug` in the notebook, export the Q-table for the API:

```python
from export_q_artifacts import export_augmented_q_table

export_augmented_q_table(agent_aug, IDX_TO_PITCH)
```

The website interprets values this way:

```text
best_q_value = max(Q(state, pitch))
best_expected_delta_run_exp = -best_q_value
```

Higher Q is better for the pitcher. Lower expected delta run expectancy is better.

The API response is already shaped for the dashboard:

```http
POST /recommend
```

```json
{
  "balls": 1,
  "strikes": 2,
  "outs": 1,
  "on_1b": true,
  "on_2b": false,
  "on_3b": false,
  "batter_hand": "R",
  "pitcher_hand": "L",
  "prev_pitch": "FF",
  "available_pitches": ["FF", "SL", "CH"]
}
```
