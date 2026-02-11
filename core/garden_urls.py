from django.urls import path
from . import views

urlpatterns = [
    path('', views.GardenListView.as_view(), name='garden_list'),
    path('<int:zone_id>/', views.GardenDetailView.as_view(), name='garden_detail'),
]
