"""
URLs de la app usuarios (autenticación).
"""
from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('login/', views.LoginView.as_view(template_name='usuarios/login.html'), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('usuarios/', views.UsuarioListView.as_view(), name='usuario_list'),
    path('usuarios/nuevo/', views.UsuarioCreateView.as_view(), name='usuario_create'),
    path('usuarios/<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='usuario_update'),
    path('usuarios/<int:pk>/eliminar/', views.UsuarioDeleteView.as_view(), name='usuario_delete'),
    path('roles/', views.RolListView.as_view(), name='rol_list'),
    path('roles/nuevo/', views.RolCreateView.as_view(), name='rol_create'),
    path('roles/<int:pk>/editar/', views.RolUpdateView.as_view(), name='rol_update'),
    path('roles/<int:pk>/eliminar/', views.RolDeleteView.as_view(), name='rol_delete'),
]
