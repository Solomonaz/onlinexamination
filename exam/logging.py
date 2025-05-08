from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType

def log_admin_action(action_flag):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            if hasattr(request, 'logged_object'):
                obj = request.logged_object
                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=ContentType.objects.get_for_model(obj).pk,
                    object_id=obj.pk,
                    object_repr=str(obj),
                    action_flag=action_flag,
                    change_message=f"Performed {LogEntry.ACTION_FLAG_CHOICES[action_flag][1]} via custom dashboard.",
                )
            return response
        return _wrapped_view
    return decorator
