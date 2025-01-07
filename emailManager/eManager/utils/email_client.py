import imaplib
import email
from email.utils import parsedate_to_datetime
from eManager.models import EmailSender
from emailManager.config import Trusted


class EmailClient:
    def __init__(self, email_address, password, imap_server):
        """
        Initialize the email client with credentials and server information.
        """
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.connection = None
        self.connected = False  # To track connection status

    def connect(self):
        """
        Connect to the IMAP server.
        """
        try:
            self.connection = imaplib.IMAP4_SSL(self.imap_server)
            self.connection.login(self.email_address, self.password)
            self.connected = True
            print(f"Connected to {self.imap_server}")
        except imaplib.IMAP4.error as e:
            self.connected = False
            print(f"IMAP login failed: {e}")
        except Exception as e:
            self.connected = False
            print(f"Failed to connect to the IMAP server: {e}")

    def disconnect(self):
        if self.connection:
            try:
                # Check if the connection is in the SELECTED state
                self.connection.close()  # Closes the IMAP mailbox if open
            except imaplib.IMAP4.error as e:
                print(f"Error during close: {e}")
            finally:
                try:
                    self.connection.logout()  # Logs out from the server
                    print("Disconnected from the email server.")
                except imaplib.IMAP4.error as e:
                    print(f"Error during logout: {e}")


    def fetch_emails(self, folder="inbox"):
        """
        Fetch email IDs from the specified folder.
        """
        try:
            if not self.connected:
                print("Not connected to the email server.")
                return []
            
            self.connection.select(folder)
            status, messages = self.connection.search(None, "ALL")
            if status == "OK":
                email_ids = messages[0].split()
                if not email_ids:
                    print("No emails found.")
                return email_ids
            else:
                print("Failed to fetch emails.")
                return []
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []

    def _fetch_email_by_id(self, email_id):
        """
        Fetch a specific email by its ID.
        """
        try:
            status, email_data = self.connection.fetch(email_id, "(RFC822)")
            if status != "OK":
                print(f"Failed to fetch email with ID: {email_id}")
                return None
            raw_email = email_data[0][1]
            return email.message_from_bytes(raw_email)
        except Exception as e:
            print(f"Error fetching email ID {email_id}: {e}")
            return None

    def update_sender_preference(self, sender_email, is_important):
        """
        Update or create a sender preference in the database.
        """
        try:
            sender, created = EmailSender.objects.get_or_create(email=sender_email)
            sender.is_important = is_important
            sender.save()
            print(f"Sender {sender_email} marked as {'important' if is_important else 'unimportant'}.")
        except Exception as e:
            print(f"Error updating sender preference for {sender_email}: {e}")

    def is_sender_important(self, sender_email):
        """
        Check if a sender is marked as important in the database.
        """
        try:
            sender = EmailSender.objects.get(email=sender_email)
            return sender.is_important
        except EmailSender.DoesNotExist:
            print(f"Sender {sender_email} not found in the database. Defaulting to unimportant.")
            return False

    def categorize_senders(self, folder="inbox", trusted_domains=None):
        """
        Categorize senders as important or unimportant based on criteria.
        """
        if trusted_domains is None:
            trusted_domains = Trusted

        self.connect()
        email_ids = self.fetch_emails(folder)

        for email_id in email_ids:
            email_message = self._fetch_email_by_id(email_id)
            if not email_message:
                continue

            sender_email = email_message.get("From")
            if sender_email:
                sender_email = sender_email.split()[-1].strip("<>")
                if any(sender_email.endswith(domain) for domain in trusted_domains) or \
                        "urgent" in email_message.get("Subject", "").lower():
                    self.update_sender_preference(sender_email, is_important=True)
                else:
                    self.update_sender_preference(sender_email, is_important=False)

        self.disconnect()
