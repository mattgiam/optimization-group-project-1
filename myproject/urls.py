from django.http import HttpResponse
from django.urls import path

def home(request):
    print("everything is working!")
    return HttpResponse("Hello from the Optimization Project!")

urlpatterns = [
    path("", home),
]
