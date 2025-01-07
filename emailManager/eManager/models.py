from django.db import models

class EmailSender(models.Model):
    email = models.EmailField(unique=True)
    is_important = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email} - {'Important' if self.is_important else 'Unimportant'}"
