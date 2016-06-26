import card
from card import Card, Faction

def strix ():
    return Card({
        'name': "Strix",
        'image': "owl.png",
        'cost': 1,
        'rank': 1
        })

def equus ():
    def equusGetRank (self):
        return 2 if (self.owner.manaCap % 2 == 0) else 5

    equus = Card({
        'name': "Equus",
        'image': "horse-head.png",
        'cost': 3,
        })
    equus.setRankAbility(equusGetRank)

    return equus

def grail ():
    return Card({
        'name': "Grail",
        'image': "holy-grail.png"
        })

Templars = Faction({
    'name': "Templars",
    'iconPath': "./templar_icons",
    'cardBack': "templar-shield.png",
    'deck': [
        card.one(), card.one(), card.one(), card.one(),
        card.sweep(), card.sweep(),
        card.spellBlade(),
        strix(),
        equus(),
        equus(),
        grail()
        ]
    })
