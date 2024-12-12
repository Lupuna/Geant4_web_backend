from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_employee", False)
        return self._create_user(email, password, **extra_fields)

    def create_employee_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_employee", True)
        if extra_fields.get("is_employee") is not True:
            raise ValueError("Employee must have is_employee=True.")
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_employee", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        return self._create_user(email, password, **extra_fields)

    def _create_user(self, email, password, **extra_fields):
        self._validate_user_fields(email, extra_fields.get('username'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    @staticmethod
    def _validate_user_fields(email, username):
        if not email:
            raise ValueError("The given username must be set")
        if not username:
            raise ValueError("The username must be set")
