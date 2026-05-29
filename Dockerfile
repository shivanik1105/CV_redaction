FROM python:3.11-slim

WORKDIR /app

# System deps for PyMuPDF, presidio, and sentence-transformers
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model used by presidio and the app
RUN python -m spacy download en_core_web_sm

# Pre-download sentence-transformers model so first request isn't slow
# all-mpnet-base-v2 is ~400MB and produces 768-dim embeddings
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-mpnet-base-v2')"

COPY . .

EXPOSE 7860

# Hugging Face Spaces requires the app on port 7860
# Use -w 1 (one worker) to stay within memory limits
CMD ["gunicorn", "-b", "0.0.0.0:7860", "-w", "1", "app:app"]
