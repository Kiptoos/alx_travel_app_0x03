from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_payment_confirmation_email(payment_id, to_email, booking_reference, amount, currency):
    subject = "Payment Confirmation"
    body = (
        f"Your payment for booking {booking_reference} was successful.\n\n"
        f"Amount: {amount} {currency}\n"
        f"Payment ID: {payment_id}\n\n"
        f"Thank you for booking with us!"
    )
    send_mail(
        subject=subject,
        message=body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
        recipient_list=[to_email],
        fail_silently=True,
    )
