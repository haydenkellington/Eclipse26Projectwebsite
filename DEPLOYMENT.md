# Free Deployment Guide

This project deploys as two free services:

- **Frontend:** Vercel, using the `frontend/` folder
- **Backend:** Render Free Web Service, using the `backend/` folder

## Backend - Render Free

1. Go to Render and create a new Web Service from the GitHub repo.
2. Choose the free instance type.
3. Use these settings:
   - Root directory: `backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. Add this environment variable after the frontend is deployed:
   - `CORS_ORIGINS=https://your-vercel-url.vercel.app`

The repo also includes `render.yaml`, so Render can use it as a blueprint.

The backend pins Render to Python 3.12 with both `PYTHON_VERSION` in `render.yaml` and `backend/.python-version`. This avoids Python 3.14 package-build issues during deployment.

## Frontend - Vercel Free

1. Import the same GitHub repo into Vercel.
2. Set the project root directory to `frontend`.
3. Vercel should detect Next.js automatically.
4. Add this environment variable:
   - `NEXT_PUBLIC_API_URL=https://your-render-backend-url.onrender.com`
5. Deploy.

## Free Hosting Sleep Note

Render Free web services spin down after a period without inbound traffic. The first recommendation after inactivity can take around 30-60 seconds while the backend wakes up. The dashboard includes a public demo note telling users to expect a 30-45 second first load.

## Quick Public Test

After both services are live:

1. Open the Vercel URL in a private/incognito browser window.
2. Select a count with at least one pitch already thrown, such as `0-2`.
3. Choose a previous pitch, such as `FF`.
4. Confirm the dashboard shows:
   - model-recommended pitch
   - best available pitch
   - pitch comparison table
   - value key at the bottom

If the frontend says the backend did not respond, wait 30-45 seconds and change one input to retry.
