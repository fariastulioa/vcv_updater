FROM python:3.10

# Install cron package
RUN apt-get update && apt-get install -y cron

# Set the working directory
WORKDIR /vancouver_updater

# Copy the Python script to the container
COPY main.py /vancouver_updater/main.py
COPY run.sh /vancouver_updater/run.sh

# Install any dependencies if required
RUN pip install beautifulsoup4==4.11.1
RUN pip install python-telegram-bot==20.3
RUN pip install requests==2.31.0

# Set up the cron job
COPY crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab
RUN crontab /etc/cron.d/crontab
RUN touch /var/log/cron.log

# Run the command to start the cron service
CMD cron && tail -f /var/log/cron.log

# Run cron in the foreground
CMD cron -f
