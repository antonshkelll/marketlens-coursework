FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN useradd --uid 10001 --create-home marketlens && python experiment.py && chown -R marketlens:marketlens /app
USER marketlens
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=3)" || exit 1
CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8000"]
