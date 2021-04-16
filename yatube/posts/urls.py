from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('group/', views.group_index, name='group_index'),
    path('group/<slug:slug>/', views.group_posts, name='group')
]
