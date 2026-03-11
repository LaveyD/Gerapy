# Separate Frontend/Backend Deployment

This document describes deployment after splitting the repository into `frontend/` and `backend/`.

## Directories

* `frontend/`: Vue frontend project (build output defaults to `backend/core/templates`)
* `backend/`: Django backend service
* `gerapy/`: CLI, spider templates, and shared capabilities

## Deployment Flow

1. **Deploy backend**
   * Install Python dependencies and initialize workspace:
   ```bash
   gerapy init
   cd gerapy
   gerapy migrate
   gerapy initadmin
   ```
   * Start backend service:
   ```bash
   gerapy runserver 0.0.0.0:8000
   ```

2. **Deploy frontend**
   * Build in frontend directory:
   ```bash
   cd frontend
   npm install
   npm run build
   ```
   * Serve built static assets and reverse proxy `/api/*` to backend service.

## Recommendations

* Deploy frontend and backend independently (frontend on Nginx/CDN, backend as app service).
* Persist backend workspace directories: `dbs/`, `projects/`, and `logs/`.
* Set `APP_DEBUG=false` in production and restrict database network access.
