FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Extract only the Flask app from the source bundle; the storefront HTML is maintained as a normal repository file.
RUN python -c "import zipfile; z=zipfile.ZipFile('storefront-source.zip'); z.extract('app.py', '.')"
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 5000
CMD ["python", "app.py"]
