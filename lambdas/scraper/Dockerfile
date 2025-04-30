FROM public.ecr.aws/lambda/python:3.12 AS base
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ── Python deps ────────────────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir awslambdaric

# ── Function code ──────────────────────────────────────────────────────────────
COPY . ${LAMBDA_TASK_ROOT}

# ── Entrypoint ─────────────────────────────────────────────────────────────────
ENTRYPOINT ["python", "-m", "awslambdaric"]
CMD ["scraper.lambda_handler"]