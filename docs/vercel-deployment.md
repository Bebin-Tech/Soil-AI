# Online deployment

The root `vercel.json` deploys the Vite frontend and FastAPI backend together
using Vercel Services (beta). `/api/*` goes to the backend; frontend deep links
serve the SPA. The backend runs Alembic migrations during the build.

Connect a dedicated Neon PostgreSQL database to this project through Vercel
Storage. Set `ENVIRONMENT=production` and a fresh random `JWT_SECRET` (at least
32 characters) in Vercel. Database URLs supplied by Neon are normalized to the
psycopg driver. Production uses short-lived database connections with NullPool.
Keep preview databases separate from production before working on new schema
changes. Never copy the local `.env` or local account data into source control.

New PDF and spreadsheet reports are stored in PostgreSQL; temporary rendering
files are removed immediately. Existing local file reports remain downloadable
on the original host. Migration `0002` adds the nullable report content column
without changing those records. Apply migrations before starting updated local
containers as well.

Set `FRONTEND_URL` to the deployed origin before enabling SMTP password resets.
SMTP settings are optional; resets are unavailable until configured. Fertility
predictions remain unavailable pending dataset validation. The cloud database
starts empty and users register a new account.

Deployment protection is managed in Vercel project settings. Keep it enabled
unless the owner explicitly approves public access. The application also
requires its own user login for farm records and reports.
