from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    path('', views.ProductoListView.as_view(), name='list'),
    path('nuevo/', views.ProductoCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', views.ProductoUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.ProductoDeleteView.as_view(), name='delete'),
    path('api/buscar/', views.ProductoBuscarApiView.as_view(), name='api_buscar'),
]
