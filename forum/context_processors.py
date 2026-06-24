from forum.services.forumService import ForumNotificationService


def forum_notifications(request):
    """Expose unread notification count on every template."""
    user_id = request.session.get("userId")
    if not user_id:
        return {"unreadCount": 0}

    return {
        "unreadCount": ForumNotificationService().getUnreadCount(user_id),
    }
