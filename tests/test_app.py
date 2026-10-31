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


def test_sample_data_shows_every_product(app):
    assert app.selectbox(key="product").options == ["Classic Mug", "Gift Set", "New Tumbler", "Travel Mug"]
    table = next(df.value for df in app.dataframe if "Product" in df.value.columns)
    assert list(table["Product"]) == ["Classic Mug", "Gift Set", "New Tumbler", "Travel Mug"]
    status = dict(zip(table["Product"], table["Status"]))
    assert status["Classic Mug"] == "OK" and "Only 2 month(s)" in status["New Tumbler"]


def test_too_short_product_shows_an_error_not_a_crash(app):
    app.selectbox(key="product").set_value("New Tumbler").run()
    assert not app.exception
    assert any("Only 2 month(s)" in e.value for e in app.error)


def test_fees_eating_the_whole_price_show_the_no_profit_card(app):
    app.number_input(key="variable_fees").set_value(90.0)
    app.toggle(key="prices_incl_vat").set_value(True).run()
    app.number_input(key="vat_US").set_value(20.0)  # US VAT is 0 by default; 90% fees > 1/1.2 net share
    app.run()
    assert not app.exception
    assert any("No price covers the variable costs" in e.value for e in app.error)
    assert any("take the whole net price" in w.value for w in app.sidebar.warning)
    assert not any("range of the optimum" in c.value for c in app.caption)  # no 90% range
