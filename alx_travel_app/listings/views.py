import os
import uuid
import logging
import requests
from decimal import Decimal

from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Payment
from .tasks import send_payment_confirmation_email

logger = logging.getLogger(__name__)

CHAPA_SECRET_KEY = os.getenv("CHAPA_SECRET_KEY", "")
CHAPA_BASE_URL = os.getenv("CHAPA_BASE_URL", "https://api.chapa.co/v1")


def _auth_headers():
    return {
        "Authorization": f"Bearer {CHAPA_SECRET_KEY}",
        "Content-Type": "application/json",
    }


class InitiatePaymentAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not CHAPA_SECRET_KEY:
            return Response(
                {"detail": "Chapa secret key not configured."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        data = request.data
        booking_reference = str(data.get("booking_reference", "")).strip()
        amount = Decimal(str(data.get("amount", "0")))
        currency = str(data.get("currency", "ETB")).upper() or "ETB"
        email = str(data.get("email", "")).strip()
        first_name = str(data.get("first_name", "")).strip()
        last_name = str(data.get("last_name", "")).strip()

        if not booking_reference or amount <= 0 or not email:
            return Response(
                {"detail": "booking_reference, valid amount, and email are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tx_ref = f"{booking_reference}-{uuid.uuid4().hex[:8]}"
        host = request.build_absolute_uri("/")[:-1]
        default_return = host + reverse("payments:verify") + f"?tx_ref={tx_ref}"
        return_url = data.get("return_url") or default_return

        init_payload = {
            "amount": str(amount),
            "currency": currency,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "tx_ref": tx_ref,
            "callback_url": default_return,
            "return_url": return_url,
            "customization": {
                "title": "Travel Booking Payment",
                "description": f"Payment for booking {booking_reference}",
            },
        }

        try:
            resp = requests.post(
                f"{CHAPA_BASE_URL}/transaction/initialize",
                json=init_payload,
                headers=_auth_headers(),
                timeout=30,
            )
            resp_json = resp.json()
            logger.info("Chapa init response: %s", resp_json)

            if resp.status_code >= 400 or not resp_json.get("status"):
                message = resp_json.get("message", "Chapa initialization failed")
                Payment.objects.create(
                    booking=None,
                    booking_reference=booking_reference,
                    customer_email=email,
                    customer_first_name=first_name,
                    customer_last_name=last_name,
                    amount=amount,
                    currency=currency,
                    tx_ref=tx_ref,
                    status=Payment.Status.FAILED,
                    raw_init_response=resp_json,
                )
                return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)

            checkout_url = resp_json["data"]["checkout_url"]
            chapa_txn_id = resp_json["data"].get("id", "")

            payment = Payment.objects.create(
                booking=None,
                booking_reference=booking_reference,
                customer_email=email,
                customer_first_name=first_name,
                customer_last_name=last_name,
                amount=amount,
                currency=currency,
                tx_ref=tx_ref,
                chapa_txn_id=chapa_txn_id,
                status=Payment.Status.PENDING,
                raw_init_response=resp_json,
            )

            return Response(
                {"tx_ref": tx_ref, "checkout_url": checkout_url, "status": payment.status},
                status=status.HTTP_201_CREATED,
            )

        except requests.RequestException as e:
            logger.exception("Chapa init error")
            Payment.objects.create(
                booking=None,
                booking_reference=booking_reference,
                customer_email=email,
                customer_first_name=first_name,
                customer_last_name=last_name,
                amount=amount,
                currency=currency,
                tx_ref=tx_ref,
                status=Payment.Status.FAILED,
                raw_init_response={"error": str(e)},
            )
            return Response(
                {"detail": "Network error initializing payment."},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class VerifyPaymentAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if not CHAPA_SECRET_KEY:
            return Response(
                {"detail": "Chapa secret key not configured."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        tx_ref = request.query_params.get("tx_ref")
        if not tx_ref:
            return Response({"detail": "tx_ref is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = Payment.objects.get(tx_ref=tx_ref)
        except Payment.DoesNotExist:
            return Response({"detail": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            resp = requests.get(
                f"{CHAPA_BASE_URL}/transaction/verify/{tx_ref}",
                headers=_auth_headers(),
                timeout=30,
            )
            resp_json = resp.json()
            logger.info("Chapa verify response: %s", resp_json)

            ok = bool(resp_json.get("status"))
            chapa_status = (resp_json.get("data") or {}).get("status", "").lower()

            if ok and chapa_status in {"success", "successful", "completed", "paid"}:
                payment.mark_completed(verify_payload=resp_json)
                try:
                    send_payment_confirmation_email.delay(
                        str(payment.id),
                        payment.customer_email,
                        payment.booking_reference,
                        str(payment.amount),
                        payment.currency,
                    )
                except Exception:
                    logger.exception("Failed to queue email task")
            else:
                payment.mark_failed(verify_payload=resp_json)

            return Response(
                {
                    "tx_ref": payment.tx_ref,
                    "status": payment.status,
                    "amount": str(payment.amount),
                    "currency": payment.currency,
                    "booking_reference": payment.booking_reference,
                },
                status=status.HTTP_200_OK,
            )

        except requests.RequestException as e:
            logger.exception("Chapa verify error")
            return Response(
                {"detail": "Network error verifying payment."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
