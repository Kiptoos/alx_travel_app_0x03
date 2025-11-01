# alx_travel_app/listings/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Avg
from .models import Listing, Booking, Review

User = get_user_model()


class HostSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")


class ListingSerializer(serializers.ModelSerializer):
    host = HostSerializer(read_only=True)
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Listing
        fields = [
            "id",
            "title",
            "description",
            "location",
            "price_per_night",
            "max_guests",
            "is_active",
            "host",
            "average_rating",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "host", "created_at", "updated_at", "average_rating")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # compute average rating dynamically (optional)
        reviews = instance.reviews.all()
        if reviews.exists():
            avg = reviews.aggregate(models_avg=Avg("rating"))["models_avg"]
            data["average_rating"] = round(float(avg), 2) if avg is not None else None
        else:
            data["average_rating"] = None
        return data


class BookingCreateSerializer(serializers.ModelSerializer):
    # Accept listing id and guest id (or use request.user)
    class Meta:
        model = Booking
        fields = [
            "id",
            "listing",
            "guest",
            "start_date",
            "end_date",
            "total_price",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "total_price", "created_at", "updated_at")

    def validate(self, attrs):
        start = attrs.get("start_date")
        end = attrs.get("end_date")
        if start and end and start >= end:
            raise serializers.ValidationError("end_date must be after start_date")
        return attrs

    def create(self, validated_data):
        # total_price will be computed in model.save()
        booking = Booking.objects.create(**validated_data)
        booking.save()  # ensure save() computes total_price
        return booking


class BookingSerializer(serializers.ModelSerializer):
    listing = ListingSerializer(read_only=True)
    guest = HostSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "listing",
            "guest",
            "start_date",
            "end_date",
            "nights",
            "total_price",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "listing", "guest", "nights", "total_price", "created_at", "updated_at")
