from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser

from foodgram_back.constants import EMAIL_MAX_LENGTH, USER_NAMES_MAX_LENGTH


class User(AbstractUser):
    """
    Переопределенная модель пользователя с новыми полями согласно заданию.
    """
    email = models.EmailField(verbose_name='Электронная почта',
                              max_length=EMAIL_MAX_LENGTH, unique=True)

    username = models.CharField(verbose_name='Логин',
                                max_length=USER_NAMES_MAX_LENGTH, unique=True)

    first_name = models.CharField(verbose_name='Имя',
                                  max_length=USER_NAMES_MAX_LENGTH)

    last_name = models.CharField(verbose_name='Фамилия',
                                 max_length=USER_NAMES_MAX_LENGTH)

    is_subscribed = models.BooleanField(verbose_name='Подписан',
                                        default=False)

    avatar = models.ImageField(verbose_name='Аватар',
                               upload_to='users/',
                               blank=True, null=True)

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

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_short_name(self):
        return self.first_name

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """
    Модель для отслеживания подписок.
    """
    author = models.ForeignKey(User,
                               verbose_name='Пользователь',
                               on_delete=models.CASCADE,
                               related_name='subscribers')

    subscriber = models.ForeignKey(User,
                                   verbose_name='Подписчик',
                                   on_delete=models.CASCADE,
                                   related_name='subscribtions')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.subscriber} на {self.author}'
