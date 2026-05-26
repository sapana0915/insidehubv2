# Celery Task Queue Setup Guide

This FastAPI boilerplate includes **Celery** for asynchronous task processing with **RabbitMQ** as the message broker, **Redis** for result backend, and **Flower** for monitoring.

## Architecture

```
FastAPI App
    ↓
RabbitMQ (Message Broker)
    ↓
Celery Worker (Process Tasks)
    ↓
Redis (Result Backend)
    ↑
Flower (Monitor Tasks)
    ↑
Celery Beat (Scheduled Tasks)
```

## Components

1. **RabbitMQ** - Message broker (port 5672)
2. **Redis** - Result backend and cache (port 6379)
3. **Celery Worker** - Processes async tasks
4. **Celery Beat** - Schedules periodic tasks
5. **Flower** - Web UI for monitoring (port 5555)

## Quick Start

### 1. Using Docker (Recommended)

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (database)
- Redis (result backend)
- RabbitMQ (message broker)
- FastAPI app
- Celery worker
- Celery Beat (scheduler)
- Flower (monitoring)

### 2. Local Setup

#### Prerequisites

```bash
pip install -r requirements.txt
```

#### Start Redis (required)

```bash
redis-server
# or with Docker
docker run -d -p 6379:6379 redis:7-alpine
```

#### Start RabbitMQ (required)

```bash
# macOS with Homebrew
brew install rabbitmq
brew services start rabbitmq

# or with Docker
docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:3.12-management-alpine
```

#### Start Celery Worker

```bash
celery -A app.celery_app worker -l info
```

#### Start Celery Beat (Optional - for scheduled tasks)

```bash
celery -A app.celery_app beat -l info
```

#### Start Flower (Optional - for monitoring)

```bash
celery -A app.celery_app flower
```

## Creating Tasks

### Basic Task

Create tasks in `app/tasks/` folder:

```python
from celery import shared_task

@shared_task
def my_task(param1, param2):
    # Do something
    return {"status": "success", "result": param1 + param2}
```

### Task with Retry

```python
from celery import shared_task
from app.celery_app import celery_app

@celery_app.task(bind=True, max_retries=3)
def my_retry_task(self, data):
    try:
        # Do something
        return {"status": "success"}
    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60)
```

### Task with Custom Configuration

```python
@celery_app.task(
    bind=True,
    max_retries=5,
    default_retry_delay=60,
    time_limit=300,  # Hard limit
    soft_time_limit=250,  # Soft limit
)
def long_task(self, data):
    # Task logic
    return {"status": "completed"}
```

## Using Tasks in Routes

### Fire and Forget

```python
from fastapi import APIRouter
from app.tasks.placeholder_task import send_email_task

router = APIRouter()

@router.post("/send-email")
async def send_email(email: str, subject: str):
    # Fire and forget - returns immediately
    send_email_task.delay(email, subject, "Hello!")
    return {"message": "Email queued for sending"}
```

### Get Task Result

```python
from celery.result import AsyncResult
from app.celery_app import celery_app

@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    
    return {
        "task_id": task_id,
        "state": result.state,
        "result": result.result if result.successful() else None,
        "error": str(result.info) if result.failed() else None,
    }
```

### Wait for Result

```python
@router.post("/send-email-wait")
async def send_email_wait(email: str, subject: str):
    # Wait for result (blocking)
    result = send_email_task.apply_async(
        args=(email, subject, "Hello!"),
        timeout=30  # Wait max 30 seconds
    )
    
    if result.successful():
        return {"status": "success", "result": result.result}
    else:
        return {"status": "error", "error": str(result.info)}
```

## Scheduled Tasks (Celery Beat)

Configure periodic tasks in `celery_beat_schedule.py`:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Run every 5 minutes
    "run-every-5-min": {
        "task": "app.tasks.placeholder_task.process_data_task",
        "schedule": 5 * 60,  # seconds
        "args": ({"data": "value"}, 1),
    },
    
    # Run daily at 2 AM
    "run-daily-2am": {
        "task": "app.tasks.placeholder_task.send_email_task",
        "schedule": crontab(hour=2, minute=0),
        "args": ("admin@example.com", "Daily Report", "Your report"),
    },
    
    # Run every Monday at 9 AM
    "run-weekly": {
        "task": "app.tasks.placeholder_task.process_data_task",
        "schedule": crontab(day_of_week=0, hour=9, minute=0),
        "args": ({"type": "weekly"}, 1),
    },
    
    # Run every hour
    "run-hourly": {
        "task": "app.tasks.placeholder_task.long_running_task",
        "schedule": 60 * 60,  # 1 hour
        "args": (300,),  # 5 minute duration
    },
}
```

### Crontab Patterns

```python
from celery.schedules import crontab

# Every hour
crontab(minute=0)

# Every day at 2:30 AM
crontab(hour=2, minute=30)

# Every Monday at 9 AM
crontab(day_of_week=0, hour=9)

# Every 15 minutes
crontab(minute="*/15")

# Weekdays (Mon-Fri) at 5 PM
crontab(day_of_week="mon-fri", hour=17)

# 1st day of month at midnight
crontab(day_of_month=1, hour=0, minute=0)
```

## Monitoring with Flower

Access Flower at **http://localhost:5555**

### Features
- View all tasks (active, scheduled, completed, failed)
- Monitor worker status and stats
- View task details and results
- Real-time task execution graph
- Retry failed tasks
- View logs

## Configuration

Environment variables in `.env`:

```bash
# Celery Broker (RabbitMQ)
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//

# Celery Result Backend (Redis)
CELERY_RESULT_BACKEND_URL=redis://localhost:6379/0

# Redis
REDIS_URL=redis://localhost:6379/0
```

### Advanced Configuration

In `app/celery_app.py`:

```python
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task tracking
    task_track_started=True,
    task_time_limit=30 * 60,      # 30 min hard limit
    task_soft_time_limit=25 * 60,  # 25 min soft limit
    
    # Worker configuration
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)
```

## Placeholder Tasks

The boilerplate includes example tasks in `app/tasks/placeholder_task.py`:

1. **send_email_task** - Async email sending
2. **process_data_task** - Data processing task
3. **long_running_task** - Long-running background job
4. **retry_task_example** - Example of retry logic

### Using Placeholders

```python
from app.tasks.placeholder_task import send_email_task, process_data_task

# Fire and forget
send_email_task.delay("user@example.com", "Welcome", "Hello!")

# With signature
process_data_task.apply_async(
    args=({"user_id": 123}, ),
    retry=True,
    retry_policy={
        "max_retries": 3,
        "interval_start": 1,
        "interval_step": 0.2,
        "interval_max": 0.2,
    }
)
```

## Common Operations

### Get Task Result

```python
from celery.result import AsyncResult

result = AsyncResult("task-id-here", app=celery_app)
print(result.state)      # PENDING, STARTED, SUCCESS, FAILURE
print(result.result)     # Task result if successful
print(result.info)       # Error info if failed
```

### Revoke Task

```python
celery_app.control.revoke("task-id-here", terminate=True)
```

### Purge Queue

```bash
celery -A app.celery_app purge
```

### View Active Tasks

```bash
celery -A app.celery_app inspect active
```

### View Scheduled Tasks

```bash
celery -A app.celery_app inspect scheduled
```

## Troubleshooting

### Tasks Not Being Processed

1. Check Celery worker is running: `celery -A app.celery_app inspect active`
2. Check RabbitMQ is running: `rabbitmq-diagnostics status`
3. Check Redis is running: `redis-cli ping`
4. Check logs: `celery -A app.celery_app worker -l debug`

### Tasks Stuck in Queue

```bash
# Purge all tasks
celery -A app.celery_app purge

# Or restart worker
celery -A app.celery_app worker --pool=prefork -l info
```

### Connection Errors

Check environment variables:
```bash
echo $CELERY_BROKER_URL
echo $CELERY_RESULT_BACKEND_URL
```

Verify services are running:
```bash
# RabbitMQ
telnet localhost 5672

# Redis
redis-cli ping

# PostgreSQL
psql -U fastapi_user -d fastapi_db
```

## Best Practices

1. **Keep Tasks Idempotent** - Running the same task twice should produce the same result
2. **Use Task IDs** - Store task IDs in database for tracking
3. **Set Timeouts** - Always set time limits to prevent hanging tasks
4. **Use Retries** - Implement retry logic for unreliable operations
5. **Log Everything** - Use logging extensively in tasks
6. **Monitor Celery** - Use Flower to monitor task execution
7. **Scale Workers** - Run multiple worker processes: `celery -A app.celery_app worker -c 4`
8. **Use Dedicated Queues** - Route different task types to different workers
9. **Clean Up Results** - Configure result expiration to prevent database bloat
10. **Version Tasks** - Handle task upgrades gracefully

## Resources

- [Celery Documentation](https://docs.celeryproject.org/)
- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)
- [Redis Documentation](https://redis.io/documentation)
- [Flower Documentation](https://flower.readthedocs.io/)
