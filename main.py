from card import Card
from player import Player
import numpy as np
import pandas as pd
from tabulate import tabulate
from collections import deque
from functools import partial

rng = np.random.default_rng(seed=4)  # Zufallszahlengenerator mit Seed

colors = ["red", "green", "blue", "yellow"]
spielerliste = [
Player("Gregor_samsa", 1337, []),
Player( "Billy_Bonka", 420, []),
Player("Testo_Torsten", 100, [])
]

def karten_mischen():
    karten = []
    for color in colors:
        karten.append(Card("",14))
        karten.append(Card("", 0))
        for value in range(13):
            karten.append(Card(color, value+1))
    rng.shuffle(karten)
    return karten

def wie_viele_runden_spielen_wir(spieler_anzahl):
    if spieler_anzahl == 3:
        return 9
    if spieler_anzahl == 4:
        return 15
    if spieler_anzahl == 5:
        return 12

    print("unzulaessige Spieleranzahl")
    return 0


#def punkte_tabelle(spielerliste):
    runden_anzahl = wie_viele_runden_spielen_wir(len(spielerliste))
    runden_index = pd.Index(range(1,runden_anzahl+1), name = "Runde")
    metriken = ["Angesagt", "Gemacht", "Punkte"]
    multi_index_columns = pd.MultiIndex.from_product([spielerliste, metriken], names = ["Spieler", "Metriken"])
    Tabelle = pd.DataFrame(index=runden_index, columns=multi_index_columns)
    return Tabelle


def erstelle_punkte_tabelle(spieler_namen: list[str]) -> pd.DataFrame:
    """
    Erstellt eine leere Pandas DataFrame für die Punkte-Tabelle des Wizard-Spiels.
    """
    spalten = pd.MultiIndex.from_product([spieler_namen, ['Angesagt', 'Gemacht', 'Punkte']],
                                         names=['Spieler', 'Kategorie'])
    punkte_tabelle = pd.DataFrame(columns=spalten)
    punkte_tabelle.index.name = 'Runde'
    # Wichtig: Explizite Typ-Konvertierung, um NaN zu vermeiden
    return punkte_tabelle.astype('int64')


def fuege_runde_punkte_hinzu(punkte_tabelle: pd.DataFrame, runden_nummer: int,
                             runden_daten: dict[str, list[int]]) -> pd.DataFrame:
    """
    Fügt die Ergebnisse einer Spielrunde zur Punkte-Tabelle hinzu.
    """
    neue_runde = {}
    for spieler, daten in runden_daten.items():
        neue_runde[(spieler, 'Angesagt')] = daten[0]
        neue_runde[(spieler, 'Gemacht')] = daten[1]
        neue_runde[(spieler, 'Punkte')] = daten[2]
    punkte_tabelle.loc[runden_nummer] = neue_runde
    return punkte_tabelle


def berechne_gesamtpunkte(tabelle: pd.DataFrame) -> pd.DataFrame:
    """
    Fügt eine Zeile 'GESAMT' hinzu, welche die Summe aller 'Punkte' für jeden Spieler enthält.
    """
    gesamt_punkte_reihe = tabelle.xs('Punkte', level='Kategorie', axis=1).sum(axis=0)
    gesamt_reihe = {}
    for spieler in tabelle.columns.get_level_values('Spieler').unique():
        gesamt_reihe[(spieler, 'Angesagt')] = 0
        gesamt_reihe[(spieler, 'Gemacht')] = 0
        gesamt_reihe[(spieler, 'Punkte')] = gesamt_punkte_reihe[spieler]
    tabelle.loc['GESAMT'] = gesamt_reihe
    return tabelle

def print_tabelle(tabelle: pd.DataFrame):
    """
    Gibt die Pandas Punkte-Tabelle lesbar in der Konsole aus.
    """
    print(tabelle.to_string())


# ==============================================================================
# II. SPIELLOGIK (ANGEPASST & BEREINIGT) 🃏
# ==============================================================================

def spiele_runde(spielerliste, runde, trumpf, tabelle, anzahl_runden):

    runden_daten = {}

    # 1. Kartenausgabe & Ansagen
    for spieler in spielerliste:
        print("-----")
        print(f"Spieler: {spieler.name}")

        print(f"Karten auf der Hand ({len(spieler.karten_auf_der_hand)}): {spieler.karten_auf_der_hand}")
        print("-----")


        anzahl_angesagte_stiche, _ = karten_bewerten(spieler.karten_auf_der_hand, trumpf, runde, 1.5)
        print(f" -> Angesagte Stiche: {anzahl_angesagte_stiche}")

        runden_daten[spieler.name] = [
            anzahl_angesagte_stiche,
            0,  # Gemacht (wird in der Stich-Simulation/Logik aktualisiert)
            0
        ]

    # 2. Stiche spielen & simulieren (Platzhalter)

    # Für die Demonstration nutzen wir die Simulationswerte, um die Tabelle zu füllen
    stiche_gemacht = {spieler.name: 0 for spieler in spielerliste}

    # Simulationswerte (Annahme: stiche_gemacht wurde durch die Stich-Logik gefüllt)
    if runde == 1:
        stiche_gemacht[spielerliste[0].name] = 1
        stiche_gemacht[spielerliste[1].name] = 0
        stiche_gemacht[spielerliste[2].name] = 1
    elif runde == 2:
        stiche_gemacht[spielerliste[0].name] = 3
        stiche_gemacht[spielerliste[1].name] = 1
        stiche_gemacht[spielerliste[2].name] = 0

        # 3. Punkte berechnen und Daten sammeln
    for spieler_name, daten in runden_daten.items():
        angesagt = daten[0]
        gemacht = stiche_gemacht[spieler_name]

        punkte = 0
        if angesagt == gemacht:
            punkte = 20 + gemacht * 10
        else:
            punkte = (abs(angesagt - gemacht)) * (-10)

        runden_daten[spieler_name] = [angesagt, gemacht, punkte]

    # 4. Tabelle füllen und ausgeben (NUR HIER)
    tabelle = fuege_runde_punkte_hinzu(tabelle, runde, runden_daten)

    print("\n-----------"
          f"ERGEBNISSE NACH RUNDE {runde}"
          "-----------")
    print_tabelle(tabelle)
    start_spieler_index = (runde % len(spielerliste)) - 1
    for i in range(runde):
        spiele_stich(spielerliste, start_spieler_index, trumpf, tabelle)

    # 5. Gesamtsumme hinzufügen, falls es die letzte Runde war
    if runde == anzahl_runden:
        tabelle = berechne_gesamtpunkte(tabelle)
        print("\n🏆 ENDSTAND DES SPIELS (inkl. GESAMT) 🏆")
        print_tabelle(tabelle)

    spielerliste_deque.rotate(-1)

    return tabelle


def starte_spiel(spielerliste, startrunde=1):

    runden_anzahl = wie_viele_runden_spielen_wir(len(spielerliste))
    spieler_namen_str = [spieler.name for spieler in spielerliste]
    tabelle = erstelle_punkte_tabelle(spieler_namen_str)

    print("\n===========================================")
    print(f"🃏 STARTE WIZARD-SPIEL mit {runden_anzahl} Runden 🃏")
    print("===========================================")

    for runde in range(startrunde, runden_anzahl + 1):
        print(f"\n====================== RUNDE {runde} ======================")

        karten = karten_mischen()

        # Kartenausteilen und Trumpf bestimmen
        restkarten = teile_karten_aus(karten, runde, spielerliste)
        trumpf = bestimme_trumpf(restkarten)

        print(f"📢 Startspieler: {spielerliste[(runde - 1) % len(spielerliste)].name}")
        print(f"👑 Trumpffarbe: {trumpf} | {runde} Karten pro Spieler")

        # spiele_runde führt Logik und Ausgabe durch
        tabelle = spiele_runde(spielerliste, runde, trumpf, tabelle, runden_anzahl)

    print("\nSpiel vorbei.")

def teile_karten_aus(karten, anzahl_karten, spielerliste):
    for i in range(anzahl_karten):
        for spieler in spielerliste:
            oberste_karte = karten.pop(0)
            spieler.karten_auf_der_hand.append(oberste_karte)

    return karten

def bestimme_trumpf(restkarten):
    trumpf_karte = restkarten[0]  # oberste Karte aufdecken
    if trumpf_karte.color in colors:
        trumpf_farbe = trumpf_karte.color

    elif trumpf_karte.value == 0:
        trumpf_farbe = "Narr"

    elif trumpf_karte.value == 14:
        haeufigkeiten = {}
        start_spieler = spielerliste[0]

        for karte in start_spieler.karten_auf_der_hand:
            farbe = karte.color
            if farbe:                                                   #ki
               haeufigkeiten[farbe] = haeufigkeiten.get(farbe,0) + 1

        if haeufigkeiten:
           haeufigste_farbe = max(haeufigkeiten, key=haeufigkeiten.get)  #ki
           trumpf_farbe = print(f' Ersatztrumpf für Zauberer: {haeufigste_farbe}')

        else: trumpf_farbe = print(f' Ersatztrumpf für Zauberer: {rng.choice(colors)}')

    return trumpf_farbe

def karten_bewerten(karten, trumpf_farbe, runde, bewertungs_grenze):
    anzahl_stiche = 0
    anzahl_karten = len(karten)
    score = 0
    gute_karten = []
    for karte in karten:

        if karte.value == 14:
            score_karte = 2

        elif  karte.color == trumpf_farbe:
            score_karte = karte.value / anzahl_karten

        else:
            score_karte = karte.value / (anzahl_karten * 2)

        if score_karte >= 1:
            gute_karten.append(karte)

        score += score_karte

        #print(f'karte {karte}, score {score_karte}')

        if score > bewertungs_grenze:
            anzahl_stiche += 1
            score = 0
    #for karte in gute_karten:
        #print(f'Die guten: {karte}')

    return anzahl_stiche, gute_karten




def spiele_stich(spielerliste, start_spieler_index, trumpf_farbe, tabelle):
    stich_karten = {}
    bedien_farbe = ""
    for i in range(len(spielerliste)):
        aktiver_spieler = spielerliste[(start_spieler_index + i)%len(spielerliste)]

        # finde alle erlaubten Karten
        moegliche_karten = finde_erlaubte_karten_für_Zug(aktiver_spieler.karten_auf_der_hand, bedien_farbe)

        #To Do: schlaue karte auswählen
        gelegte_karte = rng.choice(moegliche_karten)
        aktiver_spieler.karten_auf_der_hand.remove(gelegte_karte)
        stich_karten[aktiver_spieler.name] = gelegte_karte
        if bedien_farbe == "":
            bedien_farbe = gelegte_karte.color
    print(stich_karten)
    gewinner = gewinner_des_stiches(stich_karten, bedien_farbe, trumpf_farbe)
    print(gewinner)


    return stich_karten


#1: bedienfarbe --> größer?
    #2: keine bedienfarbe --> trumpf?
    #3: noch keine bedienfarbe
    #4: zauberer
    #5: brauch ich noch stich?


def schlaue_karte_auswaehlen(karten, stich_karten, bedien_farbe, trumpf_farbe):
    normale_karten = [karte for karte in karten if karte.color in colors]
    trumpf_karten = [karte for karte in karten if karte.color == trumpf_farbe]
    normale_karten_ohne_trumpf = [karte for karte in normale_karten if karte.color != trumpf_farbe]

    if 14 in stich_karten.values:
        karte = min(normale_karten_ohne_trumpf.value)
        return karte

    if bedien_farbe == "":
        karte = max(normale_karten_ohne_trumpf.value)
        return karte

    if bedien_farbe in normale_karten_ohne_trumpf:
        if trumpf_farbe not in stich_karten.values:
            if max(normale_karten_ohne_trumpf.value) > max(stich_karten.values):
                karte = max(normale_karten_ohne_trumpf.value)
                return karte
            karte = min(normale_karten_ohne_trumpf.value)





    trumpf_karten_im_stich = [karte for karte in stich_karten.values if karte.color == trumpf_farbe]
    if trumpf_karten_im_stich:
        if max(trumpf_karten.value) > max(trumpf_karten_im_stich.value):
            karte = max(trumpf_karten.value)
            return karte
        else:
            pass

    größere_karten = [
        karte for karte in normale_karten
        if karte.value > max(stich_karten.values) and karte.color == bedien_farbe
    ]







def finde_erlaubte_karten_für_Zug(karten, bedien_farbe):
    if bedien_farbe == "": 
        return karten
    bedien_farbe_karten = [karte for karte in karten if karte.color == bedien_farbe]
    if len(bedien_farbe_karten) == 0:
        return karten
    erlaubte_karten = [karte for karte in karten if karte.color == bedien_farbe or karte.color == ""]
    return erlaubte_karten



def gewinner_des_stiches(stich_karten, bedien_farbe, trumpf_farbe):

    alle_bedienkarten = []
    alle_trumpfkarten = []

    for spieler, karte in stich_karten.items():
        if karte.value == 14:
            gewinner = {spieler: karte}
            return gewinner

        if karte.color == trumpf_farbe:
            alle_trumpfkarten.append(karte.value)

        if karte.color == bedien_farbe:
            alle_bedienkarten.append(karte.value)

    for spieler, karte in stich_karten.items():
        if alle_trumpfkarten:
            if karte.color == trumpf_farbe and karte.value == max(alle_trumpfkarten):
                gewinner = {spieler: karte}
                return gewinner

        else:
            if karte.color == bedien_farbe and karte.value == max(alle_bedienkarten):
                gewinner = {spieler: karte}
                return gewinner





spielerliste = [
Player("Gregor_samsa", 1337, []),
Player( "Billy_Bonka", 420, []),
Player("Testo_Torsten", 100, [])
]

spielerliste_deque = deque(spielerliste)
starte_spiel(spielerliste,1)
