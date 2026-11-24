from mailroom.subscribers import import_rows



def test_model_accepts_maria_sara_tom_ines() -> None:
    accepted, _ = import_rows("data/new-signups.csv")
    assert [s.first_name for s in accepted] == ["Maria", "Sara", "Tom", "Ines"]


def test_model_rejects_omar_lena_kofi_hana_with_reasons() -> None:
    _, rejected = import_rows("data/new-signups.csv")
    assert [name for name, _ in rejected] == ["Omar", "Lena", "Kofi", "Hana"]
    reasons = dict(rejected)
    assert "email" in reasons["Omar"]
    assert "consent" in reasons["Lena"]
    assert "group" in reasons["Kofi"]
    assert "joined_on" in reasons["Hana"]
