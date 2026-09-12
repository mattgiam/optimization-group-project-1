from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('about/', views.about_view, name='about'),
    path('upload/', views.upload_view, name='upload'),
    path('results/', views.results_view, name='results'),
    path('start-over/', views.start_over_view, name='start_over'),
    path('', views.upload_view, name='home'),
]
