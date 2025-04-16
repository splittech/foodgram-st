from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import (ListCreateAPIView,
                                     RetrieveAPIView,
                                     ListAPIView)

import base64

from . import serializers
from . import pagination

User = get_user_model()


class UserListCreateView(ListCreateAPIView):
    """
    Представление для получения списка пользователей или создания нового
    пользователя.
    """
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    pagination_class = pagination.CustomLimitPagination
    permission_classes = (AllowAny,)

    # Переопределяем метод для создания пользователя.
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_data = serializer.data
        # Удаляем два лишних поля для ответа согласно заданию.
        response_data.pop('is_subscribed', None)
        response_data.pop('avatar', None)

        headers = self.get_success_headers(serializer.data)
        return Response(response_data,
                        status=status.HTTP_201_CREATED,
                        headers=headers)

    def perform_create(self, serializer):
        # Добавляем пользователю пароль.
        data_password = self.request.data.get('password')
        if data_password is None:
            return ValueError('При регистрации пользователя не указан пароль')
        password = make_password(data_password)
        serializer.save(password=password)


class UserDetailView(RetrieveAPIView):
    """
    Представление для полученя профиля любого пользователя.
    """
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer


class UserMeView(RetrieveAPIView):
    """
    Представление для полученя собственного профиля.
    """
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class UserAvatarView(APIView):
    """
    Представление для добавления, изменения и удаления аватара.
    """
    def put(self, request, *args, **kwargs):
        avatar_data = request.data.get('avatar')
        if not avatar_data:
            return Response({'avatar': ['Это поле обязательно.']},
                            status=status.HTTP_400_BAD_REQUEST)

        # Декодируем изображение из base64 (взято из теории курса яндекса).
        try:
            format, imgstr = avatar_data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='avatar.' + ext)
        except Exception:
            return Response({'avatar': ['Неверный формат изображения.']},
                            status=status.HTTP_400_BAD_REQUEST)

        request.user.avatar.save('avatar.' + ext, data, save=True)
        # Формируем url для ответа.
        avatar_url = request.build_absolute_uri(request.user.avatar.url)

        return Response({'avatar': avatar_url},
                        status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        request.user.avatar.delete(save=True)

        return Response({'detail': 'Аватар успешно удален.'},
                        status=status.HTTP_204_NO_CONTENT)


class PasswordChangeView(APIView):
    """
    Представление для изменения пароля пользователя.
    """
    def post(self, request, *args, **kwargs):
        # Получаем данные из запроса и проверяем их наличие.
        current_password = request.data.get('current_password')
        if not current_password:
            return Response({"current_password": ["Это поле обязательно."]},
                            status=status.HTTP_400_BAD_REQUEST)

        new_password = request.data.get('new_password')
        if not new_password:
            return Response({"new_password": ["Это поле обязательно."]},
                            status=status.HTTP_400_BAD_REQUEST)

        # Проверяем правильность текущего пароля.
        if not request.user.check_password(current_password):
            return Response({"current_password": ["Неверный пароль."]},
                            status=status.HTTP_400_BAD_REQUEST)

        # Изменяем пароль пользователя.
        request.user.set_password(new_password)
        request.user.save()

        return Response({'detail': ['Пароль успешно изменен.']},
                        status=status.HTTP_204_NO_CONTENT)


class SubscriptionListView(ListAPIView):
    """
    Представление для вывода списка подписок пользователя.
    """
    serializer_class = serializers.UserWithRecipesSerializer
    pagination_class = pagination.CustomLimitPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(subscribers=user)


class SubscriptionView(APIView):
    """
    Представления для подписки на пользователя или ее отмены.
    """
    def post(self, request, *args, **kwargs):
        subscriber = request.user
        user = get_object_or_404(User, id=kwargs.get('user_id'))

        if subscriber == user:
            return Response({'detail': 'Попытка подписаться на самого себя.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if subscriber in user.subscribers.all():
            return Response({'detail': 'Уже подписан на пользователя.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user.subscribers.add(subscriber)

        serializer = serializers.UserWithRecipesSerializer(
            user, context={'request': request}
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        subscriber = request.user
        user = get_object_or_404(User, id=kwargs.get('user_id'))

        if subscriber == user:
            return Response({'detail': 'Попытка отписаться от самого себя.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if subscriber not in user.subscribers.all():
            return Response({'detail': 'Подписки и так не было.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user.subscribers.remove(subscriber)

        return Response(status=status.HTTP_204_NO_CONTENT)
