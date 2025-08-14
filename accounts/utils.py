# accounts/utils.py
def can_view_profile(request_user, target_user):
    # owner and admin can always view
    if not request_user:
        # anonymous
        request_user = None
    if target_user == request_user:
        return True
    if request_user and (request_user.is_staff or request_user.is_superuser):
        return True
    visibility = target_user.profile.visibility
    if visibility == target_user.profile.VISIBILITY_PUBLIC:
        return True
    if visibility == target_user.profile.VISIBILITY_PRIVATE:
        return False
    if visibility == target_user.profile.VISIBILITY_FOLLOWERS:
        # viewer must be in followers of target_user
        return request_user and request_user in target_user.followers.all()
    return False
