from .models import Notification

def create_notification(user, message, link=""):
    """Create and save a notification for the user."""
    Notification.objects.create(
        user=user,
        message=message,
        link=link
    )

from django.contrib.contenttypes.models import ContentType
from .models import SystemLog
from django.utils import timezone

def log_activity(user=None, action_type='OTHER', content_object=None, description=None):
    """
    Create a log entry for system activities
    
    Args:
        user: The user who performed the action (optional)
        action_type: Type of action (CREATE, UPDATE, DELETE, LOGIN, LOGOUT, OTHER)
        content_object: The object related to the action (optional)
        description: Additional description of the action (optional)
    """
    log = SystemLog(
        user=user,
        action_type=action_type,
        content_type=ContentType.objects.get_for_model(content_object) if content_object else None,
        object_id=str(getattr(content_object, 'pk', '')) if content_object else None,
        object_repr=str(content_object) if content_object else '',
        description=description
    )
    log.save()
    return log