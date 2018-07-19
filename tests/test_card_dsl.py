from core.card import Card


def test_card_dsl():
    class Bar(Card):
        a = 'Moo'

    assert not hasattr(Bar, 'a')
    bar = Bar()
    assert bar.a == 'Moo'
