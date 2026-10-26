from src.services.config import DEFAULT_PINNED_ASINS, load_config

EXPECTED_DEFAULTS = (
    "B0GQVP8RLD",  # Estée Lauder Double Wear
    "B0028P5TOW",  # Armani Luminous Silk
    "B0HC436QM3",  # Westmore Beauty
    "B0BFRV3GCS",  # L'Oréal True Match
    "B00AVUDDC6",  # tarte BB blur (fair)
    "B0BNWBT2G2",  # Lancôme Teint Idole
    "B078QZDJFB",  # NARS Natural Radiant Longwear
)


def test_default_pinned_asins(monkeypatch):
    monkeypatch.delenv("PINNED_ASINS", raising=False)
    assert load_config().pinned_asins == EXPECTED_DEFAULTS
    assert DEFAULT_PINNED_ASINS.split(",") == list(EXPECTED_DEFAULTS)


def test_pinned_asins_can_be_overridden_or_disabled(monkeypatch):
    monkeypatch.setenv("PINNED_ASINS", " b0aaaaaaa1 , B0AAAAAAA1, B0BBBBBBB2 ")
    assert load_config().pinned_asins == ("B0AAAAAAA1", "B0BBBBBBB2")

    monkeypatch.setenv("PINNED_ASINS", "")
    assert load_config().pinned_asins == ()
