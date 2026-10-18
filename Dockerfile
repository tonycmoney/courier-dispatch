# Stage 1: build the React dashboard
FROM node:22-alpine AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: install Python dependencies on the same Debian and Python
# version as the distroless runtime (Debian 12, Python 3.11)
FROM python:3.11-slim-bookworm AS deps
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY backend/requirements.txt .
RUN pip install --target /deps -r requirements.txt

# Stage 3: distroless runtime. No shell, no package manager, runs as
# the built in non root user. Far fewer OS packages to patch.
FROM gcr.io/distroless/python3-debian12:nonroot
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/deps:/app \
    DATABASE_URL=sqlite:////tmp/dispatch.db
WORKDIR /app

COPY --from=deps /deps /deps
COPY backend/app ./app
COPY --from=web /web/dist ./static

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD ["python3", "-c", "import os,urllib.request; urllib.request.urlopen('http://localhost:%s/api/health' % os.environ.get('PORT', '8000'))"]

ENTRYPOINT ["python3", "-m", "app.serve"]
