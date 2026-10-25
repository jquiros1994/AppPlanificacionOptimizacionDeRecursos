from datetime import datetime

import pytest

from planificador.dominio import Intervalo, ValidacionError


def _hora(hora: int, minuto: int = 0) -> datetime:
    return datetime(2026, 1, 1, hora, minuto)


def test_duracion_horas():
    intervalo = Intervalo(_hora(8), _hora(12))
    assert intervalo.duracion_horas() == 4.0


def test_inicio_mayor_o_igual_a_fin_lanza_validacion_error():
    with pytest.raises(ValidacionError):
        Intervalo(_hora(12), _hora(8))

    with pytest.raises(ValidacionError):
        Intervalo(_hora(8), _hora(8))


def test_contiene_un_intervalo_mas_pequeno():
    externo = Intervalo(_hora(8), _hora(17))
    interno = Intervalo(_hora(9), _hora(11))

    assert externo.contiene(interno)
    assert not interno.contiene(externo)


def test_intervalos_que_solo_se_tocan_en_un_extremo_no_se_superponen():
    manana = Intervalo(_hora(8), _hora(12))
    tarde = Intervalo(_hora(12), _hora(14))

    assert not manana.se_superpone(tarde)
    assert not tarde.se_superpone(manana)


def test_intervalos_que_se_cruzan_si_se_superponen():
    primero = Intervalo(_hora(8), _hora(12))
    segundo = Intervalo(_hora(11), _hora(14))

    assert primero.se_superpone(segundo)
    assert segundo.se_superpone(primero)


def test_interseccion_de_intervalos_que_se_cruzan():
    primero = Intervalo(_hora(8), _hora(12))
    segundo = Intervalo(_hora(11), _hora(14))

    assert primero.interseccion(segundo) == Intervalo(_hora(11), _hora(12))


def test_interseccion_de_intervalos_que_solo_se_tocan_es_none():
    manana = Intervalo(_hora(8), _hora(12))
    tarde = Intervalo(_hora(12), _hora(14))

    assert manana.interseccion(tarde) is None


def test_intervalo_es_inmutable():
    intervalo = Intervalo(_hora(8), _hora(12))

    with pytest.raises(AttributeError):
        intervalo.inicio = _hora(9)  # type: ignore[misc]
