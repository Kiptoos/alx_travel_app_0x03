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
        # pick email from user or booking
        email = None
        if hasattr(booking, "user") and booking.user and booking.user.email:
            email = booking.user.email
        elif hasattr(booking, "customer_email"):
            email = booking.customer_email

        if email:
            send_booking_confirmation_email.delay(email, booking.id)
