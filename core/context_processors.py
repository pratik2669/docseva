from .models import Notification, UserProfile


def docseva_context(request):
    """
    Global context injected into every template.
    Provides profile, role flags, and unread notification count.
    """
    if not request.user.is_authenticated:
        return {
            "profile": None,
            "unread_notifications": 0,
            "is_portal_admin": False,
            "is_portal_superadmin": False,
            "portal_role": "guest",
        }
    profile = (
        UserProfile.objects.filter(user=request.user)
        .select_related("subscription")
        .first()
    )
    portal_role = profile.portal_role if profile else "user"
    is_portal_admin = bool(profile and profile.is_portal_staff)
    is_portal_superadmin = bool(profile and profile.is_portal_superadmin)
    return {
        "profile": profile,  # makes profile.image work in base.html on every page
        "unread_notifications": Notification.objects.filter(
            user=request.user, is_read=False
        ).count(),
        "is_portal_admin": is_portal_admin,
        "is_portal_superadmin": is_portal_superadmin,
        "portal_role": portal_role,
    }
