import random as r
import json 

class fonctions():
    def __init__(self):
        pass

mots=[]

with open("mots.json") as file: 
    list_mots=json.load(file)
    mots=list_mots
file.close()


def affiche_mot(list):
    mot=""
    for i in list:
        mot=mot+f"{i} "
    return mot

def valide_lettre(lettre):
    LETTRES = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
           "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
    saisie=lettre.strip().lower() # ici strip permet d'enlever les espaces et lower mettre en minuscule 
    if lettre.strip().lower() in LETTRES:
        return (True,lettre.strip().lower())
    else:
        print(f"Votre entrée '{lettre}' n'est pas valide !!")
        return (False,lettre.strip().lower())

def devine_lettre(tentatives_restantes):
    lettre_joueur=input(f"Essaye de deviner une lettre ({tentatives_restantes} tentative(s) restante) : ")
    is_valid=valide_lettre(lettre_joueur)
    if is_valid[0]:
        return is_valid[1]
    else:
        return devine_lettre(tentatives_restantes)

def find_key(mot, lettre):
    keys=[]
    for i in range(len(mot)):
        if mot[i] == lettre:
            keys.append(i)
    return keys 



def partie(mot_choice, mot_inconnu, tentatives):
        tentatives_restantes=tentatives
        
        print(affiche_mot(mot_inconnu))

        lettre=devine_lettre(tentatives_restantes)

        if lettre in mot_choice:
            positions=find_key(mot_choice,lettre)

            for j in positions:
                mot_inconnu[j]=lettre

        else:
            tentatives_restantes=tentatives_restantes-1
            print(f"Domage :( il te reste {tentatives_restantes} tentatives")


        if not "_" in mot_inconnu:
            return (True,tentatives_restantes, mot_inconnu)
        elif tentatives_restantes == 0:
            
            return False,tentatives_restantes,mot_inconnu
        else:
            return partie(mot_choice,mot_inconnu,tentatives_restantes)


def jeu(cheat_mode):

    lettres=[5,6,7,8,9,10,12]
    nombre_lettres=r.choice(lettres)

    mot_choice=r.choice(mots[str(nombre_lettres)])

    mot_inconnu=["_" for i in range(nombre_lettres)]

    lettres_use=[]

    # Première lettre :
    mot_inconnu[0]=mot_choice[0]

    if cheat_mode:
        print(mot_inconnu, mot_choice)
    
    win,tentatives,mot_inconnu=partie(mot_choice,mot_inconnu,8)

    if win:
        print(f"Le mot était bien : {affiche_mot(mot_inconnu)}")
        print(f"il te restait : {tentatives} tentatives")
        print(f"Félicitation tu as gagné !!")

        print("Comme tu es très for veux tu rejouer ?")

        rejouer(cheat_mode)

    else:
        print("Mince tu as perdu :(")
        print(f"Le mot était : {mot_choice}")
        print(f"il te restait : {tentatives} tentatives")


        print("Veux tu rejouer tu peux t'améliorer ?")

        anwser=input("Y : oui N : non")
    
        rejouer(cheat_mode)

def rejouer(cheat_mode):
    anwser=input("Y : oui N : non \n")
    
    while anwser.strip().lower() != "y" and anwser.strip().lower() != "n":
        anwser=input("Y : oui N : non")

    if anwser.strip().lower()=="y":
        print("Super on recommence !")
        
        jeu(cheat_mode)
    else:
        print("Merci d'avoir joué !")
        