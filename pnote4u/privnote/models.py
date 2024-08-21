from django.db import models
from django.utils import timezone
import uuid

class Note(models.Model):
    content = models.TextField()
    unique_link = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    one_time_view = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def is_expired(self):
        if self.one_time_view and not self.is_active:
            return True
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False

    def mark_as_viewed(self):
        if self.one_time_view:
            self.is_active = False
            self.save()

    def __str__(self):
        return f"Note {self.unique_link}"
