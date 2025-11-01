# listings/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_booking_confirmation_email(email, booking_id):
    """
    Celery task to send booking confirmation email asynchronously.
    """
    subject = f"Booking Confirmation #{booking_id}"
    message = (
        f"Dear customer,\n\n"
        f"Your booking with ID {booking_id} has been successfully confirmed.\n"
        f"Thank you for choosing ALX Travel App!\n\n"
        f"Best regards,\nALX Travel Team"
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
    return f"Booking confirmation sent to {email}"
