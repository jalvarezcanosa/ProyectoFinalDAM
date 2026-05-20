"""
URL configuration for ContApp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from cont01app.views import create_counter, get_counter_by_id, update_counter, delete_counter, increment_counter, \
    get_counter_mine, register, join_counter, login

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/auth/register/', register),
    path('api/auth/login/', login),
    path('api/auth/refresh/', TokenRefreshView.as_view()),
    path('api/counters/', get_counter_mine),
    path('api/counters/<int:counter_id>/', get_counter_by_id),
    path('api/counters/create/', create_counter),
    path('api/counters/<int:counter_id>/update/', update_counter),
    path('api/counters/<int:counter_id>/delete/', delete_counter),
    path('api/counters/<int:counter_id>/increment/', increment_counter),
    path('api/counters/join/', join_counter),
]
