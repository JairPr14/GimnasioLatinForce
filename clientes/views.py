"""
Vistas del módulo Clientes.
"""
from datetime import timedelta

from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.views import View

from usuarios.permissions import RolePermissionRequiredMixin
from django.db.models import Q

from .forms import ClienteForm, AsistenciaRegistroForm
from .models import Cliente, Asistencia, AsistenciaInvitado
from .asistencia_utils import (
    cliente_tiene_plan_activo,
    cliente_en_mora,
    asistencias_hoy_count,
    puede_registrar_ingreso_hoy,
    puede_traer_invitado,
    registrar_venta_rutina_y_asistencia,
)
from usuarios.permissions import user_has_perm


class ClienteListView(RolePermissionRequiredMixin, ListView):
    """Listado de clientes con búsqueda."""
    model = Cliente
    template_name = 'clientes/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 15
    required_perms = ["clientes.view"]

    def get_queryset(self):
        qs = Cliente.objects.all()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(nombres__icontains=q) |
                Q(apellidos__icontains=q) |
                Q(dni__icontains=q)
            )
        return qs


class ClienteDetailView(RolePermissionRequiredMixin, DetailView):
    """Detalle del cliente."""
    model = Cliente
    template_name = 'clientes/cliente_detail.html'
    context_object_name = 'cliente'
    required_perms = ["clientes.view"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from datetime import timedelta
        from django.utils import timezone
        from pagos.models import Pago
        hoy = timezone.now().date()
        ultimo_pago = Pago.objects.filter(cliente=self.object, plan__isnull=False).select_related('plan').order_by('-fecha_pago').first()
        if ultimo_pago:
            fecha_vencimiento = ultimo_pago.fecha_pago + timedelta(days=ultimo_pago.plan.duracion_dias)
            ctx['ultimo_plan'] = ultimo_pago
            ctx['fecha_vencimiento_plan'] = fecha_vencimiento
            ctx['plan_activo'] = hoy <= fecha_vencimiento
        else:
            ctx['ultimo_plan'] = None
        ctx['asistencias'] = Asistencia.objects.filter(cliente=self.object).select_related('cliente').prefetch_related('invitados')[:15]
        return ctx


class ClienteCreateView(RolePermissionRequiredMixin, CreateView):
    """Crear nuevo cliente."""
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('clientes:list')
    required_perms = ["clientes.create"]

    def get_initial(self):
        from django.utils import timezone
        initial = super().get_initial()
        initial['fecha_inscripcion'] = timezone.now().date()
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'Cliente registrado correctamente.')
        return super().form_valid(form)


class ClienteUpdateView(RolePermissionRequiredMixin, UpdateView):
    """Editar cliente."""
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    context_object_name = 'cliente'
    success_url = reverse_lazy('clientes:list')
    required_perms = ["clientes.update"]

    def form_valid(self, form):
        messages.success(self.request, 'Cliente actualizado correctamente.')
        return super().form_valid(form)


class ClienteDeleteView(RolePermissionRequiredMixin, DeleteView):
    """Eliminar cliente."""
    model = Cliente
    template_name = 'clientes/cliente_confirm_delete.html'
    context_object_name = 'cliente'
    success_url = reverse_lazy('clientes:list')
    required_perms = ["clientes.delete"]

    def form_valid(self, form):
        messages.success(self.request, 'Cliente eliminado correctamente.')
        return super().form_valid(form)


class AsistenciaRegistrarView(RolePermissionRequiredMixin, View):
    """Vista para registrar ingreso o egreso por DNI."""
    required_perms = ["asistencia.create"]

    def get(self, request):
        dni_inicial = request.GET.get('dni', '').strip()
        form = AsistenciaRegistroForm(initial={'dni': dni_inicial} if dni_inicial else None)
        return render(request, 'clientes/asistencia_registrar.html', {'form': form})

    def post(self, request):
        form = AsistenciaRegistroForm(request.POST)
        cliente = None
        tiene_ingreso_abierto = False
        ultima_asistencia = None

        if form.is_valid():
            dni = form.cleaned_data['dni'].strip()
            cliente = Cliente.objects.filter(dni__iexact=dni).first()
            if cliente:
                ultima_asistencia = Asistencia.objects.filter(
                    cliente=cliente, fecha_hora_egreso__isnull=True
                ).order_by('-fecha_hora_ingreso').first()
                # Auto-cierre si ya pasaron 1h 30min
                if ultima_asistencia:
                    limite = ultima_asistencia.fecha_hora_ingreso + timedelta(minutes=Asistencia.duracion_minutos_defecto)
                    if timezone.now() >= limite:
                        ultima_asistencia.fecha_hora_egreso = limite
                        ultima_asistencia.save()
                        messages.info(request, 'Jornada cerrada automáticamente (1h 30min).')
                        ultima_asistencia = None
                tiene_ingreso_abierto = ultima_asistencia is not None

                accion = request.POST.get('accion')
                if accion == 'registrar_rutina':
                    if not user_has_perm(request.user, 'ventas.create'):
                        messages.error(request, 'No tienes permiso para registrar ventas.')
                    else:
                        try:
                            registrar_venta_rutina_y_asistencia(cliente, request.user)
                            messages.success(request, f'Rutina (S/ 5) y asistencia registradas para {cliente.nombre_completo}.')
                            form = AsistenciaRegistroForm(initial={'dni': dni})
                            cliente = None
                            tiene_ingreso_abierto = False
                            ultima_asistencia = None
                        except Exception as e:
                            messages.error(request, f'Error al registrar: {e}')
                elif accion == 'registrar_ingreso':
                    if not cliente_tiene_plan_activo(cliente):
                        messages.error(request, f'{cliente.nombre_completo} no tiene plan activo. Regístrelo en un plan o como rutina (S/ 5).')
                    else:
                        nueva_asistencia = Asistencia.objects.create(
                            cliente=cliente,
                            fecha_hora_ingreso=timezone.now()
                        )
                        messages.success(request, f'Ingreso registrado para {cliente.nombre_completo}.')
                        form = AsistenciaRegistroForm(initial={'dni': dni})
                        tiene_ingreso_abierto = False
                        if puede_traer_invitado(cliente):
                            from .asistencia_utils import invitados_mes_count, MAX_INVITADOS_POR_MES
                            ultima_asistencia = nueva_asistencia
                            request.session['_preguntar_invitado'] = {
                                'asistencia_id': nueva_asistencia.pk,
                                'invitados_restantes': MAX_INVITADOS_POR_MES - invitados_mes_count(cliente),
                            }
                        else:
                            ultima_asistencia = None
                elif accion == 'registrar_invitado':
                    invitado_nombre = (request.POST.get('invitado_nombre') or '').strip()
                    asistencia_id = request.POST.get('asistencia_id')
                    if invitado_nombre and asistencia_id and cliente:
                        asistencia = Asistencia.objects.filter(pk=asistencia_id, cliente=cliente).first()
                        if asistencia and puede_traer_invitado(cliente):
                            AsistenciaInvitado.objects.create(
                                asistencia=asistencia,
                                nombre=invitado_nombre,
                                documento=(request.POST.get('invitado_documento') or '').strip()[:20],
                            )
                            messages.success(request, f'Invitado "{invitado_nombre}" registrado.')
                    if '_preguntar_invitado' in request.session:
                        del request.session['_preguntar_invitado']
                    form = AsistenciaRegistroForm(initial={'dni': dni})
                    tiene_ingreso_abierto = False
                    ultima_asistencia = None
                elif accion == 'marcar_egreso' and ultima_asistencia:
                    ultima_asistencia.fecha_hora_egreso = timezone.now()
                    ultima_asistencia.save()
                    messages.success(request, f'Egreso registrado para {cliente.nombre_completo}.')
                    form = AsistenciaRegistroForm(initial={'dni': dni})
                    tiene_ingreso_abierto = False
                    ultima_asistencia = None

        from datetime import timedelta
        from pagos.models import Pago
        ultimo_plan = None
        fecha_vencimiento_plan = None
        preguntar_invitado = False
        invitados_restantes = 0
        if cliente:
            ultimo_plan = Pago.objects.filter(
                cliente=cliente, plan__isnull=False
            ).select_related('plan').order_by('-fecha_pago').first()
            if ultimo_plan:
                fecha_vencimiento_plan = ultimo_plan.fecha_pago + timedelta(days=ultimo_plan.plan.duracion_dias)
            if '_preguntar_invitado' in request.session and cliente:
                pd = request.session['_preguntar_invitado']
                preguntar_invitado = True
                invitados_restantes = pd.get('invitados_restantes', 0)
                aid = pd.get('asistencia_id')
                if aid and not ultima_asistencia:
                    ultima_asistencia = Asistencia.objects.filter(pk=aid, cliente=cliente).first()

        return render(request, 'clientes/asistencia_registrar.html', {
            'form': form,
            'cliente': cliente,
            'tiene_ingreso_abierto': tiene_ingreso_abierto,
            'ultima_asistencia': ultima_asistencia,
            'tiene_plan_activo': cliente_tiene_plan_activo(cliente) if cliente else False,
            'ultimo_plan': ultimo_plan,
            'fecha_vencimiento_plan': fecha_vencimiento_plan,
            'preguntar_invitado': preguntar_invitado,
            'invitados_restantes': invitados_restantes,
        })


class AsistenciaRegistroRapidoView(RolePermissionRequiredMixin, View):
    """Registro rápido: DNI + Enter = registro automático (ingreso o egreso)."""
    required_perms = ["asistencia.create"]

    def get(self, request):
        dni = request.GET.get('dni', '').strip()
        return render(request, 'clientes/asistencia_registro_rapido.html', {'dni': dni})

    def post(self, request):
        dni = (request.POST.get('dni') or '').strip()
        accion = request.POST.get('accion')

        if not dni:
            messages.error(request, 'Introduce el DNI.')
            return render(request, 'clientes/asistencia_registro_rapido.html', {'dni': ''})

        cliente = Cliente.objects.filter(dni__iexact=dni).first()
        if not cliente:
            messages.error(request, f'No se encontró cliente con DNI "{dni}".')
            return render(request, 'clientes/asistencia_registro_rapido.html', {'dni': dni})

        # Registrar invitado (después de ingreso del cliente con plan)
        if accion == 'registrar_invitado':
            invitado_nombre = (request.POST.get('invitado_nombre') or '').strip()
            asistencia_id = request.POST.get('asistencia_id')
            if invitado_nombre and asistencia_id:
                asistencia = Asistencia.objects.filter(pk=asistencia_id, cliente=cliente).first()
                if asistencia and puede_traer_invitado(cliente):
                    AsistenciaInvitado.objects.create(
                        asistencia=asistencia,
                        nombre=invitado_nombre,
                        documento=(request.POST.get('invitado_documento') or '').strip()[:20],
                    )
                    messages.success(request, f'Invitado "{invitado_nombre}" registrado.')
            return redirect('clientes:asistencia_rapido')

        # Cerrar jornada manualmente
        if accion == 'cerrar_jornada':
            ultima = Asistencia.objects.filter(
                cliente=cliente, fecha_hora_egreso__isnull=True
            ).order_by('-fecha_hora_ingreso').first()
            if ultima:
                ultima.fecha_hora_egreso = timezone.now()
                ultima.save()
                messages.success(request, f'Jornada cerrada: {cliente.nombre_completo}')
            return redirect('clientes:asistencia_rapido')

        # Registrar rutina (venta S/ 5 + asistencia)
        if accion == 'registrar_rutina':
            if not puede_registrar_ingreso_hoy(cliente):
                return render(request, 'clientes/asistencia_registro_rapido.html', {
                    'dni': dni,
                    'cliente': cliente,
                    'limite_diario': True,
                    'asistencias_hoy': asistencias_hoy_count(cliente),
                })
            if not user_has_perm(request.user, 'ventas.create'):
                messages.error(request, 'No tienes permiso para registrar ventas.')
            else:
                try:
                    registrar_venta_rutina_y_asistencia(cliente, request.user)
                    messages.success(request, f'Rutina (S/ 5) y asistencia: {cliente.nombre_completo}')
                except Exception as e:
                    messages.error(request, f'Error: {e}')
            return redirect('clientes:asistencia_rapido')

        ultima = Asistencia.objects.filter(
            cliente=cliente, fecha_hora_egreso__isnull=True
        ).order_by('-fecha_hora_ingreso').first()

        # Auto-cierre si ya pasaron 1h 30min desde el ingreso
        if ultima:
            limite = ultima.fecha_hora_ingreso + timedelta(minutes=Asistencia.duracion_minutos_defecto)
            if timezone.now() >= limite:
                ultima.fecha_hora_egreso = limite
                ultima.save()
                messages.info(request, f'Jornada cerrada automáticamente (1h 30min). {cliente.nombre_completo} puede registrar nuevo ingreso.')
                ultima = None  # Continuar para registrar nuevo ingreso

        # Paciente ya tiene ingreso abierto: mostrar mensaje y opción de cerrar jornada
        if ultima:
            return render(request, 'clientes/asistencia_registro_rapido.html', {
                'dni': dni,
                'cliente': cliente,
                'ya_dentro': True,
                'ultima_asistencia': ultima,
            })

        # Ingreso: validar máximo 2 por día
        if not puede_registrar_ingreso_hoy(cliente):
            return render(request, 'clientes/asistencia_registro_rapido.html', {
                'dni': dni,
                'cliente': cliente,
                'limite_diario': True,
                'asistencias_hoy': asistencias_hoy_count(cliente),
            })

        # Ingreso: validar plan activo
        if cliente_tiene_plan_activo(cliente):
            nueva_asistencia = Asistencia.objects.create(
                cliente=cliente, fecha_hora_ingreso=timezone.now()
            )
            messages.success(request, f'Ingreso registrado: {cliente.nombre_completo}')
            if puede_traer_invitado(cliente):
                from .asistencia_utils import invitados_mes_count, MAX_INVITADOS_POR_MES
                return render(request, 'clientes/asistencia_registro_rapido.html', {
                    'dni': dni,
                    'cliente': cliente,
                    'preguntar_invitado': True,
                    'ultima_asistencia': nueva_asistencia,
                    'invitados_restantes': MAX_INVITADOS_POR_MES - invitados_mes_count(cliente),
                })
            return redirect('clientes:asistencia_rapido')

        # Sin plan o en mora: mostrar opciones (incluir último plan para pre-seleccionar)
        from pagos.models import Pago
        ultimo_pago = Pago.objects.filter(
            cliente=cliente, plan__isnull=False
        ).select_related('plan').order_by('-fecha_pago').first()
        fecha_vencimiento = None
        if ultimo_pago:
            fecha_vencimiento = ultimo_pago.fecha_pago + timedelta(days=ultimo_pago.plan.duracion_dias)

        return render(request, 'clientes/asistencia_registro_rapido.html', {
            'dni': dni,
            'cliente': cliente,
            'sin_plan': True,
            'en_mora': cliente_en_mora(cliente),
            'ultimo_plan': ultimo_pago,
            'fecha_vencimiento_plan': fecha_vencimiento,
        })


class AsistenciaClienteListView(RolePermissionRequiredMixin, ListView):
    """Listado de asistencias de un cliente (Ver cliente -> Asistencia)."""
    model = Asistencia
    template_name = 'clientes/asistencia_list.html'
    context_object_name = 'asistencias'
    paginate_by = 20
    required_perms = ["clientes.view"]

    def get_queryset(self):
        self.cliente = get_object_or_404(Cliente, pk=self.kwargs['pk'])
        return Asistencia.objects.filter(cliente=self.cliente).select_related('cliente').prefetch_related('invitados')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cliente'] = self.cliente
        return ctx
