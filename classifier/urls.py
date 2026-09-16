from django.urls import path

from . import views

urlpatterns = [
    path('article/', views.article, name='article'),
    path('classify/', views.classify, name='classify'),
    path('classify/reset/', views.reset_classifier, name='classify_reset'),
]
