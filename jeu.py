import fonctions as f


print(f"Bienvenue dans la version console du pendu !")

joueur=f.login()

print(f"On commence ?")

cheat_mode= False

f.jeu(cheat_mode, 8, joueur)