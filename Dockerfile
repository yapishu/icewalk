FROM python:3.10.2-bullseye

RUN apt-get update -y && apt-get install -y wget xvfb unzip jq
RUN apt-get install -y libxss1 libappindicator1 libgconf-2-4 \
  fonts-liberation libasound2 libnspr4 libnss3 libx11-xcb1 libxtst6 lsb-release xdg-utils \
  libgbm1 libnss3 libatk-bridge2.0-0 libgtk-3-0 libx11-xcb1 libxcb-dri3-0

RUN curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json > /tmp/versions.json

RUN CHROME_URL=$(jq -r '.channels.Stable.downloads.chrome[] | select(.platform=="linux64") | .url' /tmp/versions.json) && \
  wget -q --continue -O /tmp/chrome-linux64.zip $CHROME_URL && \
  unzip /tmp/chrome-linux64.zip -d /opt/chrome

RUN chmod +x /opt/chrome/chrome-linux64/chrome


RUN CHROMEDRIVER_URL=$(jq -r '.channels.Stable.downloads.chromedriver[] | select(.platform=="linux64") | .url' /tmp/versions.json) && \
  wget -q --continue -O /tmp/chromedriver-linux64.zip $CHROMEDRIVER_URL && \
  unzip /tmp/chromedriver-linux64.zip -d /opt/chromedriver && \
  chmod +x /opt/chromedriver/chromedriver-linux64/chromedriver

ENV CHROMEDRIVER_DIR /opt/chromedriver
ENV PATH $CHROMEDRIVER_DIR:$PATH

RUN rm /tmp/chrome-linux64.zip /tmp/chromedriver-linux64.zip /tmp/versions.json

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Expose the port the app runs on
EXPOSE 5001

# Command to run the application
CMD ["python", "app.py", "--port", "5001"]