from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import sqlite3

class Command(BaseCommand):
    help = 'Import users from SQLite 3 database'

    def handle(self, *args, **options):
        # Connect to SQLite 3 database
        conn = sqlite3.connect('path/to/sqlite3/database.db')
        cursor = conn.cursor()

        # Retrieve users from SQLite 3 database
        cursor.execute('SELECT username, email, password FROM users')
        rows = cursor.fetchall()

        # Create new user objects and save to default Django database
        for row in rows:
            user = User.objects.create_user(row[0], row[1], row[2])
            user.save()

        # Close connection to SQLite 3 database
        conn.close()

        # Output success message
        self.stdout.write(self.style.SUCCESS('Users imported successfully.'))