import random

# Card - predstavlja jednu kartu. Ima boju i vrijednost
# -------------------------------------------------------------------------

class Card(object):
    
    def __init__(self, c, v):
        self.color = c
        self.value = v
    
    async def show_card(self):
        print(self.color, self.value)


# Deck - predstavlja spil karata. Prati stanje spila i odbacene hrpe karata
# -------------------------------------------------------------------------

class Deck(object):
    
    COLORS = ["RED","GREEN","BLUE","YELLOW"]
    ACTION = ["SKIP","REVERSE","PLAY2"]
    WILD = ["COLOR","PLAY4"]
    
    def __init__(self):
        self.cards = []
        self.cards_disc = []
    
    async def build(self):

        cards_zero   = [Card(c,0) for c in self.COLORS] #nula se definira samo jednom za svaku boju, znaci ukupno 4 nule
        cards_normal = [Card(c,v) for c in self.COLORS for v in range(1,10)]*2 #po 2 za svaku kombinaciju boje i broja, ukupno 18 po boji
        cards_action = [Card(c,v) for c in self.COLORS for v in self.ACTION]*2 #po 2 za svaku boju i akciju, ukupno 8 po akciji
        cards_wild   = [Card("WILD",v) for v in self.WILD]*4 #4 color i 4 draw four
        
        cards_all = cards_normal + cards_action + cards_zero + cards_wild
        for card in cards_all: 
            self.cards.append(card)
    
    
    async def play(self, card):
        #nije potreban remove na cards listu jer se prilikom izvlacenja radi pop()
        self.cards_disc.append(card)
    
    async def shuffle(self):
        random.shuffle(self.cards)
   

    async def draw_from_deck(self):
        #reset spila ako vise nema karata
        if len(self.cards) == 0:
            self.cards = self.cards_disc
            self.cards_disc = []
            self.cards_disc.append(self.cards[-1])
            await self.shuffle()
            
        return self.cards.pop()
    

    # Pomocne funkcije
    # ---------------------------------
    async def show_deck(self):
        for c in self.cards:
            await c.show_card()
                 
    
    async def show_discarded(self):
        for c in self.cards_disc:
            await c.show_card()

    async def show_top(self):
        return self.cards_disc[-1]