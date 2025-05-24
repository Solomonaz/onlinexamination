from .models import Notification

def create_notification(user, message, link=""):
    """Create and save a notification for the user."""
    Notification.objects.create(
        user=user,
        message=message,
        link=link
    )