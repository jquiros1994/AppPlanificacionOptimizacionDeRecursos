"""Excepciones específicas del dominio."""


class PlanificadorError(Exception):
    """Excepción base de todo el sistema."""


class ValidacionError(PlanificadorError):
    """Un campo tiene un valor inválido."""

    def __init__(self, campo: str, motivo: str) -> None:
        self.campo = campo
        self.motivo = motivo
        super().__init__(f"{campo}: {motivo}")


class ReferenciaError(PlanificadorError):
    """Un ID no existe o está duplicado."""


class CicloDependenciaError(PlanificadorError):
    """Las dependencias entre actividades forman un ciclo."""

    def __init__(self, cadena: list[str]) -> None:
        self.cadena = cadena
        super().__init__("Ciclo de dependencias: " + " → ".join(cadena))
