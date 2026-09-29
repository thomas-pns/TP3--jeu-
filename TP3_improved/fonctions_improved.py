import random as r
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load data
with open(BASE_DIR / "mots.json", encoding="utf-8") as file:
    mots = json.load(file)

with open(BASE_DIR / "bdd.json", encoding="utf-8") as file:
    joueurs = json.load(file)

def affiche_mot(lst):
    return " ".join(lst)

def valide_lettre(lettre):
    LETTRES = "abcdefghijklmnopqrstuvwxyz"
    saisie = lettre.strip().lower()
    if saisie in LETTRES and len(saisie) == 1:
        return True, saisie
    return False, saisie

def ajouter_statistique(joueur, win, restantes, mot, lettres_utilisees):
    if win:
        joueur["streak"] += 1
        joueur["historique"].append({"mot": mot, "win": True, "tentatives_restantes": restantes, "lettres_utilisees": lettres_utilisees})
    else:
        joueur["streak"] = 0
        joueur["historique"].append({"mot": mot, "win": False, "tentatives_restantes": restantes, "lettres_utilisees": lettres_utilisees})
    with open(BASE_DIR / "bdd.json", "w", encoding="utf-8") as f:
        json.dump(joueurs, f, indent=4, ensure_ascii=False)

def choisir_mot_joueur1():
    """Player 1 enters a word to be guessed."""
    while True:
        mot = input("Joueur 1, entrez le mot à faire deviner (lettres uniquement) : ").strip()
        if mot.isalpha() and len(mot) >= 3:
            return mot.lower()
        print("Mot invalide. Veuillez entrer uniquement des lettres, longueur minimale 3.")

def deviner_lettre(tentatives):
    while True:
        lettre = input(f"Joueur 2, proposez une lettre ({tentatives} tentatives restantes) : ").strip()
        ok, lettre = valide_lettre(lettre)
        if ok:
            return lettre
        print("Entrée invalide. Une seule lettre de l'alphabet.")

def tour_devinette(mot_secret, essais_max):
    masque = ["_"] * len(mot_secret)
    masque[0] = mot_secret[0]  # reveal first letter as original
    lettres_utilisees = set()
    erreurs = 0
    while essais_max - erreurs > 0 and "_" in masque:
        print("\nMot :", affiche_mot(masque))
        print(f"Lettres utilisées : {', '.join(sorted(lettres_utilisees))}")
        lettre = deviner_lettre(essais_max - erreurs)
        if lettre in lettres_utilisees:
            print("Vous avez déjà proposé cette lettre.")
            continue
        lettres_utilisees.add(lettre)
        if lettre in mot_secret:
            for i, c in enumerate(mot_secret):
                if c == lettre:
                    masque[i] = lettre
            print("Bonne lettre !")
        else:
            erreurs += 1
            print(f"Mauvaise lettre ! Il vous reste {essais_max - erreurs} tentatives.")
    gagne = "_" not in masque
    return gagne, erreurs, "".join(masque), list(lettres_utilisees)

def jouer_partie_multijoueur(joueur1, joueur2):
    print("\n=== Nouveau tour ===")
    mot_secret = choisir_mot_joueur1()
    print("\n" * 50)  # clear screen simple
    print("Joueur 2, c'est à vous de jouer !")
    gagne, erreurs, mot_trouve, lettres_utilisees = tour_devinette(mot_secret, 8)
    if gagne:
        print(f"\nBravo Joueur 2 ! Vous avez trouvé le mot : {mot_secret}")
        ajouter_statistique(joueur2, True, 8 - erreurs, mot_secret, lettres_utilisees)
        # optional: give point to player1 for choosing a good word?
        ajouter_statistique(joueur1, True, 8 - erreurs, mot_secret, lettres_utilisees)  # maybe not
    else:
        print(f"\nDommage ! Le mot était : {mot_secret}")
        ajouter_statistique(joueur2, False, 8 - erreurs, mot_secret, lettres_utilisees)
        ajouter_statistique(joueur1, False, 8 - erreurs, mot_secret, lettres_utilisees)
    # Ask to replay
    while True:
        rejouer = input("\nVoulez-vous faire une autre partie ? (o/n) : ").strip().lower()
        if rejouer in ("o", "n"):
            break
    return rejouer == "o"

def choisir_joueur(nom):
    """Return player dict by name, create if not exists."""
    for j in joueurs["joueurs"]:
        if j["identifiant"] == nom:
            return j
    nouveau = {"identifiant": nom, "streak": 0, "historique": []}
    joueurs["joueurs"].append(nouveau)
    with open(BASE_DIR / "bdd.json", "w", encoding="utf-8") as f:
        json.dump(joueurs, f, indent=4, ensure_ascii=False)
    return nouveau
