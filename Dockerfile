# Use Python 3.13
FROM python:3.13-slim

# 1. Install system dependencies required for Playwright
# We group these to reduce image layers and size
RUN apt-get update && apt-get install -y \
    wget gnupg ca-certificates curl unzip \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 \
    libgtk-3-0 libgbm1 libasound2 libxcomposite1 libxdamage1 libxrandr2 \
    libxfixes3 libpango-1.0-0 libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# 2. Set working directory
WORKDIR /app

# 3. Install uv and Playwright
RUN pip install uv playwright

# 4. Install Playwright Browsers (Chromium only to save space)
RUN playwright install --with-deps chromium

# 5. Copy requirements file first (for caching)
COPY requirements.txt .

# 6. Install dependencies using uv's pip interface (Much faster and reliable here)
RUN uv pip install --system -r requirements.txt

# 7. Copy the rest of your application code
COPY . .

# 8. Create a non-root user (Required for security on HF Spaces)
RUN useradd -m -u 1000 user
# Give the user permission to write to the app folder (for downloads/temp files)
RUN chown -R user:user /app
# Switch to non-root user
USER user

# 9. Set Environment Variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV PATH="/home/user/.local/bin:$PATH"

# 10. Expose the port
EXPOSE 7860

# 11. Run the app using standard python command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]