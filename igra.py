class Igra():
    IGRACI = { # popis agenata koji igraju, centralizirano na jednom mjestu
        1: 'agent@rec.foi.hr',
        2: 'posiljatelj@rec.foi.hr',
        3: 'primatelj@rec.foi.hr'
    }

    hand_count = { # vizualno znanje igraca koliko tko ima karata, na pocetku uvijek 7
        1: 7,
        2: 7,
        3: 7
    }

    redoslijed = 1 # 1 lijevo na desno, 2 desno na lijevo
    igrac_na_redu = 1
    called_color = "" # sluzi za postavljanje boje, npr. nakon draw 4

    uno = { # evidencija da li je pojedini igrac najavio uno rundu prije
        1: 0,
        2: 0,
        3: 0
    }

    async def najavljuje_uno(self, igrac): # postavlja se najava uno, traje za jednu rundu
        self.uno[igrac] = 1

    async def sljedeci_igrac(self): # postavlja sljedeceg igraca
        if self.redoslijed == 1:
            if self.igrac_na_redu + 1 > 3:
                self.igrac_na_redu = 1
            else:
                self.igrac_na_redu += 1
        if self.redoslijed == 2:
            if self.igrac_na_redu - 1 < 1:
                self.igrac_na_redu = 3
            else:
                self.igrac_na_redu -= 1
    
    async def dohvati_sljedeceg_igraca(self): # informativno dohvaca sljedeceg igraca
        if self.redoslijed == 1:
            if self.igrac_na_redu + 1 > 3:
                return 1
            else:
                return self.igrac_na_redu + 1
        if self.redoslijed == 2:
            if self.igrac_na_redu - 1 < 1:
                return 3
            else:
                return self.igrac_na_redu - 1
    
    async def dohvati_prethodnog_igraca(self): # informativno dohvaca prethodnog igraca
        if self.redoslijed == 1:
            if self.igrac_na_redu - 1 == 0:
                return 3
            else:
                return self.igrac_na_redu - 1
        if self.redoslijed == 2:
            if self.igrac_na_redu + 1 > 3:
                return 1
            else:
                return self.igrac_na_redu + 1

    async def promijeni_redoslijed(self): # mijenja redoslijed igranja
        if self.redoslijed == 1:
            self.redoslijed = 2
        else:
            self.redoslijed = 1
