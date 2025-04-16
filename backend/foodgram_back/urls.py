from django.contrib import admin
from django.urls import path, include
from recipes.views import ShortLinkView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<str:code>/', ShortLinkView.as_view()),
]
