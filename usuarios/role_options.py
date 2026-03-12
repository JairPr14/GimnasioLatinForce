from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class PermisoDef:
    code: str
    label: str
    group: str


PERMISOS: List[PermisoDef] = [
    # Dashboard
    PermisoDef("dashboard.view", "Ver dashboard", "Dashboard"),

    # Clientes
    PermisoDef("clientes.view", "Ver clientes", "Clientes"),
    PermisoDef("clientes.create", "Crear clientes", "Clientes"),
    PermisoDef("clientes.update", "Editar clientes", "Clientes"),
    PermisoDef("clientes.delete", "Eliminar clientes", "Clientes"),

    # Planes
    PermisoDef("planes.view", "Ver planes", "Planes"),
    PermisoDef("planes.create", "Crear planes", "Planes"),
    PermisoDef("planes.update", "Editar planes", "Planes"),
    PermisoDef("planes.delete", "Eliminar planes", "Planes"),

    # Pagos / Deudas / Reportes
    PermisoDef("pagos.view", "Ver pagos", "Pagos"),
    PermisoDef("pagos.create", "Registrar pagos", "Pagos"),
    PermisoDef("pagos.update", "Editar pagos", "Pagos"),
    PermisoDef("pagos.ticket", "Ver/Imprimir comprobantes de pago", "Pagos"),
    PermisoDef("pagos.pdf", "Generar PDF de pago 80mm", "Pagos"),

    PermisoDef("deudas.view", "Ver deudas", "Deudas"),
    PermisoDef("deudas.create", "Registrar deudas", "Deudas"),

    PermisoDef("reportes.view", "Ver reportes", "Reportes"),

    # Inventario
    PermisoDef("inventario.view", "Ver inventario", "Inventario"),
    PermisoDef("inventario.create", "Crear productos", "Inventario"),
    PermisoDef("inventario.update", "Editar productos", "Inventario"),
    PermisoDef("inventario.delete", "Eliminar productos", "Inventario"),

    # Trabajadores
    PermisoDef("trabajadores.view", "Ver trabajadores", "Trabajadores"),
    PermisoDef("trabajadores.create", "Registrar trabajadores", "Trabajadores"),
    PermisoDef("trabajadores.update", "Editar trabajadores", "Trabajadores"),
    PermisoDef("trabajadores.delete", "Eliminar trabajadores", "Trabajadores"),
    PermisoDef("trabajadores.pagos.view", "Ver pagos de trabajadores", "Trabajadores"),
    PermisoDef("trabajadores.pagos.create", "Registrar pagos a trabajadores", "Trabajadores"),
    PermisoDef("trabajadores.pagos.update", "Editar pagos a trabajadores", "Trabajadores"),
    PermisoDef("trabajadores.pagos.ticket", "Ver/Imprimir comprobantes de pago a trabajadores", "Trabajadores"),
    PermisoDef("trabajadores.pagos.pdf", "Generar PDF de pago a trabajador 80mm", "Trabajadores"),
    PermisoDef("trabajadores.sueldos.view", "Ver historial de sueldos", "Trabajadores"),
    PermisoDef("trabajadores.sueldos.create", "Actualizar/registrar sueldos", "Trabajadores"),
    PermisoDef("trabajadores.reportes.view", "Ver reportes de pagos a trabajadores", "Trabajadores"),

    # Ventas
    PermisoDef("ventas.view", "Ver ventas", "Ventas"),
    PermisoDef("ventas.create", "Registrar ventas", "Ventas"),
    PermisoDef("ventas.ticket", "Ver/Imprimir comprobantes de venta", "Ventas"),
    PermisoDef("ventas.pdf", "Generar PDF de venta 80mm", "Ventas"),

    # Seguridad
    PermisoDef("seguridad.usuarios", "Administrar usuarios", "Seguridad"),
    PermisoDef("seguridad.roles", "Administrar roles", "Seguridad"),
]


def permisos_choices() -> List[Tuple[str, str]]:
    """
    Choices agrupables para forms. Mantiene orden por grupo.
    """
    return [(p.code, f"{p.group} — {p.label}") for p in PERMISOS]


def permisos_por_grupo() -> dict[str, List[PermisoDef]]:
    groups: dict[str, List[PermisoDef]] = {}
    for p in PERMISOS:
        groups.setdefault(p.group, []).append(p)
    return groups

