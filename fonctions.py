import random as r
import json 

class fonctions():
    def __init__(self):
        pass

mots=[]
joueurs=[]

with open("mots.json") as file: 
    mots=json.load(file)
file.close()

with open("bdd.json") as file: 
    joueurs=json.load(file)
file.close()

def login():
    identifiant=input("Quel est ton identifiant ? \n")
    for i in joueurs["joueurs"]:
        if i["identifiant"]==identifiant:
            print(f"Bienvenue {identifiant} !")
            return i
    else:
        print(f"Ton identifiant n'existe pas, on va le créer !")
        new_joueur={"identifiant":identifiant,"streak":0,"historique":[]}
        joueurs["joueurs"].append(new_joueur)
        with open("bdd.json", "w") as file:
            json.dump(joueurs, file, indent=4)
        file.close()
        return new_joueur

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



def partie(mot_choice, mot_inconnu, tentatives, lettres_use):
        
        print(affiche_mot(mot_inconnu))

        lettre=devine_lettre(tentatives)

        if lettre in lettres_use:
            print(f"Tu as déjà utilisé cette lettre : {lettre}")
            print(f"Voici les lettres que tu as déjà utilisé : {lettres_use}")
            return partie(mot_choice,mot_inconnu,tentatives,lettres_use)
        else:
            lettres_use.append(lettre)
            print(f"Voici les lettres que tu as déjà utilisé : {lettres_use}")

        if lettre in mot_choice:
            positions=find_key(mot_choice,lettre)

            for j in positions:
                mot_inconnu[j]=lettre

        else:
            tentatives=tentatives-1
            print(f"Domage :( il te reste {tentatives} tentatives")


        if not "_" in mot_inconnu:
            return (True,tentatives, mot_inconnu, lettres_use)
        elif tentatives == 0:
            
            return (False,tentatives,mot_inconnu,lettres_use)
        else:
            return partie(mot_choice,mot_inconnu,tentatives,lettres_use)

def add_statistic(joueur, win, tentatives_restantes, mot_choice, lettres_use):
    if win:
        joueur["streak"]+=1
        joueur["historique"].append({"mot":mot_choice,"win":True,"tentatives_restantes":tentatives_restantes,"lettres_use":lettres_use})
    else:
        joueur["streak"]=0
        joueur["historique"].append({"mot":mot_choice,"win":False,"tentatives_restantes":tentatives_restantes,"lettres_use":lettres_use})

    with open("bdd.json", "w") as file:
        json.dump(joueurs, file, indent=4)
    file.close()

def jeu(cheat_mode, essais, joueur):

    lettres=[5,6,7,8,9,10,12]
    nombre_lettres=r.choice(lettres)

    mot_choice=r.choice(mots[str(nombre_lettres)])

    mot_inconnu=["_" for i in range(nombre_lettres)]


    # Première lettre :
    mot_inconnu[0]=mot_choice[0]

    if cheat_mode:
        print(mot_inconnu, mot_choice)
    
    win,tentatives,mot_inconnu,lettres_use=partie(mot_choice,mot_inconnu,essais,[])

    add_statistic(joueur, win, tentatives, mot_choice, lettres_use)

    if win:
        print(f"Le mot était bien : {affiche_mot(mot_inconnu)}")
        print(f"il te restait : {tentatives} tentatives")
        print(f"Félicitation tu as gagné !!")

        print("Comme tu es très fort veux tu rejouer ?")

        rejouer(cheat_mode, joueur)

    else:
        print("Mince tu as perdu :(")
        print(f"Le mot était : {mot_choice}")
        print(f"il te restait : {tentatives} tentatives")


        print("Veux tu rejouer tu peux t'améliorer ?")

        anwser=input("Y : oui N : non \n")
    
        rejouer(cheat_mode, joueur)

def rejouer(cheat_mode, joueur):
    anwser=input("Y : oui N : non \n")
    
    while anwser.strip().lower() != "y" and anwser.strip().lower() != "n":
        anwser=input("Y : oui N : non \n")

    if anwser.strip().lower()=="y":
        print("Super on recommence !")
        
        jeu(cheat_mode, joueur)
    else:
        print("Merci d'avoir joué !")
        