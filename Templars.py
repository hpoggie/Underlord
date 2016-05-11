import card
from card import Card, Faction

strix = Card({
    'name': "Strix",
    'image': "owl.png",
    'cost': 1,
    'rank': 1
    })

equus = Card({
    'name': "Equus",
    'image': "horse-head.png"
    })

grail = Card({
    'name': "Grail",
    'image': "holy-grail.png"
    })

Templars = Faction({
    'name': "Templars",
    'iconPath': "./templar_icons",
    'cardBack': "templar-shield.png",
    'deck': [
        card.one, card.one, card.one, card.one,
        strix,
        equus,
        equus,
        grail
        ]
    })
