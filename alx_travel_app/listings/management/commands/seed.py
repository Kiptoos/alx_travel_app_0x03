# alx_travel_app/listings/management/commands/seed.py

import random
from decimal import Decimal
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from faker import Faker

from listings.models import Listing, Booking, Review

fake = Faker()


def random_date(start: date, end: date) -> date:
    """Return a random date between start and end (inclusive)."""
    delta = (end - start).days
    if delta <= 0:
        return start
    return start + timedelta(days=random.randint(0, delta))


class Command(BaseCommand):
    help = "Seed the database with users, listings, bookings and reviews."

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=5, help="Number of users to create")
        parser.add_argument("--listings", type=int, default=10, help="Number of listings to create")
        parser.add_argument("--bookings", type=int, default=20, help="Number of bookings to create")
        parser.add_argument("--reviews", type=int, default=30, help="Number of reviews to create")
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete created listings, bookings, reviews and users created by this seeder (CAREFUL)",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        num_users = options["users"]
        num_listings = options["listings"]
        num_bookings = options["bookings"]
        num_reviews = options["reviews"]
        do_reset = options["reset"]

        if do_reset:
            self.stdout.write("Reset mode: deleting Listing, Booking, Review objects created by seeder...")
            Review.objects.all().delete()
            Booking.objects.all().delete()
            Listing.objects.all().delete()
            # Note: do NOT delete real users. We'll only delete users created with username seeder_*
            User.objects.filter(username__startswith="seeder_").delete()
            self.stdout.write(self.style.SUCCESS("Reset complete."))
            return

        # Create users
        users = []
        for i in range(num_users):
            username = f"seeder_user_{i+1}"
            email = f"{username}@example.com"
            password = "password123"  # change if needed
            user, created = User.objects.get_or_create(username=username, defaults={"email": email})
            if created:
                try:
                    user.set_password(password)
                    user.save()
                except Exception:
                    # If custom user model has different fields, try .save() anyway
                    user.save()
            users.append(user)

        # Ensure at least one host: if site has superuser(s), they can be hosts as well.
        all_hosts = users.copy()

        # Create listings
        listings = []
        for i in range(num_listings):
            host = random.choice(all_hosts)
            title = f"{fake.city()} {fake.word().capitalize()} Retreat"
            description = fake.paragraph(nb_sentences=3)
            location = f"{fake.city()}, {fake.country()}"
            price_per_night = Decimal(random.randint(25, 400)) + Decimal(random.choice([0.0, 0.5, 0.99]))
            max_guests = random.randint(1, 8)
            listing = Listing.objects.create(
                host=host,
                title=title,
                description=description,
                location=location,
                price_per_night=round(price_per_night, 2),
                max_guests=max_guests,
                is_active=True,
            )
            listings.append(listing)

        # Create bookings
        today = date.today()
        bookings = []
        for i in range(num_bookings):
            listing = random.choice(listings)
            guest = random.choice(users)
            # pick start date within next 90 days
            start = random_date(today, today + timedelta(days=90))
            # duration 1-10 nights
            nights = random.randint(1, 10)
            end = start + timedelta(days=nights)
            # create booking, let model.save compute price
            booking = Booking.objects.create(
                listing=listing,
                guest=guest,
                start_date=start,
                end_date=end,
                total_price=Decimal("0.00"),  # will get computed in save()
                status=random.choice([Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED]),
            )
            booking.save()
            bookings.append(booking)

        # Create reviews (ensure user has booking or random)
        for i in range(num_reviews):
            listing = random.choice(listings)
            author = random.choice(users)
            rating = random.randint(1, 5)
            comment = fake.sentence(nb_words=12)
            Review.objects.create(listing=listing, author=author, rating=rating, comment=comment)

        self.stdout.write(self.style.SUCCESS(f"Created {len(users)} users, {len(listings)} listings, {len(bookings)} bookings, and seeded reviews."))
        self.stdout.write(self.style.NOTICE("Default user password for seeder users is 'password123' (change for production)."))
        self.stdout.write(self.style.WARNING("If you used --reset earlier, objects were deleted as requested."))
