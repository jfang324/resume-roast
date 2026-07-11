"""SETTING_SPECS derivation from Settings field metadata."""

from resume_roast.persistence.settings.types import SETTING_SPECS, Settings


def test_at_least_one_setting_is_registered() -> None:
    assert SETTING_SPECS


def test_specs_exclude_bookkeeping_fields() -> None:
    assert "unrecognized" not in {spec.field for spec in SETTING_SPECS}


def test_every_spec_has_a_non_blank_label_and_choices() -> None:
    for spec in SETTING_SPECS:
        assert spec.label.strip()
        assert spec.choices


def test_every_default_is_an_allowed_choice() -> None:
    defaults = Settings()
    for spec in SETTING_SPECS:
        value = getattr(defaults, spec.field)
        values = value if spec.many else (value,)
        for item in values:
            assert item in spec.choices


def test_ensemble_models_is_the_only_multi_valued_setting() -> None:
    many_fields = {spec.field for spec in SETTING_SPECS if spec.many}
    assert many_fields == {"ensemble_models"}
