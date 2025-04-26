from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import (ListCreateAPIView,
                                     RetrieveAPIView,
                                     ListAPIView)

from . import serializers, pagination, models

User = get_user_model()


class UserListCreateView(ListCreateAPIView):
    queryset = User.objects.all()
    pagination_class = pagination.CustomLimitPagination
    permission_classes = (AllowAny,)

    # Решил использовать отдельный сериализатор для создания.
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.UserCreateSerializer
        return serializers.UserSerializer


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
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        serializer = serializers.UserAvatarSerializer(
            request.user,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'avatar': request.build_absolute_uri(request.user.avatar.url)},
            status=status.HTTP_200_OK
        )

    def delete(self, request, *args, **kwargs):
        request.user.avatar.delete(save=True)
        return Response(
            {'detail': 'Аватар успешно удален.'},
            status=status.HTTP_204_NO_CONTENT
        )


class PasswordChangeView(APIView):
    """
    Представление для изменения пароля пользователя.
    """
    def post(self, request):
        serializer = serializers.PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': 'Пароль успешно изменен'},
                        status=status.HTTP_204_NO_CONTENT)


class SubscriptionListView(ListAPIView):
    """
    Представление для вывода списка подписок пользователя.
    """
    serializer_class = serializers.UserWithRecipesSerializer
    pagination_class = pagination.CustomLimitPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        authors = User.objects.filter(
            subscribers__subscriber=self.request.user
        ).prefetch_related('recipes')

        return authors


class SubscriptionView(APIView):
    """
    Представления для подписки на пользователя или ее отмены.
    """
    def post(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        serializer = serializers.SubscribeSerializer(
            data={
                'author': author.id,
                'subscriber': request.user.id
            }
        )
        serializer.is_valid(raise_exception=True)
        subscribtion = serializer.save()
        response_serializer = serializers.UserWithRecipesSerializer(
            subscribtion.author, context={'request': request})

        return Response(response_serializer.data,
                        status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        author = get_object_or_404(User, id=user_id)

        serializer = serializers.UnsubscribeSerializer(
            data={
                'author': author.id,
                'subscriber': request.user.id
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        models.Subscription.objects.filter(
            author=author,
            subscriber=request.user
        ).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
