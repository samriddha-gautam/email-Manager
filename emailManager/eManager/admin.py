from django.contrib import admin
from django.http import HttpResponse
from .models import EmailSender
from .utils.email_client import EmailClient
from emailManager.config import Email,Password,Server


class EmailSenderAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_important')
    list_filter = ('is_important',)
    search_fields = ('email',)
    actions = [
        'mark_important',
        'mark_unimportant',
        'categorize_senders',
        'delete_unimportant_senders',
        'delete_unimportant_emails',
    ]

    # Action to mark selected senders as important
    def mark_important(self, request, queryset):
        queryset.update(is_important=True)
        self.message_user(request, "Marked selected senders as important.")

    # Action to mark selected senders as unimportant
    def mark_unimportant(self, request, queryset):
        queryset.update(is_important=False)
        self.message_user(request, "Marked selected senders as unimportant.")

    # Action to categorize senders automatically based on predefined rules
    def categorize_senders(self, request, queryset):
        email_address = Email
        password = Password
        imap_server = Server

        # Create an EmailClient instance and run the categorization logic
        client = EmailClient(email_address, password, imap_server)
        client.categorize_senders()

        self.message_user(request, "Senders categorized successfully.")

    # Action to delete unimportant senders from the database
    def delete_unimportant_senders(self, request, queryset):
        unimportant_senders = EmailSender.objects.filter(is_important=False)

        if unimportant_senders.exists():
            count, _ = unimportant_senders.delete()
            self.message_user(request, f"Deleted {count} unimportant senders.")
        else:
            self.message_user(request, "No unimportant senders found to delete.")

    # Action to delete unimportant emails from the email server
    def delete_unimportant_emails(self, request, queryset):
        email_address = Email
        password = Password
        imap_server = Server

        email_client = EmailClient(email_address, password, imap_server)

        try:
            # Connect to the email server
            email_client.connect()

            # Fetch all emails
            email_ids = email_client.fetch_emails()

            # Iterate through emails and delete unimportant ones
            for email_id in email_ids:
                email_message = email_client._fetch_email_by_id(email_id)
                sender_email = email_message.get("From").split()[-1].strip("<>")

                if not EmailSender.objects.filter(email=sender_email, is_important=True).exists():
                    email_client.connection.store(email_id, '+FLAGS', '\\Deleted')

            # Permanently delete the marked emails
            email_client.connection.expunge()
            self.message_user(request, "Unimportant emails deleted successfully.")

        except Exception as e:
            self.message_user(request, f"An error occurred: {e}")

        finally:
            # Ensure the connection is properly closed
            email_client.disconnect()

    # Custom short description for the action
    delete_unimportant_emails.short_description = "Delete unimportant emails"

# Register the EmailSender model with the customized admin interface
admin.site.register(EmailSender, EmailSenderAdmin)
