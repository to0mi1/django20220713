from django.urls import path, re_path

from accounts import views

app_name = 'accounts'

urlpatterns = [
    re_path(r'^(login/|)$', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(), name='logout'),
]
