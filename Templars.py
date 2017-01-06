import card
from card import Card, Faction


class ConditionalAttack ():
    def __init__(self, card, condition):
        self.player = card.owner
        self.enemy = self.player.getEnemy()
        self.original = self.enemy.attack
        self.enemy.attack = self

        self.condition = condition

    def destroy(self):
        self.enemy.attack = self.original

    def __call__(self, cardIndex, targetIndex, zone):
        if (zone == 0 and self.condition(self.player)):
            print "Attack failed."
            return
        self.original(cardIndex, targetIndex, zone)


def strix():
    return Card(
        name="Strix",
        image="owl.png",
        cost=1,
        rank=1
        )


def equus():
    def equusGetRank(self):
        return 2 if (self.owner.manaCap % 2 == 0) else 5

    equus = Card(
        name="Equus",
        image="horse-head.png",
        cost=3,
        )
    equus.setRankAbility(equusGetRank)

    return equus


def grail():
    def grailAttackCondition(player):
        return player.manaCap % 2 == 0

    def grailInit(self):
        self.grailAttack = ConditionalAttack(self, grailAttackCondition)

    def grailDestroy(self):
        self.grailAttack.destroy()

    grail = Card(
        name="Grail",
        image="holy-grail.png"
        )
    grail.setSpawnAbility(grailInit)
    grail.setDeathAbility(grailDestroy)
    return grail

Templars = Faction(
    name="Templars",
    iconPath="./templar_icons",
    cardBack="templar-shield.png",
    deck=[
        card.one(), card.one(), card.one(), card.one(),
        card.sweep(), card.sweep(),
        card.spellBlade(),
        strix(),
        equus(),
        equus(),
        grail()
        ]
    )
