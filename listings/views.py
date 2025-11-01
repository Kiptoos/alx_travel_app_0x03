# listings/views.py
from rest_framework import viewsets
from .models import Booking
from .serializers import BookingSerializer
from .tasks import send_booking_confirmation_email

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def perform_create(self, serializer):
        booking = serializer.save()
        # Trigger Celery email task
        if booking.user and booking.user.email:
            send_booking_confirmation_email.delay(
                booking.user.email, booking.id
            )
