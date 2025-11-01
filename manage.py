#!/usr/bin/env python
import os
import sys


def main():
    # ALX checker expects this exact module path:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alx_travel_app.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
