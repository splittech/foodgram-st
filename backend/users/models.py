from django.utils import timezone
from django.db import models
from django.contrib.auth.models import (UserManager,
                                        AbstractBaseUser,
                                        PermissionsMixin)


class CustomUserManager(UserManager):
    """
    Используется для более правильного создания пользователя средствами джанго.
    Например, через python manage.py createsuperuser.
    """
    def _create_user(self, email, username, first_name,
                     last_name, password, **extra_fields):

        if not email:
            raise ValueError('Для пользователя должна быть указана почта.')

        if not username:
            raise ValueError('Для пользователя должен быть указан логин.')

        if self.model.objects.filter(username=username).exists():
            raise ValueError('Пользователь с таким именем уже существует.')

        if not first_name:
            raise ValueError('Для пользователя должно быть указано имя.')

        if not last_name:
            raise ValueError('Для пользователя должна быть указана фамилия.')

        if not password:
            raise ValueError('Для пользователя должен быть указан пароль.')

        email = self.normalize_email(email)

        user = self.model(email=email, username=username,
                          first_name=first_name, last_name=last_name,
                          **extra_fields)

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, email, username, first_name,
                    last_name, password, **extra_fields):

        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        return self._create_user(email, username, first_name,
                                 last_name, password, **extra_fields)

    def create_superuser(self, email, username, first_name, last_name,
                         password, **extra_fields):

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self._create_user(email, username, first_name, last_name,
                                 password, **extra_fields)


class User(PermissionsMixin, AbstractBaseUser):
    """
    Переопределенная модель пользователя с новыми полями согласно заданию.
    """
    # Основные поля.
    email = models.EmailField(verbose_name='Электронная почта',
                              max_length=254, unique=True)

    username = models.CharField(verbose_name='Логин',
                                max_length=150, unique=True)

    first_name = models.CharField(verbose_name='Имя',
                                  max_length=150)

    last_name = models.CharField(verbose_name='Фамилия',
                                 max_length=150)

    is_subscribed = models.BooleanField(verbose_name='Подписан',
                                        default=False)

    avatar = models.ImageField(verbose_name='Аватар',
                               upload_to='users/',
                               blank=True, null=True)

    subscribers = models.ManyToManyField(to='self',
                                         verbose_name='Подписчики',
                                         symmetrical=False,
                                         blank=True)

    # Дополнительные поля.
    is_active = models.BooleanField(verbose_name='Активен',
                                    default=True)

    is_superuser = models.BooleanField(verbose_name='Админиcтратор',
                                       default=False)

    is_staff = models.BooleanField(verbose_name='Работник',
                                   default=False)

    date_joined = models.DateTimeField(verbose_name='Дата создания',
                                       default=timezone.now)

    last_login = models.DateTimeField(verbose_name='Последний вход в систему',
                                      blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_short_name(self):
        return self.first_name

    def __str__(self):
        return self.username
