# ALX Travel App 0x03 — Celery with RabbitMQ Email Notifications

## Objective

Enhance the `alx_travel_app` project by integrating **Celery** with **RabbitMQ** to send booking confirmation emails asynchronously.

## Setup Instructions

### 1. Install and Start RabbitMQ
```bash
sudo apt-get update
sudo apt-get install rabbitmq-server -y
sudo systemctl enable rabbitmq-server
sudo systemctl start rabbitmq-server
