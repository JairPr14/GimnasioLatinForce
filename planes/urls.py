"""
URLs del módulo Planes.
"""
from django.urls import path
from . import views

app_name = 'planes'

urlpatterns = [
    path('', views.PlanListView.as_view(), name='list'),
    path('nuevo/', views.PlanCreateView.as_view(), name='create'),
    path('<int:pk>/', views.PlanDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.PlanUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.PlanDeleteView.as_view(), name='delete'),
]
