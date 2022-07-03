from django.urls import path

from pi import views

urlpatterns = [
    path('', views.index, name='index'),
    path('calc', views.calc_pi, name='calc_pi'),
    path('progress', views.progress_pi, name='progress_pi'),
    path('kill', views.kill_pi, name='progress_pi'),
]
