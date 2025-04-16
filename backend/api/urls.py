from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views import (UserListCreateView,
                         UserDetailView,
                         UserMeView,
                         UserAvatarView,
                         PasswordChangeView,
                         SubscriptionView,
                         SubscriptionListView)

from recipes.views import (IngredientViewSet,
                           RecipeViewSet,
                           ShortLinkView,
                           GetShortLinkView,
                           ShoppingCartView,
                           DownloadShoppingCartView,
                           FavoriteView)

router = DefaultRouter()
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    # Аутентификация по токенам.
    path('auth/', include('djoser.urls.authtoken')),
    # Пользователи.
    path('users/', UserListCreateView.as_view()),
    path('users/<int:pk>/', UserDetailView.as_view()),
    path('users/me/', UserMeView.as_view()),
    path('users/me/avatar/', UserAvatarView.as_view()),
    path('users/set_password/', PasswordChangeView.as_view()),
    # Список покупок.
    path('recipes/<int:recipe_id>/shopping_cart/', ShoppingCartView.as_view()),
    path(
        'recipes/download_shopping_cart/',
        DownloadShoppingCartView.as_view()
    ),
    # Рецепты и ингридиенты.
    path('', include(router.urls)),
    path('recipes/<int:pk>/get-link/', GetShortLinkView.as_view()),
    path('s/<str:code>/', ShortLinkView.as_view()),
    # Избранное.
    path('recipes/<int:recipe_id>/favorite/', FavoriteView.as_view()),
    # Подписки.
    path('users/subscriptions/', SubscriptionListView.as_view()),
    path('users/<int:user_id>/subscribe/', SubscriptionView.as_view())
]
