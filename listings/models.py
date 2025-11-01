import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone

try:
    # Adjust this import if your Booking model lives elsewhere.
    from .booking import Booking  # placeholder; ok if missing
except Exception:
    Booking = None


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        COMPLETED = "Completed", "Completed"
        FAILED = "Failed", "Failed"
        CANCELED = "Canceled", "Canceled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    booking = models.ForeignKey(
        Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments"
    ) if Booking else models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name="noop_ref"
    )

    booking_reference = models.CharField(max_length=64, db_index=True)

    customer_email = models.EmailField()
    customer_first_name = models.CharField(max_length=64, blank=True)
    customer_last_name = models.CharField(max_length=64, blank=True)

    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=8, default="ETB")

    tx_ref = models.CharField(max_length=128, unique=True)
    chapa_txn_id = models.CharField(max_length=128, blank=True)

    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True
    )

    raw_init_response = models.JSONField(null=True, blank=True)
    raw_verify_response = models.JSONField(null=True, blank=True)

    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["booking_reference"]),
            models.Index(fields=["status"]),
        ]
        ordering = ["-created_at"]

    def mark_completed(self, verify_payload=None):
        self.status = self.Status.COMPLETED
        self.verified_at = timezone.now()
        if verify_payload is not None:
            self.raw_verify_response = verify_payload
        self.save(update_fields=["status", "verified_at", "raw_verify_response", "updated_at"])

    def mark_failed(self, verify_payload=None):
        self.status = self.Status.FAILED
        if verify_payload is not None:
            self.raw_verify_response = verify_payload
        self.save(update_fields=["status", "raw_verify_response", "updated_at"])

    def __str__(self):
        return f"{self.booking_reference} • {self.tx_ref} • {self.status}"
