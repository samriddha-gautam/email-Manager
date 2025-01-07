from django.core.management.base import BaseCommand
from eManager.utils.email_client import EmailClient
from eManager.models import EmailSender
from email.utils import parsedate_to_datetime
from emailManager.config import Email,Password,Server
import time
import sys

class Command(BaseCommand):
    help = "Delete unimportant emails, limited to 200 emails at a time."

    def handle(self, *args, **kwargs):
        # Initialize the email client
        email_client = EmailClient(
            email_address=Email, 
            password=Password, 
            imap_server=Server
        )

        try:
            # Start timing the operation
            start_time = time.time()

            # Connect to the email server
            email_client.connect()

            # Fetch emails, limiting the number to 200
            email_ids = email_client.fetch_emails()
            emails_with_dates = []

            # Retrieve the email messages along with their senders
            for email_id in email_ids:
                email_message = email_client._fetch_email_by_id(email_id)
                sender_email = email_message.get("From").split()[-1].strip("<>")
                email_date = email_message.get("Date")

                # Parse the date into a datetime object
                parsed_date = parsedate_to_datetime(email_date)
                emails_with_dates.append((email_id, sender_email, parsed_date))

            # Sort emails by the date, most recent first
            emails_with_dates.sort(key=lambda x: x[2], reverse=True)

            # Limit the number of emails to delete
            limited_email_ids = emails_with_dates[:10]

            if not limited_email_ids:
                self.stdout.write(self.style.SUCCESS("No emails found to delete."))
                return

            # Initialize delete count
            delete_count = 0

            # Go through each email and check the sender
            for email_id, sender_email, _ in limited_email_ids:
                # Check if the sender is unimportant
                if not EmailSender.objects.filter(email=sender_email, is_important=True).exists():
                    # If the sender is unimportant, delete the email
                    email_client.connection.store(email_id, '+FLAGS', '\\Deleted')
                    delete_count += 1
                    # Update live count on the same line
                    sys.stdout.write(f"\rDeleted emails: {delete_count}")
                    sys.stdout.flush()

            # Permanently delete the marked emails
            email_client.connection.expunge()

            # Calculate time taken
            end_time = time.time()
            time_taken = end_time - start_time

            # Disconnect after deletion
            email_client.disconnect()

            # Final output
            self.stdout.write("\n")
            self.stdout.write(self.style.SUCCESS(f"Unimportant emails deleted successfully (Total: {delete_count})."))
            self.stdout.write(self.style.SUCCESS(f"Time taken: {time_taken:.2f} seconds."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))

        finally:
            # Ensure the connection is always closed
            email_client.disconnect()
