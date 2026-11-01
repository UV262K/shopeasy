FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Expand the storefront sources during image build; this keeps CI and runtime in sync.
RUN python -c "import zipfile; z=zipfile.ZipFile('storefront-source.zip'); [z.extract(p, '.') for p in ('app.py', 'static/index.html')]"
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 5000
CMD ["python", "app.py"]
