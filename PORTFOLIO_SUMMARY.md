# Pitch Sequencing Dashboard - Portfolio Summary

## Short LinkedIn Post

I built an interactive baseball pitch-sequencing dashboard that uses a reinforcement learning model to recommend pitches based on count, base/out state, batter/pitcher handedness, previous pitch, and the pitcher's available arsenal.

The app turns a trained Q-table from a Jupyter notebook into a live FastAPI recommendation engine, then presents the output in a Baseball Savant-style dashboard built with Next.js. For each game state, it shows the model-recommended pitch, expected delta run expectancy, empirical Statcast run value, whiff rate, MLB usage frequency, sample size, and a pitch-by-pitch comparison table.

One feature I wanted to include was "best unavailable pitch," which shows whether the model prefers a pitch that is not currently in the selected arsenal. That makes the tool useful not only for pitch calling, but also for thinking about pitch design, scouting, and arsenal construction.

This project helped me connect sports analytics, reinforcement learning, model deployment, and frontend data visualization in one end-to-end product.

## Longer Project Description

This project is a baseball analytics dashboard that recommends pitch selections using a reinforcement learning model trained on pitch-level data. The model estimates pitcher reward using Q-values, where higher values indicate pitches the model expects to better prevent future run scoring in the current game state.

The dashboard lets a user define the situation:

- count
- outs
- runners on base
- batter handedness
- pitcher handedness
- previous pitch
- selected pitch arsenal

After the user selects a valid at-bat state, the backend returns the best available pitch, the best overall pitch, and a full comparison table across pitch types. The frontend explains the recommendation in plain English and includes confidence labels based on sample size, learned Q-value availability, and swing data.

The project is designed to feel like a lightweight internal baseball operations tool: clean layout, readable tables, restrained visual styling, and explainable model outputs rather than a black-box prediction.

## Technical Summary

- **Modeling:** reinforcement learning Q-table for pitch sequencing
- **Backend:** FastAPI recommendation API
- **Frontend:** Next.js, React, Tailwind CSS, Recharts
- **Data outputs:** Q-value, model-implied delta run expectancy, empirical Statcast delta run expectancy, whiff rate, batting average allowed, MLB frequency, model preference weight, and sample size
- **Deployment target:** free frontend hosting plus free backend hosting for demo access

## Important Model Note

The model is a decision-support tool, not a guarantee of real-world pitch outcomes. It estimates which pitch has the strongest learned value in similar historical states. Recommendations should be interpreted as directional signals that can support scouting, coaching, and pitch-design discussion.

## Public Demo Note

If hosted on a free backend, the model server may sleep after inactivity. The first recommendation after a long idle period may take about 30-45 seconds to load.
