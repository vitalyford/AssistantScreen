from django.urls import path

from . import views

app_name = 'assistant'
urlpatterns = [
    path('', views.index, name='index'),
    path('delete-all/', views.delete_all, name='delete-all'),
    path('delete-visitor/', views.delete_visitor, name='delete-visitor'),
    path('detect-face/', views.detect_face, name='detect-face'),
    path('send-message/', views.send_message, name='send-message'),
    path('check-for-update/', views.check_for_update, name='check-for-update'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
]
