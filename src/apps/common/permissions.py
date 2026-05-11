from rest_framework.permissions import BasePermission


def check_role(user, role_field):
    return bool(user and user.is_authenticated and getattr(user, role_field, False))


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return check_role(request.user, 'is_teacher')


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return check_role(request.user, 'is_student')


class IsGlobalAdmin(BasePermission):
    def has_permission(self, request, view):
        return check_role(request.user, 'is_global_admin')


class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        return any([
            check_role(user, 'is_global_admin'),
            check_role(user, 'is_local_admin'),
            check_role(user, 'is_manager')
        ])
