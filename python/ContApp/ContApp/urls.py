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

from cont01app.views import create_counter, get_counter_stats, update_counter, delete_counter, increment_counter, \
    get_counter

urlpatterns = [
    path('admin/', admin.site.urls),
    path('counters/', get_counter),
    path('counters/<int:counter_id>/stats/', get_counter_stats),
    path('counters/create/', create_counter),
    path('counters/<int:counter_id>/update/', update_counter),
    path('counters/<int:counter_id>/delete/', delete_counter),
    path('counters/<int:counter_id>/increment/', increment_counter),
]
