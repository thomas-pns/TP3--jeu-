import json
import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

import fonctions as f


class JeuPendu:
	def __init__(self, root, joueur):
		self.root = root
		self.joueur = joueur
		self.essais_max = 8
		self.images = []
		self.image_actuelle = None
		self.mot = ""
		self.mot_cache = []
		self.lettres_utilisees = []
		self.erreurs = 0
		self.partie_terminee = False

		root.title("Le pendu")
		root.geometry("760x500")
		root.minsize(620, 440)

		cadre = ttk.Frame(root, padding=24)
		cadre.pack(fill="both", expand=True)
		ttk.Label(cadre, text="LE PENDU", font=("Segoe UI", 22, "bold")).pack(anchor="w")
		ttk.Label(cadre, text=f"Joueur : {joueur['identifiant']}").pack(anchor="w", pady=(0, 18))

		zone_jeu = ttk.Frame(cadre)
		zone_jeu.pack(fill="both", expand=True)

		self.canvas = tk.Canvas(zone_jeu, width=360, height=290, bg="white", highlightthickness=1)
		self.canvas.pack(side="left", fill="both", expand=True, padx=(0, 24))

		panneau = ttk.Frame(zone_jeu, width=240)
		panneau.pack(side="left", fill="y")
		panneau.pack_propagate(False)
		ttk.Label(panneau, text="Mot à trouver").pack(anchor="w")
		self.mot_label = ttk.Label(panneau, text="", font=("Consolas", 20, "bold"))
		self.mot_label.pack(anchor="w", pady=(4, 18))
		self.essais_label = ttk.Label(panneau, text="")
		self.essais_label.pack(anchor="w", pady=(0, 18))

		ttk.Label(panneau, text="Votre lettre").pack(anchor="w")
		self.saisie = ttk.Entry(panneau, font=("Segoe UI", 14), justify="center")
		self.saisie.pack(fill="x", pady=(5, 8))
		self.saisie.bind("<Return>", self.proposer)
		self.bouton = ttk.Button(panneau, text="Proposer", command=self.proposer)
		self.bouton.pack(fill="x")
		self.message = ttk.Label(panneau, text="", wraplength=230)
		self.message.pack(anchor="w", pady=(18, 0))

		self.charger_images()
		self.nouvelle_partie()

	def charger_images(self):
		dossier_images = Path(__file__).resolve().parent / "images PENDU-20260929"
		for numero in range(1, self.essais_max + 1):
			chemin = dossier_images / f"bonhomme{numero}.gif"
			try:
				self.images.append(tk.PhotoImage(file=str(chemin)))
			except tk.TclError:
				self.images.append(None)

	def afficher_pendu(self):
		self.canvas.delete("all")
		if self.erreurs == 0:
			self.canvas.create_text(180, 145, text="Le dessin apparaîtra ici", fill="#666666")
			return

		image = self.images[self.erreurs - 1]
		if image is not None:
			self.image_actuelle = image
			self.canvas.create_image(180, 145, image=image)
		else:
			self.canvas.create_text(180, 145, text=f"Erreurs : {self.erreurs}", fill="#9b2c2c")

	def nouvelle_partie(self):
		longueurs = list(f.mots.keys())
		longueur = random.choice(longueurs)
		self.mot = random.choice(f.mots[longueur])
		self.mot_cache = ["_" for _ in self.mot]
		self.mot_cache[0] = self.mot[0]
		self.lettres_utilisees = []
		self.erreurs = 0
		self.partie_terminee = False
		self.message.config(text="")
		self.saisie.config(state="normal")
		self.saisie.delete(0, tk.END)
		self.bouton.config(text="Proposer")
		self.actualiser_affichage()
		self.saisie.focus_set()

	def actualiser_affichage(self):
		self.mot_label.config(text=f.affiche_mot(self.mot_cache))
		restantes = self.essais_max - self.erreurs
		self.essais_label.config(text=f"Coups restants : {restantes}")
		self.afficher_pendu()

	def proposer(self, _event=None):
		del _event
		if self.partie_terminee:
			self.nouvelle_partie()
			return

		lettre = self.saisie.get().strip().lower()
		self.saisie.delete(0, tk.END)
		if len(lettre) != 1 or not lettre.isascii() or not lettre.isalpha():
			self.message.config(text="Saisissez une seule lettre de l’alphabet.")
			return
		if lettre in self.lettres_utilisees:
			self.message.config(text=f"Vous avez déjà proposé la lettre {lettre}.")
			return

		self.lettres_utilisees.append(lettre)
		if lettre in self.mot:
			for position, caractere in enumerate(self.mot):
				if caractere == lettre:
					self.mot_cache[position] = lettre
		else:
			self.erreurs += 1

		self.actualiser_affichage()
		if "_" not in self.mot_cache:
			self.terminer_partie(True)
		elif self.erreurs == self.essais_max:
			self.terminer_partie(False)
		else:
			self.message.config(text=f"Lettres utilisées : {', '.join(self.lettres_utilisees)}")

	def terminer_partie(self, victoire):
		restantes = self.essais_max - self.erreurs
		f.add_statistic(self.joueur, victoire, restantes, self.mot, self.lettres_utilisees)
		self.partie_terminee = True
		self.saisie.config(state="disabled")
		self.bouton.config(text="Nouvelle partie")
		if victoire:
			self.message.config(text=f"Bravo, vous avez trouvé « {self.mot} » !")
		else:
			self.message.config(text=f"Partie terminée. Le mot était « {self.mot} ».")


def choisir_joueur(root):
	while True:
		identifiant = simpledialog.askstring("Le pendu", "Quel est votre identifiant ?", parent=root)
		if identifiant is None:
			return None
		identifiant = identifiant.strip()
		if identifiant:
			break
		messagebox.showwarning("Identifiant requis", "Veuillez saisir un identifiant.", parent=root)

	for joueur in f.joueurs["joueurs"]:
		if joueur["identifiant"] == identifiant:
			return joueur

	joueur = {"identifiant": identifiant, "streak": 0, "historique": []}
	f.joueurs["joueurs"].append(joueur)
	chemin_bdd = Path(__file__).resolve().parent / "bdd.json"
	with chemin_bdd.open("w", encoding="utf-8") as fichier:
		json.dump(f.joueurs, fichier, indent=4, ensure_ascii=False)
	return joueur


def main():
	root = tk.Tk()
	root.withdraw()
	joueur = choisir_joueur(root)
	if joueur is None:
		root.destroy()
		return
	root.deiconify()
	JeuPendu(root, joueur)
	root.mainloop()


if __name__ == "__main__":
	main()
