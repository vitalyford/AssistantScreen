from django.urls import path

from . import views

app_name = 'assistant'
urlpatterns = [
    path('', views.index, name='index'),
    path('send-message/', views.send_message, name='send-message'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
]
