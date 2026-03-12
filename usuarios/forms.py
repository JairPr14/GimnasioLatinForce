from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Rol, RolPermiso, UsuarioRol
from .role_options import permisos_choices, permisos_por_grupo

User = get_user_model()


class UsuarioCreateForm(UserCreationForm):
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "correo@ejemplo.com"}),
    )
    roles = forms.ModelMultipleChoiceField(
        queryset=Rol.objects.filter(activo=True).order_by("nombre"),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select"}),
        help_text="Opcional. Asigna roles al usuario.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name", "is_active")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["is_active"].widget = forms.CheckboxInput(attrs={"class": "form-check-input"})
        # Asegura estilo consistente aunque se sobrescriban widgets
        if "email" in self.fields:
            self.fields["email"].widget.attrs.setdefault("class", "form-control")

        # Estilizar password fields
        for k in ("password1", "password2"):
            if k in self.fields:
                self.fields[k].widget.attrs.update({"class": "form-control"})

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            roles = self.cleaned_data.get("roles")
            if roles:
                UsuarioRol.objects.bulk_create([UsuarioRol(usuario=user, rol=r) for r in roles], ignore_conflicts=True)
        return user


class UsuarioUpdateForm(forms.ModelForm):
    roles = forms.ModelMultipleChoiceField(
        queryset=Rol.objects.filter(activo=True).order_by("nombre"),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select"}),
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "is_active")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["is_active"].widget = forms.CheckboxInput(attrs={"class": "form-check-input"})
        if self.instance and self.instance.pk:
            self.fields["roles"].initial = list(
                self.instance.roles_asignados.select_related("rol").values_list("rol_id", flat=True)
            )

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit and user.pk:
            selected = set(self.cleaned_data.get("roles").values_list("id", flat=True)) if self.cleaned_data.get("roles") else set()
            current = set(user.roles_asignados.values_list("rol_id", flat=True))
            to_add = selected - current
            to_remove = current - selected
            if to_remove:
                user.roles_asignados.filter(rol_id__in=to_remove).delete()
            if to_add:
                UsuarioRol.objects.bulk_create([UsuarioRol(usuario=user, rol_id=r) for r in to_add], ignore_conflicts=True)
        return user


class RolForm(forms.ModelForm):
    permisos = forms.MultipleChoiceField(
        required=False,
        choices=permisos_choices(),
        widget=forms.CheckboxSelectMultiple,
        help_text="Selecciona lo que este rol puede ver/hacer en el sistema.",
    )

    class Meta:
        model = Rol
        fields = ("nombre", "codigo", "descripcion", "activo")
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "codigo": forms.TextInput(attrs={"class": "form-control", "placeholder": "admin, caja, ..."}),
            "descripcion": forms.TextInput(attrs={"class": "form-control"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.permisos_grouped = permisos_por_grupo()
        if self.instance and self.instance.pk:
            self.fields["permisos"].initial = list(self.instance.permisos.values_list("codigo", flat=True))

    def save(self, commit=True):
        rol = super().save(commit=commit)
        if commit and rol.pk:
            selected = set(self.cleaned_data.get("permisos") or [])
            current = set(rol.permisos.values_list("codigo", flat=True))
            to_add = selected - current
            to_remove = current - selected
            if to_remove:
                rol.permisos.filter(codigo__in=to_remove).delete()
            if to_add:
                RolPermiso.objects.bulk_create([RolPermiso(rol=rol, codigo=c) for c in to_add], ignore_conflicts=True)
        return rol

