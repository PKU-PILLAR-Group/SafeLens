FROM node:22-bookworm-slim AS explorer-web

WORKDIR /build
COPY apps/local_explorer/package.json apps/local_explorer/package-lock.json ./
RUN npm ci
COPY apps/local_explorer/ ./
RUN npm run build


FROM python:3.12-slim AS package-builder

WORKDIR /build
COPY . .
COPY --from=explorer-web /build/dist apps/local_explorer/dist
RUN python -m pip install --no-cache-dir build \
    && python scripts/prepare_explorer_distribution.py --skip-web-build \
    && python -m build --wheel --outdir /wheel


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=package-builder /wheel /wheel
RUN wheel="$(find /wheel -name 'safelens-*.whl' -print -quit)" \
    && python -m pip install --no-cache-dir "${wheel}[explorer]" \
    && rm -rf /wheel \
    && useradd --create-home --uid 10001 safelens \
    && mkdir -p /data \
    && chown -R safelens:safelens /data

USER safelens
EXPOSE 7860
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/api/health', timeout=3).read()"]

ENTRYPOINT ["safelens", "explorer"]
CMD ["--artifact-root", "/data", "--host", "0.0.0.0", "--port", "7860", "--allow-remote", "--no-browser"]
