from django.core.management.base import BaseCommand
from eManager.models import EmailSender

class Command(BaseCommand):
    help = "Mark an email sender as important or unimportant"

    def add_arguments(self, parser):
        """
        Define the command-line arguments for the management command.
        """
        parser.add_argument(
            'email', 
            type=str, 
            help="Email address of the sender"
        )
        parser.add_argument(
            'status', 
            type=str, 
            choices=['important', 'unimportant'], 
            help="Mark as important or unimportant"
        )

    def handle(self, *args, **kwargs):
        """
        Handle the command logic.
        """
        email = kwargs['email']
        status = kwargs['status'] == 'important'  # Convert status to boolean
        
        try:
            # Update or create sender preference in the database
            sender, created = EmailSender.objects.get_or_create(email=email)
            sender.is_important = status
            sender.save()
            
            action = "marked as important" if status else "marked as unimportant"
            if created:
                self.stdout.write(self.style.SUCCESS(f"New sender {email} created and {action}."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Sender {email} updated and {action}."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred while processing {email}: {e}"))
