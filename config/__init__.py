import pymysql

# Install PyMySQL as MySQLdb for Django compatibility
pymysql.install_as_MySQLdb()

# Ensure Celery app is always imported when Django starts
from .celery import app as celery_app  # noqa: E402

__all__ = ("celery_app",)

