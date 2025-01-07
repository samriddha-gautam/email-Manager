from django.core.management.base import BaseCommand
from eManager.utils.email_client import EmailClient
from emailManager.config import Email, Password, Server

class Command(BaseCommand):
    help = "Automatically categorize email senders as important or unimportant."

    def handle(self, *args, **kwargs):
        # Use values from config.py
        email_address = Email
        password = Password
        imap_server = Server

        # Log the details (avoid logging sensitive data like passwords)
        self.stdout.write(f"Email Address: {email_address}")
        self.stdout.write(f"IMAP Server: {imap_server}")

        try:
            # Create an instance of EmailClient and categorize senders
            client = EmailClient(email_address, password, imap_server)
            client.categorize_senders()

            # Success message
            self.stdout.write(self.style.SUCCESS("Senders categorized successfully."))

        except Exception as e:
            # Error handling
            self.stderr.write(self.style.ERROR(f"Error: {e}"))
