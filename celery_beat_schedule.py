"""Celery Beat schedule configuration."""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Example: Run task every 5 minutes
    "run-placeholder-every-5-minutes": {
        "task": "app.tasks.placeholder_task.process_data_task",
        "schedule": 5 * 60,  # 5 minutes in seconds
        "args": ({"sample": "data"}, 1),
    },
    # Example: Run task every day at 2 AM
    "run-email-daily-at-2am": {
        "task": "app.tasks.placeholder_task.send_email_task",
        "schedule": crontab(hour=2, minute=0),
        "args": ("admin@example.com", "Daily Report", "Your daily report is ready"),
    },
    # Example: Run task every Monday at 9 AM
    "run-weekly-monday-9am": {
        "task": "app.tasks.placeholder_task.process_data_task",
        "schedule": crontab(day_of_week=0, hour=9, minute=0),
        "args": ({"type": "weekly"}, 1),
    },
    # Example: Run every hour
    "run-hourly": {
        "task": "app.tasks.placeholder_task.long_running_task",
        "schedule": 60 * 60,  # 1 hour
        "args": (300,),  # 5 minute duration
    },
}
