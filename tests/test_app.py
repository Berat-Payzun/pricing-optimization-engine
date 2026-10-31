"""Smoke test: the whole Streamlit app runs on the sample data, with every network call stubbed."""

import pytest

import macro_api
from config import FALLBACK_MACRO
from macro_api import MacroValue

APP = str(__import__("pathlib").Path(__file__).resolve().parents[1] / "src" / "app.py")


@pytest.fixture
def app(monkeypatch):
    from streamlit.testing.v1 import AppTest

    def inflation(country):
        return MacroValue(FALLBACK_MACRO[country][0], None, "fallback default", ok=False)

    def fx(country):
        _, rate, change = FALLBACK_MACRO[country]
        return MacroValue(rate, None, "fallback default", ok=False, change_pct=change)

    monkeypatch.delenv("FRED_API_KEY", raising=False)
    monkeypatch.setattr(macro_api, "get_inflation", inflation)
    monkeypatch.setattr(macro_api, "get_fx", fx)
    return AppTest.from_file(APP, default_timeout=300).run()


def test_app_runs_and_auto_picks_a_model(app):
    assert not app.exception
    assert app.radio(key="model_kind").value == "auto"
    assert any("Auto chose" in c.value for c in app.caption)
    labels = [m.label for m in app.metric]
    assert "Recommended price" in labels[0]


@pytest.mark.parametrize("changes", [
    {"model_kind": "loglog", "ending": ".99", "test_step": 1.0},
    {"country": "TR", "use_trend": True, "variable_fees": 15.0, "prices_incl_vat": True},
])
def test_app_survives_setting_changes(app, changes):
    for key, value in changes.items():
        widget = next(w for w in (app.radio, app.selectbox, app.slider, app.toggle, app.number_input)
                      if any(x.key == key for x in w))
        next(x for x in widget if x.key == key).set_value(value)
    app.run()
    assert not app.exception
