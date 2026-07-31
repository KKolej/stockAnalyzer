import json
import math
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum

from stock_agents.api.serializer import to_json


class Kolor(Enum):
    RED = "red"


@dataclass
class Wewnetrzna:
    x: int = 1


@dataclass
class Przyklad:
    name: str = "test"
    value: float | None = None
    when: date | None = None
    inner: Wewnetrzna = field(default_factory=Wewnetrzna)
    items: list[int] = field(default_factory=list)

    @property
    def doubled(self) -> str:
        return self.name * 2


class TestToJson:
    def test_typy_proste_bez_zmian(self):
        assert to_json(None) is None
        assert to_json(5) == 5
        assert to_json("abc") == "abc"
        assert to_json(True) is True
        assert to_json(1.5) == 1.5

    def test_nan_i_inf_na_none(self):
        # NaN/inf wywala json.dumps po stronie n8n — muszą zniknąć
        assert to_json(float("nan")) is None
        assert to_json(math.inf) is None
        assert to_json(-math.inf) is None

    def test_enum_na_wartosc(self):
        assert to_json(Kolor.RED) == "red"

    def test_daty_na_isoformat(self):
        assert to_json(date(2026, 7, 28)) == "2026-07-28"
        assert to_json(datetime(2026, 7, 28, 12, 30)) == "2026-07-28T12:30:00"

    def test_dataclass_rekurencyjnie_z_property(self):
        out = to_json(Przyklad(value=float("nan"), when=date(2026, 1, 1), items=[1, 2]))
        assert out["name"] == "test"
        assert out["value"] is None
        assert out["when"] == "2026-01-01"
        assert out["inner"] == {"x": 1}
        assert out["items"] == [1, 2]
        assert out["doubled"] == "testtest"

    def test_dict_i_lista_rekurencyjnie(self):
        out = to_json({"a": [float("nan"), Kolor.RED], "b": {"c": date(2026, 1, 1)}})
        assert out == {"a": [None, "red"], "b": {"c": "2026-01-01"}}

    def test_wynik_jest_json_serializowalny(self):
        out = to_json(Przyklad(value=math.inf))
        json.dumps(out)  # nie może rzucić

    def test_nieznany_typ_na_string(self):
        assert to_json(object()).startswith("<object")
