"""
UI Components - Componentes visuales para la interfaz de usuario.

Módulo que proporciona funciones para imprimir elementos de UI con estilos,
como encabezados de menú, opciones, mensajes en cajas, etc.
"""

import os
from common import ANSIColors, MENU_BORDER_WIDTH


def print_menu_header(title: str) -> None:
    """
    Imprime un encabezado de menú con bordes estilizados.

    Args:
        title: Título del menú a mostrar.

    Example:
        >>> print_menu_header("CONFIGURACIÓN")
        ┌────────────────────────────┐
        │ CONFIGURACIÓN              │
        └────────────────────────────┘
    """
    color = ANSIColors.CYAN
    reset = ANSIColors.RESET
    print(
        f"\n{color}┌{'─' * MENU_BORDER_WIDTH}┐{reset}"
    )
    print(f"{color}│ {title:<{MENU_BORDER_WIDTH - 1}}│{reset}")
    print(f"{color}└{'─' * MENU_BORDER_WIDTH}┘{reset}")


def print_menu_option(
    number: int,
    text: str,
    emoji: str = "▸"
) -> None:
    """
    Imprime una opción de menú estilizada.

    Args:
        number: Número de la opción (1-based).
        text: Texto de la opción.
        emoji: Emoji prefijo (default: "▸").

    Example:
        >>> print_menu_option(1, "Crear endpoint")
        ▸ 1 - Crear endpoint
    """
    color = ANSIColors.GREEN
    reset = ANSIColors.RESET
    print(f"  {color}{emoji} {number}{reset} - {text}")


def print_summary_item(
    label: str,
    value: str,
    highlight: bool = False,
) -> None:
    """
    Imprime un elemento de resumen con estilo opcional.

    Args:
        label: Etiqueta del elemento.
        value: Valor a mostrar.
        highlight: Si se debe resaltar el valor (default: False).

    Example:
        >>> print_summary_item("API ID", "abc123")
        ▸ API ID: abc123

        >>> print_summary_item("Status", "CREADO", highlight=True)
        ▸ Status: CREADO (con colores destacados)
    """
    info_color = ANSIColors.CYAN
    highlight_color = ANSIColors.YELLOW
    value_color = ANSIColors.GREEN
    debug_color = ANSIColors.GRAY
    reset = ANSIColors.RESET

    if highlight:
        print(
            f"  {info_color}▸{reset} "
            f"{highlight_color}{label}:{reset} "
            f"{value_color}{value}{reset}"
        )
    else:
        print(
            f"  {info_color}▸{reset} "
            f"{label}: {debug_color}{value}{reset}"
        )


def print_box_message(message: str, style: str = "info") -> None:
    """
    Imprime un mensaje dentro de una caja con estilo.

    Args:
        message: Mensaje a mostrar (soporta saltos de línea).
        style: Estilo de la caja - "info", "success", "warning", o "error".

    Example:
        >>> print_box_message("Operación completada", "success")
        ╔══════════════════════════════╗
        ║ Operación completada         ║
        ╚══════════════════════════════╝
    """
    color_map = {
        "info": ANSIColors.CYAN,
        "success": ANSIColors.GREEN,
        "warning": ANSIColors.YELLOW,
        "error": ANSIColors.RED,
    }
    color = color_map.get(style, ANSIColors.CYAN)
    reset = ANSIColors.RESET

    lines = message.split('\n')
    max_len = max(len(line) for line in lines) if lines else 0

    print(f"\n{color}╔{'═' * (max_len + 2)}╗{reset}")
    for line in lines:
        print(f"{color}║ {line:<{max_len}} ║{reset}")
    print(f"{color}╚{'═' * (max_len + 2)}╝{reset}")


def clear_screen() -> None:
    """
    Limpia la pantalla de forma segura en Windows y sistemas Unix.

    Ejecuta el comando apropiado según el sistema operativo:
    - Windows: 'cls'
    - Unix/Linux/Mac: 'clear'

    Example:
        >>> clear_screen()
        # La pantalla se limpia
    """
    os.system('cls' if os.name == 'nt' else 'clear')
