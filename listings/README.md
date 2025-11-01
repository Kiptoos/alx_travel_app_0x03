# alx_travel_app_0x02 — Chapa Payment Integration

This update adds Chapa payment processing to the project:
- Secure env credentials (`CHAPA_SECRET_KEY`, `CHAPA_BASE_URL`)
- `Payment` model for transaction tracking
- API endpoints to **initiate** and **verify** payments
- Status transitions (**Pending → Completed/Failed**)
- **Celery**-based confirmation emails after success
- Sandbox testing cURL examples and expected logs

## Quick Start

1) Install requirements:
```bash
pip install django djangorestframework requests python-dotenv celery redis
```

2) Env file (`.env`):
```
CHAPA_SECRET_KEY=CHASEC_sandbox_xxxxxxxxxxxxxxxxx
CHAPA_BASE_URL=https://api.chapa.co/v1
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=bookings@example.com
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
```

3) Migrations:
```bash
python manage.py makemigrations listings
python manage.py migrate
```

4) URLs:
- Include `path("api/", include("listings.urls", namespace="payments"))` in project `urls.py`.

5) Run:
```bash
python manage.py runserver
celery -A alx_travel_app worker -l info
```

## API

**Initiate**
`POST /api/payments/initiate/`
```json
{
  "booking_reference": "BK-2025-0001",
  "amount": "120.00",
  "currency": "ETB",
  "email": "user@example.com",
  "first_name": "Jane",
  "last_name": "Doe"
}
```

Response:
```json
{
  "tx_ref": "BK-2025-0001-a1b2c3d4",
  "checkout_url": "https://checkout.chapa.co/...",
  "status": "Pending"
}
```

**Verify**
`GET /api/payments/verify/?tx_ref=<tx_ref>`

Response:
```json
{
  "tx_ref": "BK-2025-0001-a1b2c3d4",
  "status": "Completed",
  "amount": "120.00",
  "currency": "ETB",
  "booking_reference": "BK-2025-0001"
}
```

## Notes
- Adjust the `Booking` foreign key in `listings/models.py` to your real booking model.
- Switch `EMAIL_BACKEND` to SMTP in production.
- For stronger integrity, add webhooks signature verification when enabling Chapa callbacks.
