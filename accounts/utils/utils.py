from django.contrib.auth.mixins import UserPassesTestMixin


class StaffPrivilegesRequiredMixin(UserPassesTestMixin):
    """Mixin that provides feature of checking if user is staff and forbids to
    pass if it is."""

    def test_func(self):
        authorized = False
        user = self.request.user
        if user.is_staff or user.is_superuser:
            authorized = True
        return authorized
