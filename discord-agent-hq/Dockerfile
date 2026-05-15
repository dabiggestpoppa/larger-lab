FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir discord.py python-dotenv requests

# Copy application files
COPY . .

# Create non-root user
RUN useradd -m -u 1000 agent && chown -R agent:agent /app
USER agent

# Run the bot
CMD ["python", "discord_bot.py"]