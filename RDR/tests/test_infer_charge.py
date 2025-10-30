import pytest
from RDR.extract_input import infer_charge


def test_positive_with_peg():
    label, conf, prov = infer_charge(
        "PEGylated micelle, positively charged surface",
        "A PEGylated micelle with cationic surface modifiers",
        "",
    )
    assert label == "positive"
    assert conf >= 0.9


def test_positive_zeta():
    label, conf, prov = infer_charge(
        "PEGylated micelle",
        "Measured zeta potential +35 mV (highly positive)",
        "",
    )
    assert label == "positive"
    assert conf >= 0.9


def test_conflict_zeta_text_ambiguous():
    label, conf, prov = infer_charge(
        "Cationic coating",
        "Measured zeta -38 mV (strongly negative)",
        "",
    )
    assert label == "ambiguous"


def test_neutral_only():
    label, conf, prov = infer_charge(
        "PEGylated nanoparticle",
        "Surface shows PEG; expected neutral or uncharged behaviour",
        "",
    )
    # depending on cues this may be 'neutral' with moderate confidence
    assert label in ("neutral", "unknown") or label == "neutral"
    # if neutral, confidence should be moderate
    if label == "neutral":
        assert conf >= 0.7
