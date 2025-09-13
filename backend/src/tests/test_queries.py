import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import types


from smp.config import FactoresTDV
from smp.database import TDVQueries
import logging


# Mock factores for tests
factores = FactoresTDV()


@pytest.fixture
def processor():
    with patch(
        "smp.database.TDVQueries.get_instance", return_value=Mock()
    ) as mock_get_instance:
        mock_processor = mock_get_instance.return_value
        # Bind the method to the mock object to provide 'self'
        mock_processor._procesar_costos_historicos_con_limites_previos = (
            types.MethodType(
                TDVQueries._procesar_costos_historicos_con_limites_previos,
                mock_processor,
            )
        )
        yield mock_processor


@pytest.fixture
def base_input():
    now = datetime.now()
    return [
        {
            "costo_textil": 30,
            "costo_manufactura": 25,
            "prendas_requeridas": 2,
            "esfuerzo_total": 5,
            "fecha_facturacion": now - timedelta(days=30),
        },
        {
            "costo_textil": 40,
            "costo_manufactura": 30,
            "prendas_requeridas": 1,
            "esfuerzo_total": 7,
            "fecha_facturacion": now - timedelta(days=365),
        },
    ]


def test_normal_case(processor, base_input, caplog):
    caplog.set_level(logging.INFO)
    res = processor._procesar_costos_historicos_con_limites_previos(base_input, "test")
    weight1, weight2 = 0.917808, 1.0  # 1 - 30/365, max(0.1, 1 - 365/365)
    sum_weights = weight1 + weight2
    assert res["costo_textil"] == pytest.approx(
        (10 * weight1 + 10 * weight2) / sum_weights, rel=1e-5
    )  # Both clipped to 10
    assert res["costo_manufactura"] == pytest.approx(
        (10 * weight1 + 10 * weight2) / sum_weights, rel=1e-5
    )  # 25/2=12.5→10, 30→10
    cols = [
        "costo_textil",
        "costo_manufactura",
        "costo_avios",
        "costo_materia_prima",
        "costo_indirecto_fijo",
        "gasto_administracion",
        "gasto_ventas",
    ]
    assert res["registros_ajustados_por_componente"] == {
        col: 2 if col in cols else 0
        for col in res["registros_ajustados_por_componente"]
    }
    assert res["total_ajustados"] == 14
    assert res["esfuerzo_promedio"] == 6.0
    assert res["registros_encontrados"] == 2
    assert res["estrategia_usada"] == "test"
    assert res["fecha_mas_reciente"] == base_input[0]["fecha_facturacion"]
    assert res["precision_estimada"] == 0.1
    assert res["version_calculo"] == "FLUIDA"
    assert "2 registros procesados con estrategia 'test', 14 ajustes" in caplog.text


def test_empty_input(processor):
    with pytest.raises(ValueError, match="Sin resultados"):
        processor._procesar_costos_historicos_con_limites_previos([], "test")


@pytest.mark.parametrize(
    "invalid_input",
    [
        [
            {
                "costo_textil": "invalid",
                "prendas_requeridas": "bad",
                "esfuerzo_total": None,
                "fecha_facturacion": "not_a_date",
            }
        ],
        [{"costo_textil": None, "prendas_requeridas": -1, "esfuerzo_total": "invalid"}],
    ],
)
def test_invalid_values(processor, invalid_input):
    res = processor._procesar_costos_historicos_con_limites_previos(
        invalid_input, "test"
    )
    print(res)
    assert all(
        list(
            res[col] == 0.05000000000000001
            for col in [
                "costo_textil",
                "costo_manufactura",
                "costo_avios",
                "costo_materia_prima",
                "costo_indirecto_fijo",
                "gasto_administracion",
                "gasto_ventas",
            ]
        )
    )
    assert res["esfuerzo_promedio"] == 6.0
    assert res["fecha_mas_reciente"] is None
    assert res["registros_ajustados_por_componente"]["costo_textil"] == 1
    assert res["total_ajustados"] == 7


def test_missing_keys(processor):
    res = processor._procesar_costos_historicos_con_limites_previos([{}], "test")
    assert all(
        list(
            res[col] == 0.05000000000000001
            for col in [
                "costo_textil",
                "costo_manufactura",
                "costo_avios",
                "costo_materia_prima",
                "costo_indirecto_fijo",
                "gasto_administracion",
                "gasto_ventas",
            ]
        )
    )
    assert res["esfuerzo_promedio"] == 6.0
    assert res["fecha_mas_reciente"] is None
    assert res["registros_encontrados"] == 1


def test_single_record(processor):
    now = datetime.now()
    input_data = [
        {
            "costo_textil": 20,
            "costo_manufactura": 30,
            "prendas_requeridas": 2,
            "esfuerzo_total": 8,
            "fecha_facturacion": now,
        }
    ]
    res = processor._procesar_costos_historicos_con_limites_previos(input_data, "test")
    assert res["costo_textil"] == 10.0  # 20/2, no clipping
    assert res["costo_manufactura"] == 10.0  # 30/2 clipped to 10
    assert res["registros_ajustados_por_componente"]["costo_manufactura"] == 1
    assert res["esfuerzo_promedio"] == 8.0


def test_zero_prendas(processor):
    now = datetime.now()
    res = processor._procesar_costos_historicos_con_limites_previos(
        [{"costo_textil": 15, "prendas_requeridas": 0, "fecha_facturacion": now}],
        "test",
    )
    assert res["costo_textil"] == 10.0  # 15/1 clipped to 10


def test_old_dates(processor):
    now = datetime.now()
    res = processor._procesar_costos_historicos_con_limites_previos(
        [
            {
                "costo_textil": 5,
                "prendas_requeridas": 1,
                "fecha_facturacion": now - timedelta(days=730),
            }
        ],
        "test",
    )
    assert res["costo_textil"] == 5.0  # Weight = 0.1, no clipping
    assert res["precision_estimada"] == 0.05
