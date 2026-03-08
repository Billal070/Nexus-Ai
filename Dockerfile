FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot source
COPY bot.py .

# Create non-root user for security
RUN useradd -m botuser && chown -R botuser /app
USER botuser

# Run the bot
CMD ["python", "bot.py"]
