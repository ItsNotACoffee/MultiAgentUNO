import spade
import time
import random
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from karte import *
from igra import *

class Igrac(Agent):

    def postavi_parametre(self, is_dealer, broj):
        self.hand = list()
        self.is_dealer = is_dealer
        self.broj = broj

    async def print_info(self, karta):
        odabrana_karta = ""
        if karta:
            odabrana_karta = karta.color + " " + str(karta.value)
        sve_karte = ""
        na_stolu = ""
        top = await deck.show_top()
        if top:
            na_stolu = top.color + " " + str(top.value)
        for card in self.hand:
            if not sve_karte:
                sve_karte += "" + card.color + " " + str(card.value)
            else:
                sve_karte += ", " + card.color + " " + str(card.value)
        print("\n")
        print("=================================================================")
        print("Igrac: " + str(self.broj))
        print("U ruci: " + sve_karte)
        print("Potez: " + odabrana_karta)
        print("-----------------------------------------------------------------")
        print("Na stolu: " + na_stolu)
        print("-----------------------------------------------------------------")
        print("Broj karata u spilu: " + str(len(deck.cards)))
        print("Broj karata u hrpi: " + str(len(deck.cards_disc)))
        print("Karte igraca 1: " + str(igra.hand_count[1]))
        print("Karte igraca 2: " + str(igra.hand_count[2]))
        print("Karte igraca 3: " + str(igra.hand_count[3]))
        print("=================================================================")

    async def najzastupljenija_boja(self):
        colors = { #temp dict za brojanje
            'RED': 0,
            'GREEN': 0,
            'YELLOW': 0,
            'BLUE': 0
        }
        for card in self.hand:
            if card.color in deck.COLORS:
                colors[card.color] += 1
        color = None
        color_name = None
        for k,v in colors.items():
            if color == None:
                color = v
            elif v > color:
                color = v
        for k,v in colors.items():
            if v == color:
                color_name = k
        return color_name

    async def izvuci_karte(self, broj_karata):
        for i in range(0, broj_karata):
            card = await deck.draw_from_deck()
            self.hand.append(card)
            igra.hand_count[self.broj] += 1

    class Automat(FSMBehaviour):
        async def on_start(self):
            print("Pokrece se igrac " + str(self.agent.broj))

    class KrajIgre(State):
        async def run(self):
            if self.agent.broj == 1:
                await self.agent.stop()
            else:
                msg = spade.message.Message(
                to=igra.IGRACI[1],
                body="kraj")
                await self.send(msg)

    class CekajRed(State):
        async def run(self):
            print("Igrac " + str(self.agent.broj) + ": cekam red")
            start = False
            kraj = False
            while not start:
                msg = await self.receive(timeout=20)
                if msg:
                    if msg.body == 'zapocni': #igrac zapocinje
                        start = True
                    elif 'karta' in msg.body: #igrac dobiva kartu
                        card = Card(msg.body.split(":")[1], msg.body.split(":")[2])
                        self.agent.hand.append(card)
                    elif 'draw' in msg.body: #igrac mora uzeti n karata
                        print("Igrac " + str(self.agent.broj) + ": vucem karte")
                        broj_karata = int(msg.body.split(":")[1])
                        await self.agent.izvuci_karte(broj_karata)
                    elif 'wild' in msg.body: #igrac odigrava wild color na pocetku igre
                        color = await self.agent.najzastupljenija_boja()
                        igra.called_color = color
                        start = True
                    elif 'kraj' in msg.body: #igra je gotova
                        kraj = True
                        start = True

            if kraj:
                self.set_next_state("KrajIgre")
            else:
                self.set_next_state("Odigraj")
    
    class Odigraj(State):
        async def obavijesti_igraca(self, igrac, poruka):
            msg = spade.message.Message(
                to=igrac,
                body=poruka)
            await self.send(msg)

        async def odigraj_wild(self, type):
            color = await self.agent.najzastupljenija_boja()
            print("Igrac " + str(igra.igrac_na_redu) + ": biram boju " + str(color))
            igra.called_color = color
            await igra.sljedeci_igrac()
            if type == 'PLAY4':
                await self.obavijesti_igraca(igra.IGRACI[igra.igrac_na_redu], "draw:4")

        async def odigraj_drawtwo(self):
            await igra.sljedeci_igrac()
            await self.obavijesti_igraca(igra.IGRACI[igra.igrac_na_redu], "draw:2")
            await igra.sljedeci_igrac()

        async def odigraj_reverse(self):
            await igra.promijeni_redoslijed()
            await igra.sljedeci_igrac()

        async def odigraj_skip(self):
            await igra.sljedeci_igrac()
            await igra.sljedeci_igrac()

        async def odigraj(self, card):
            if card == None:
                await igra.sljedeci_igrac()
            else:
                self.agent.hand.remove(card)
                await deck.play(card)
                igra.hand_count[self.agent.broj] -= 1
                if card.value in deck.ACTION:
                    if card.value == 'SKIP':
                        await self.odigraj_skip()
                    elif card.value == 'REVERSE':
                        await self.odigraj_reverse()
                    elif card.value == 'PLAY2':
                        await self.odigraj_drawtwo()
                elif card.color == 'WILD':
                    await self.odigraj_wild(card.value)
                else:
                    await igra.sljedeci_igrac()
        
        async def provjeri_uno(self):
            sljedeci = await igra.dohvati_sljedeceg_igraca()
            prethodni = await igra.dohvati_prethodnog_igraca()

            karte_sljedeceg = igra.hand_count[sljedeci]
            karte_prethodnog = igra.hand_count[prethodni]

            najavio_sljedeci = igra.uno[sljedeci]
            najavio_prethodni = igra.uno[prethodni]

            nisu_najavili = list()
            if karte_sljedeceg == 1:
                if najavio_sljedeci == 0:
                    nisu_najavili.append(sljedeci)
            if karte_prethodnog == 1:
                if najavio_prethodni == 0:
                    nisu_najavili.append(prethodni)
            
            return nisu_najavili

        async def odaberi_kartu(self, prozvana_boja):
            wild = []
            action_color = []
            action_sign = []
            color_color = []
            color_sign = []
            sljedeci = await igra.dohvati_sljedeceg_igraca()
            na_hrpi = await deck.show_top()
            broj_karata_sljedeceg = igra.hand_count[sljedeci]

            #pronadi sve karte koje je moguce odigrati u ruci
            for card in self.agent.hand:
                if card.color == 'WILD':
                    if card.value == 'COLOR':
                        wild.append(card)
                if card.value in deck.ACTION:
                    if card.color == na_hrpi.color:
                        action_color.append(card)
                    elif card.color == prozvana_boja:
                        action_color.append(card)
                    elif na_hrpi.value in deck.ACTION:
                        if card.value == na_hrpi.value:
                            action_sign.append(card)
                else:
                    if card.color == na_hrpi.color:
                        color_color.append(card)
                    elif card.color == prozvana_boja:
                        color_color.append(card)
                    elif not na_hrpi.value in deck.ACTION:
                        if card.value == na_hrpi.value:
                            color_sign.append(card)
            
            for card in self.agent.hand:
                if card.color == 'WILD':
                    if card.value == 'PLAY4':
                        if len(action_color) == 0 & len(color_sign) == 0:
                            wild.append(card)

            action = action_color + action_sign
            color = color_color + color_sign

            #odabir strategije
            odabrana_karta = None
            if broj_karata_sljedeceg < 4: #prioritiziraj +4 i +2
                for card in wild:
                    if card.value == 'PLAY4':
                        odabrana_karta = card
                        break
                if odabrana_karta == None:
                    for card in action:
                        if card.value == 'PLAY2':
                            odabrana_karta = card
                            break
                if odabrana_karta == None: #ako nema +4 i +2, bilo koja akcija
                    for card in action:
                        odabrana_karta = card
                        break
                if odabrana_karta == None: #ako nema akcija, onda wild color
                    for card in wild:
                        if card.value == 'COLOR':
                            odabrana_karta = card
                            break
                if odabrana_karta == None: #ako nema akcija i wild, bilo koja color
                    for card in color:
                        odabrana_karta = card
                        break
            sve_moguce = action + color + wild

            if len(sve_moguce) > 0:
                if odabrana_karta == None: #ako se ne primjenjuje strategija, uzmi random iz mogucih
                    index = random.randint(0, len(sve_moguce) - 1)
                    odabrana_karta = sve_moguce[index]

            return odabrana_karta

        async def run(self):
            print("Igrac " + str(self.agent.broj) + ": odigravam")
            time.sleep(2) #simulacija trajanja
            prozvana_boja = igra.called_color

            nisu_najavili = await self.provjeri_uno()
            if len(nisu_najavili) > 0:
                for igrac in nisu_najavili:
                    print("Igrac " + str(self.agent.broj) + ": igrac " + str(igrac) + " nije najavio UNO!")
                    await self.obavijesti_igraca(igra.IGRACI[igrac], "draw:2") #igrac koji nije najavio uno, vuce 2 karte

            odabrana_karta = await self.odaberi_kartu(prozvana_boja)
            await self.agent.print_info(odabrana_karta)
            if odabrana_karta == None: #nema izbora, mora izvuci kartu
                await self.agent.izvuci_karte(1)
                odabrana_karta = await self.odaberi_kartu(prozvana_boja)
                await self.agent.print_info(odabrana_karta)

            igra.uno[self.agent.broj] = 0 #reset vrijednosti za najavu uno ako je sada broj karata u ruci veci od 1

            await self.odigraj(odabrana_karta)
            if odabrana_karta: # prozvana boja se resetira kada naide igrac koji moze odigrati za tu boju
                if odabrana_karta.color != 'WILD':
                    if prozvana_boja != "": 
                        igra.called_color = ""

            if len(self.agent.hand) == 1:
                percentage = random.randint(1, 5)
                if percentage < 5: # u 20% slucajeva, igrac ce zaboraviti reci UNO
                    await igra.najavljuje_uno(self.agent.broj)
                    print("Igrac " + str(self.agent.broj) + ": UNO!")
            
            if len(self.agent.hand) == 0:
                print("Igrac " + str(self.agent.broj) + " je pobjednik, igra se zavrsava!")
                self.set_next_state("KrajIgre")
            else:
                await self.obavijesti_igraca(igra.IGRACI[igra.igrac_na_redu], "zapocni")
                self.set_next_state("CekajRed")

    class PostaviIgru(State):
        async def obavijesti_igraca(self, igrac, poruka):
            msg = spade.message.Message(
                to=igrac,
                body=poruka)
            await self.send(msg)

        async def postavi_pocetnu_kartu(self):
            valid = False
            pocetna = None
            while not valid: #ako je draw 4, vrati u deck i vuci novu
                valid = True
                pocetna = await deck.draw_from_deck()
                if pocetna.color == "WILD":
                    if pocetna.value == "PLAY4":
                        deck.cards.insert(0, pocetna)
                        valid = False
                        
            deck.cards_disc.append(pocetna)
            print("Igrac " + str(self.agent.broj) + ": pocetna karta je " + pocetna.color + " " + str(pocetna.value))

        async def run(self):
            print("Igrac " + str(self.agent.broj) + ": postavljam igru")
            global deck
            deck = Deck()
            await deck.build()
            await deck.shuffle()

            index = 0
            print("Igrac " + str(self.agent.broj) + ": dijelim karte")
            for i in range(1,22):
                index += 1
                agent = ""
                card = await deck.draw_from_deck()
                if index == 1:
                    agent = "primatelj@rec.foi.hr"
                elif index == 2:
                    agent = "posiljatelj@rec.foi.hr"

                if index == 3:
                    self.agent.hand.append(card)
                    index = 0
                else:
                    await self.obavijesti_igraca(agent, "karta:" + str(card.color) + ":" + str(card.value))
            
            time.sleep(1) #stavljeno samo da svi igraci stignu dobiti sve karte
            print("Igrac " + str(self.agent.broj) + ": zapocinjemo igru")
            await self.postavi_pocetnu_kartu()
            top = await deck.show_top()
            if top.color == 'WILD': #ovdje nikada nece biti wild draw 4
                await igra.sljedeci_igrac()
                await self.obavijesti_igraca(igra.IGRACI[igra.igrac_na_redu], "wild")
                self.set_next_state("CekajRed")
            elif top.value in deck.ACTION:
                if top.value == 'PLAY2':
                    await igra.sljedeci_igrac()
                    await self.obavijesti_igraca(igra.IGRACI[igra.igrac_na_redu], "draw:2")
                    await igra.sljedeci_igrac()
                    await self.obavijesti_igraca(igra.IGRACI[igra.igrac_na_redu], "zapocni")
                    self.set_next_state("CekajRed")
                if top.value == 'REVERSE':
                    await igra.promijeni_redoslijed()
                    self.set_next_state("Odigraj")
                if top.value == 'SKIP':
                    await igra.sljedeci_igrac()
                    await igra.sljedeci_igrac()
                    await self.obavijesti_igraca(igra.IGRACI[igra.igrac_na_redu], "zapocni")
                    self.set_next_state("CekajRed")
            else: #color
                self.set_next_state("Odigraj")

    async def setup(self):
        fsm = self.Automat()
        if self.is_dealer:
            fsm.add_state(name="PostaviIgru", state=self.PostaviIgru(), initial=True)
            fsm.add_state(name="CekajRed", state=self.CekajRed())
        else:
            fsm.add_state(name="PostaviIgru", state=self.PostaviIgru())
            fsm.add_state(name="CekajRed", state=self.CekajRed(), initial=True)
        fsm.add_state(name="Odigraj", state=self.Odigraj())
        fsm.add_state(name="KrajIgre", state=self.KrajIgre())
        fsm.add_transition(source="PostaviIgru", dest="CekajRed")
        fsm.add_transition(source="PostaviIgru", dest="Odigraj")
        fsm.add_transition(source="CekajRed", dest="Odigraj")
        fsm.add_transition(source="CekajRed", dest="KrajIgre")
        fsm.add_transition(source="Odigraj", dest="CekajRed")
        fsm.add_transition(source="Odigraj", dest="KrajIgre")
        self.add_behaviour(fsm)

if __name__ == '__main__':
    global igra
    igra = Igra()

    prviIgrac = Igrac(igra.IGRACI[1], "tajna")
    prviIgrac.postavi_parametre(True, 1)
    drugiIgrac = Igrac(igra.IGRACI[2], "tajna")
    drugiIgrac.postavi_parametre(False, 2)
    treciIgrac = Igrac(igra.IGRACI[3], "tajna")
    treciIgrac.postavi_parametre(False, 3)
    time.sleep(1)

    drugiIgrac.start()
    treciIgrac.start()
    time.sleep(1)
    prviIgrac.start()

    while not prviIgrac.is_alive():
        time.sleep(1)
        #wait

    while prviIgrac.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    prviIgrac.stop()
    drugiIgrac.stop()
    treciIgrac.stop()
    spade.quit_spade()