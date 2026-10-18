# Stage 1: build the React dashboard
FROM node:22-alpine AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: install Python dependencies with the same Python as the runtime
FROM cgr.dev/chainguard/python:latest-dev AS deps
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
COPY backend/requirements.txt .
RUN pip install --target /build/deps -r requirements.txt

# Stage 3: minimal runtime. Chainguard's Wolfi based Python image is rebuilt
# daily from patched sources, has no shell or package manager, and runs as
# a non root user by default.
FROM cgr.dev/chainguard/python:latest
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/deps:/app \
    DATABASE_URL=sqlite:////tmp/dispatch.db
WORKDIR /app

COPY --from=deps /build/deps /deps
COPY backend/app ./app
COPY --from=web /web/dist ./static

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD ["python", "-c", "import os,urllib.request; urllib.request.urlopen('http://localhost:%s/api/health' % os.environ.get('PORT', '8000'))"]

ENTRYPOINT ["python", "-m", "app.serve"]
