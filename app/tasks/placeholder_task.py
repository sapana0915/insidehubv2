"""Placeholder Celery tasks.

These are example tasks to demonstrate Celery integration.
Replace with your actual business logic.
"""
import logging
from celery import shared_task
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@shared_task
def send_email_task(email: str, subject: str, message: str) -> dict:
    """
    Placeholder task for sending emails asynchronously.

    Args:
        email: Recipient email address
        subject: Email subject
        message: Email body

    Returns:
        dict: Task result with status and timestamp
    """
    logger.info(f"Sending email to {email} with subject: {subject}")

    try:
        # TODO: Integrate with your email provider
        # Example: SendGrid, AWS SES, SMTP, etc.

        # Simulated email sending
        logger.info(f"✓ Email sent successfully to {email}")

        return {
            "status": "success",
            "email": email,
            "subject": subject,
            "message": "Email sent successfully"
        }
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise


@shared_task
def process_data_task(data: dict, user_id: str) -> dict:
    """
    Placeholder task for processing data asynchronously.

    Args:
        data: Data to process
        user_id: User UUID (string) for context

    Returns:
        dict: Processing result
    """
    logger.info(f"Processing data for user {user_id}")

    try:
        # TODO: Add your data processing logic
        # This could include:
        # - Database operations
        # - External API calls
        # - File processing
        # - Complex calculations

        result = {
            "processed_items": len(data) if isinstance(data, (list, dict)) else 1,
            "user_id": user_id,
        }

        logger.info(f"✓ Data processing completed for user {user_id}")

        return {
            "status": "success",
            "data": result,
            "message": "Data processed successfully"
        }
    except Exception as e:
        logger.error(f"Failed to process data: {str(e)}")
        raise


@celery_app.task
def long_running_task(duration: int = 60) -> dict:
    """
    Placeholder task for long-running operations.

    Args:
        duration: Task duration in seconds

    Returns:
        dict: Task completion status
    """
    import time

    logger.info(f"Starting long-running task (duration: {duration}s)")

    try:
        # Simulate long-running work
        for i in range(0, duration, 10):
            logger.info(f"Task progress: {i}s / {duration}s")
            time.sleep(10)

        logger.info("✓ Long-running task completed")

        return {
            "status": "success",
            "duration": duration,
            "message": "Long-running task completed successfully"
        }
    except Exception as e:
        logger.error(f"Long-running task failed: {str(e)}")
        raise


@celery_app.task
def retry_task_example(retry_count: int = 0) -> dict:
    """
    Example task showing retry mechanism.

    Args:
        retry_count: Number of retries attempted

    Returns:
        dict: Task result
    """
    logger.info(f"Executing task with retry (attempt: {retry_count + 1})")

    try:
        # Simulate a task that might fail
        # TODO: Replace with actual business logic

        return {
            "status": "success",
            "retry_count": retry_count,
            "message": "Task completed after retries"
        }
    except Exception as e:
        logger.warning(f"Task failed, will retry: {str(e)}")
        # Retry with exponential backoff
        raise retry_task_example.retry(exc=e, countdown=60, max_retries=3)
