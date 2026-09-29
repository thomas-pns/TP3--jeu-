export const CHARACTER_LIST = [
    { id: "pirate", name: "Capitaine Moustache", unlock: 0, title: "Pirate grincheux", colors: ["#f2b68b", "#7555bf", "#ffd06f", "#382851"] },
    { id: "chef", name: "Chef Patatras", unlock: 2, title: "Cuisinier catastrophe", colors: ["#e9a878", "#e96e7d", "#ffe2a6", "#4a304a"] },
    { id: "mummy", name: "Momie Biscotte", unlock: 3, title: "Momie très polie", colors: ["#e6c996", "#b8a77f", "#fff0cf", "#514a40"] },
    { id: "astronaut", name: "Astro-Biscuit", unlock: 5, title: "Astronaute rêveur", colors: ["#b7def0", "#6485e8", "#7ee7db", "#2b345c"] },
    { id: "robot", name: "Bip le robot", unlock: 7, title: "Robot premier degré", colors: ["#b1c9d6", "#5b8faa", "#7ee7db", "#34485c"] },
    { id: "knight", name: "Sir Gribouille", unlock: 10, title: "Chevalier distrait", colors: ["#e8b58f", "#657291", "#ffc970", "#394159"] },
];

const LINES = {
    pirate: {
        idle: ["À l’abordage du dictionnaire !", "Mon perroquet connaît peut-être la réponse.", "J’ai caché la carte au trésor. Oups.", "Le mot est dans la cale, moussaillon !", "Prêt·e ? Je hisse la grand-voile !"],
        good: ["Par les sept voyelles, bien joué !", "Tu as le compas dans l’œil !", "Un coup de sabre… sur la bonne lettre !", "Mon perroquet applaudit. Enfin, il crie.", "À ce rythme, tu pilles le dictionnaire !"],
        wrong: ["Aïe, ça pique plus qu’un perroquet.", "Pas mon crochet ! Il est tout neuf !", "Mille sabords, c’était pas celle-là.", "J’ai entendu un « plouf » dans la cale.", "Mon chapeau a pris un courant d’air !"],
        panic: ["Terre en vue ? Non, c’est juste la sueur.", "Mon perroquet vient de démissionner !", "Je négocie avec le dictionnaire !", "Moussaillon, c’est la dernière vague !", "Je n’ai pas peur. C’est le bateau qui tremble."],
        victory: ["Le trésor est à toi, capitaine !", "On fête ça avec du jus de perroquet !", "Victoire ! Le dictionnaire a marché sur la planche !", "Cap sur le prochain mot !", "Un butin pareil mérite une danse pirate !"],
        defeat: ["Le mot s’est enfui dans la cale !", "On remonte l’ancre et on retente ?", "Ce fichu mot avait le pied marin.", "Le dictionnaire a gagné… pour cette manche.", "Je réclame une revanche, moussaillon !"],
    },
    chef: {
        idle: ["Bienvenue dans ma cuisine… range les couteaux !", "Aujourd’hui, le mot est à point.", "La recette du succès ? Une bonne voyelle.", "J’ai mis le dictionnaire au four. Mauvaise idée.", "À vos marques, prêts, mijotez !"],
        good: ["Une lettre cuite à la perfection !", "Bravo, c’est du grand chef !", "Tu as trouvé le bon ingrédient.", "Ça, c’est une réponse cinq étoiles !", "Le mot prend forme, quelle recette !"],
        wrong: ["Oups, j’ai fait tomber une casserole !", "Aïe, ça brûle plus qu’un soufflé raté.", "J’ai confondu sel et alphabet.", "La lettre est un peu trop grillée.", "Pas ce bras ! Il tient la louche !"],
        panic: ["Le minuteur sonne, chef !", "Ça chauffe, même le four transpire.", "Dernière chance : ajoute une voyelle !", "Mon soufflé retombe… et moi aussi.", "Je sors la recette de secours !"],
        victory: ["Service gagnant, à table !", "Ce mot est parfaitement assaisonné.", "Une victoire bien gratinée !", "Chef-d’œuvre servi avec panache !", "La prochaine manche est pour la maison !"],
        defeat: ["Le mot a brûlé au fond de la poêle.", "On remet les ingrédients et on recommence ?", "Cette recette manquait d’une lettre.", "Le dictionnaire m’a piqué ma spatule.", "Pas grave : la revanche est au menu !"],
    },
    mummy: {
        idle: ["Je suis momifiée… mais très motivée.", "Déroulons ce mystère ensemble !", "J’ai perdu le fil. Littéralement.", "Mon sarcophage dit que tu vas gagner.", "Le mot est quelque part sous ces bandelettes."],
        good: ["Une lettre bien déroulée !", "Excellent, je note ça sur mon papyrus.", "Tu as déchiffré un hiéroglyphe !", "La momie approuve d’un petit hochement.", "On déroule la victoire, bravo !"],
        wrong: ["Aïe, ma bandelette s’est emmêlée !", "Pas celle-là, elle tenait mon coude.", "Je perds le fil… encore.", "Mon sarcophage vient de faire « pouf ».", "Ouille, c’était ma bandelette préférée !"],
        panic: ["Je transpire sous trois mille ans de lin !", "Dernière chance, déroulement express !", "Mon papyrus indique : panique un peu.", "Je vais manquer de bandelettes… et de temps !", "Même les pharaons retiennent leur souffle."],
        victory: ["Victoire gravée dans le papyrus !", "La momie fait une danse millénaire !", "On a déroulé le mystère jusqu’au bout.", "Le pharaon offre une pyramide de bonbons !", "À la prochaine manche, mortel·le… façon de parler !"],
        defeat: ["Le mot est reparti sous le sable.", "J’avais pourtant bien déroulé la carte.", "Le sphinx connaît la réponse, lui.", "Une manche perdue, pas une dynastie !", "Je réclame une revanche de l’au-delà du canapé."],
    },
    astronaut: {
        idle: ["Houston, on a un mot à trouver.", "Prêt·e au décollage alphabétique ?", "Mon casque fait un drôle d’écho.", "J’ai cartographié trois galaxies de lettres.", "Cap sur la constellation des voyelles !"],
        good: ["Quelle découverte intergalactique !", "Lettre confirmée par le centre spatial !", "Tu as une intuition en orbite.", "Cette réponse mérite une pluie d’étoiles !", "On vient de franchir la bonne orbite !"],
        wrong: ["Oups, turbulences dans le module !", "Pas mon gant spatial !", "Cette lettre a raté la station.", "Houston, j’ai perdu un bouton… encore.", "Aïe, micro-météorite sur le casque !"],
        panic: ["Alerte rouge, mais très décorative !", "Plus qu’une chance avant la rentrée !", "Mon casque s’embue. C’est l’émotion.", "Houston, préparez le plan B !", "Les étoiles me regardent, quelle pression."],
        victory: ["Victoire en orbite, équipage !", "On plante le drapeau sur ce mot !", "Un petit pas pour toi, un grand mot trouvé.", "Feux d’artifice en apesanteur !", "Destination : la prochaine manche !"],
        defeat: ["Le mot a filé dans une autre galaxie.", "On remet les moteurs et on redécolle ?", "Mission reportée, équipage.", "Même les fusées ont parfois le mal de mot.", "La prochaine orbite sera la bonne !"],
    },
    robot: {
        idle: ["Bip. Mode devin activé.", "Analyse du dictionnaire… trop de mots.", "Je suis prêt. Probabilité de victoire : élevée.", "Veuillez insérer une lettre sympathique.", "Mes circuits frétillent d’impatience."],
        good: ["Bip-bip ! Calcul parfaitement effectué.", "Lettre correcte. Petit robot content.", "Analyse confirmée à 100,0 %.", "Tu viens de battre mon meilleur processeur !", "Succès ! Je sauvegarde cette émotion."],
        wrong: ["Erreur 404 : bras introuvable.", "Aïe. Mon coude demande une mise à jour.", "Cette lettre a fait planter mon grille-pain.", "Bip… je fais semblant que c’était prévu.", "Vis perdue. Quelqu’un a une clé ?"],
        panic: ["Alerte : sueur non compatible avec mon système.", "Dernière tentative détectée. Courage humain.", "Mes ventilateurs tournent à fond !", "Bip-bip-bip : stress en cours.", "Redémarrage émotionnel imminent."],
        victory: ["Victoire enregistrée. Joie.exe lancé !", "Je lance la danse des circuits !", "Mission accomplie, humain·e.", "Niveau de bonheur : beaucoup trop élevé.", "Prochaine manche chargée en mémoire !"],
        defeat: ["Mot introuvable. Je vais redémarrer.", "Échec… mais échec très élégant.", "On relance le programme ?", "Je sauvegarde ma revanche dans le cloud.", "Bip. La prochaine sera la bonne."],
    },
    knight: {
        idle: ["Par le royaume des consonnes, en garde !", "Mon armure est prête. Mon cheval aussi.", "Cette quête sent la voyelle héroïque.", "Je cherche ma carte… sous mon casque.", "Que le meilleur mot l’emporte !"],
        good: ["Parfaitement trouvé, noble devineur !", "La lettre a rejoint la table ronde.", "Quelle bravoure alphabétique !", "Le royaume applaudit ta trouvaille !", "Tu as touché la cible du premier coup !"],
        wrong: ["Ma visière vient de se retourner !", "Aïe, mon armure avait une bosse.", "Pas mon épée… c’est une spatule.", "La lettre a esquivé mon bouclier.", "Mon cheval vient de pouffer."],
        panic: ["Dernière chance avant le tournoi !", "Même mon cheval retient son souffle.", "Le royaume compte sur toi !", "Mon heaume se met à chauffer.", "À l’aide, mon armure fait du bruit !"],
        victory: ["Gloire au royaume des mots !", "Une victoire digne d’une ballade !", "Le dragon du dictionnaire est vaincu !", "Je salue ta bravoure, champion·ne !", "En selle pour la prochaine manche !"],
        defeat: ["Le mot s’est caché dans le donjon.", "Mon cheval demande une revanche.", "La quête continue, noble ami·e.", "Le dragon garde encore un secret.", "Reprenons nos forces et repartons !"],
    },
};

const ACCESSORIES = {
    pirate: `<path d="M103 77 Q112 35 151 34 Q192 35 201 77 Q155 66 103 77Z" fill="#392442" stroke="#291c3d" stroke-width="5"/><path d="M109 75 Q151 64 196 75 L205 85 Q154 77 101 86Z" fill="#ffd06f" stroke="#392442" stroke-width="4"/><circle cx="151" cy="50" r="7" fill="#fff2c6"/>`,
    chef: `<path d="M115 60 C95 36 117 21 132 34 C133 8 169 9 171 34 C190 20 209 39 190 62Z" fill="#fff7e8" stroke="#c2bfd8" stroke-width="4"/><path d="M115 59H190V70H115Z" fill="#e96e7d"/>`,
    mummy: `<path d="M114 48 Q151 27 190 49 M108 61 Q151 40 196 62 M108 85 Q151 65 195 87" fill="none" stroke="#fff0cf" stroke-width="8" stroke-linecap="round"/><path d="M111 74 Q151 55 191 76" fill="none" stroke="#c2ad82" stroke-width="3"/>`,
    astronaut: `<circle cx="151" cy="72" r="49" fill="rgba(149,228,246,.18)" stroke="#e3f6ff" stroke-width="5"/><path d="M111 57 Q151 36 189 57" fill="none" stroke="#fff" stroke-opacity=".7" stroke-width="4"/>`,
    robot: `<path d="M151 41V25" stroke="#7ee7db" stroke-width="5" stroke-linecap="round"/><circle cx="151" cy="20" r="8" fill="#ff8aa8"/><path d="M111 51 Q151 31 191 51 L187 69H115Z" fill="#527b9e" stroke="#34485c" stroke-width="4"/>`,
    knight: `<path d="M110 69 Q108 31 151 28 Q194 31 192 69 L178 62 Q151 49 124 63Z" fill="#8492b0" stroke="#394159" stroke-width="5"/><path d="M149 31 Q170 4 179 18 Q178 32 158 44Z" fill="#ffc970" stroke="#806342" stroke-width="3"/><path d="M119 68H184" stroke="#d4e4f1" stroke-width="6"/>`,
};

function partClasses(part, errors, threshold, stageError) {
    const lost = errors >= threshold;
    const flying = errors === threshold && stageError;
    return `c-part ${part}${lost ? " is-lost" : ""}${flying ? " is-flying" : ""}`;
}

export function characterSvg(id = "pirate", options = {}) {
    const character = CHARACTER_LIST.find((item) => item.id === id) || CHARACTER_LIST[0];
    const [skin, main, accent, dark] = character.colors;
    const errors = Math.max(0, Math.min(8, Number(options.errors) || 0));
    const mood = options.mood || "idle";
    const withGallows = Boolean(options.withGallows);
    const stageError = Boolean(options.stageError);
    const expression = mood === "good" || mood === "victory"
        ? `<path d="M132 103 Q151 119 170 103" fill="none" stroke="${dark}" stroke-width="5" stroke-linecap="round"/>`
        : mood === "wrong" || mood === "panic"
            ? `<ellipse cx="137" cy="91" rx="5" ry="9" fill="${dark}"/><ellipse cx="165" cy="91" rx="5" ry="9" fill="${dark}"/><ellipse cx="151" cy="111" rx="8" ry="6" fill="${dark}"/>`
            : `<path d="M136 106 Q151 115 166 106" fill="none" stroke="${dark}" stroke-width="4" stroke-linecap="round"/>`;
    const eyes = mood === "wrong" || mood === "panic"
        ? `<circle cx="137" cy="92" r="7" fill="#fff"/><circle cx="165" cy="92" r="7" fill="#fff"/><circle cx="138" cy="93" r="3.5" fill="${dark}"/><circle cx="164" cy="93" r="3.5" fill="${dark}"/>`
        : `<ellipse cx="138" cy="94" rx="4" ry="6" fill="${dark}"/><ellipse cx="164" cy="94" rx="4" ry="6" fill="${dark}"/>`;
    const gallows = withGallows ? `
        <g class="hangman-rope" fill="none" stroke="#c9c2ed" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M40 252H112M65 252V36H153V51"/>
            <path d="M142 51 Q151 61 160 51" stroke-width="4"/>
        </g>` : "";
    const headAccessory = ACCESSORIES[character.id];
    const bodyDetail = character.id === "pirate"
        ? `<path d="M135 157 Q151 146 167 157" fill="none" stroke="#f7e2b8" stroke-width="5"/><path d="M160 94L171 98L160 103Z" fill="${dark}"/>`
        : character.id === "chef"
            ? `<path d="M137 109 Q151 101 165 109" fill="none" stroke="#49313b" stroke-width="7" stroke-linecap="round"/><path d="M151 158V216" stroke="#ffe2a6" stroke-width="6"/>`
            : character.id === "mummy"
                ? `<path d="M121 150L181 183M119 178L181 148M125 204L175 177" fill="none" stroke="#fff0cf" stroke-width="7" stroke-linecap="round"/><path d="M121 151L181 184M119 179L181 149" fill="none" stroke="#b8a77f" stroke-width="2"/>`
                : character.id === "astronaut"
                    ? `<path d="M126 159H176V207H126Z" fill="#5477d7" stroke="#d7efff" stroke-width="4"/><path d="M139 177H164" stroke="#7ee7db" stroke-width="5" stroke-linecap="round"/>`
                    : character.id === "robot"
                        ? `<rect x="131" y="149" width="40" height="55" rx="12" fill="#5b8faa" stroke="#34485c" stroke-width="4"/><circle cx="151" cy="171" r="7" fill="#7ee7db"/><path d="M140 190H162" stroke="#34485c" stroke-width="4" stroke-linecap="round"/>`
                        : `<path d="M124 153L151 166L178 153V205L151 219L124 205Z" fill="#657291" stroke="#394159" stroke-width="4"/><path d="M151 167V216M127 185H175" stroke="#ffc970" stroke-width="5"/>`;
    const sweat = mood === "panic" ? `<path class="sweat-drop" d="M199 89 Q190 103 199 109 Q208 103 199 89Z" fill="#7ee7db"/>` : "";
    const escape = errors >= 8
        ? `<g class="escape-cloud" opacity="0"><circle cx="112" cy="195" r="19" fill="#fff7e8"/><circle cx="136" cy="183" r="25" fill="#fff7e8"/><circle cx="162" cy="192" r="21" fill="#fff7e8"/><circle cx="183" cy="203" r="15" fill="#fff7e8"/><path d="M123 198l6 5 10-14M160 203l6 4 9-12" fill="none" stroke="#a68bff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><text x="150" y="241" text-anchor="middle" fill="#f2eaff" font-size="13" font-weight="800">POUF !</text></g>`
        : "";

    return `<svg class="character-svg" viewBox="0 0 300 280" role="img" aria-label="${character.name}, étape ${errors} sur 8" xmlns="http://www.w3.org/2000/svg">
        <defs><filter id="char-shadow-${character.id}" x="-40%" y="-30%" width="180%" height="180%"><feDropShadow dx="0" dy="5" stdDeviation="5" flood-color="#080817" flood-opacity=".3"/></filter></defs>
        ${gallows}
        <g class="character-person hangman-person-parts" filter="url(#char-shadow-${character.id})">
            <g class="${partClasses("c-left-leg", errors, 6, stageError)}"><path d="M137 203L127 244Q126 252 134 253L145 252L153 210Z" fill="${main}" stroke="${dark}" stroke-width="5" stroke-linejoin="round"/><path d="M128 245Q119 250 125 258H149Q154 251 144 247" fill="${accent}" stroke="${dark}" stroke-width="4"/></g>
            <g class="${partClasses("c-right-leg", errors, 7, stageError)}"><path d="M158 207L164 247Q163 254 173 253L183 248L169 199Z" fill="${main}" stroke="${dark}" stroke-width="5" stroke-linejoin="round"/><path d="M164 247Q157 254 164 260H188Q192 253 179 248" fill="${accent}" stroke="${dark}" stroke-width="4"/></g>
            <g class="${partClasses("c-body", errors, 3, stageError)}"><path d="M123 143Q151 127 179 143L184 203Q151 220 118 203Z" fill="${main}" stroke="${dark}" stroke-width="6" stroke-linejoin="round"/>${bodyDetail}<path d="M117 149Q107 164 114 183L128 178L132 151Z" fill="${accent}" stroke="${dark}" stroke-width="4"/></g>
            <g class="${partClasses("c-left-arm", errors, 4, stageError)}"><path d="M121 151Q103 157 91 179L103 188Q120 177 134 168Z" fill="${main}" stroke="${dark}" stroke-width="5" stroke-linejoin="round"/><circle cx="97" cy="184" r="9" fill="${skin}" stroke="${dark}" stroke-width="4"/></g>
            <g class="${partClasses("c-right-arm", errors, 5, stageError)}"><path d="M177 151Q195 158 206 180L194 190Q179 177 165 168Z" fill="${main}" stroke="${dark}" stroke-width="5" stroke-linejoin="round"/><circle cx="201" cy="185" r="9" fill="${skin}" stroke="${dark}" stroke-width="4"/></g>
            <g class="${partClasses("c-head", errors, 2, stageError)}">
                ${character.id === "astronaut" ? "" : `<circle cx="151" cy="91" r="35" fill="${skin}" stroke="${dark}" stroke-width="5"/>`}
                ${character.id === "robot" ? `<rect x="119" y="59" width="64" height="65" rx="19" fill="${skin}" stroke="${dark}" stroke-width="5"/>` : ""}
                ${headAccessory}
                ${eyes}${expression}
                <ellipse cx="124" cy="106" rx="6" ry="3" fill="#ff8aa8" opacity=".55"/><ellipse cx="178" cy="106" rx="6" ry="3" fill="#ff8aa8" opacity=".55"/>
                ${sweat}
            </g>
        </g>
        ${escape}
        <path d="M225 71l4 8 9 1-7 6 2 9-8-5-8 5 2-9-7-6 9-1Z" fill="${accent}" opacity=".85"/>
        <circle cx="80" cy="114" r="4" fill="${accent}" opacity=".8"/>
    </svg>`;
}

export function characterQuote(id = "pirate", situation = "idle") {
    const lines = LINES[id] || LINES.pirate;
    const variants = lines[situation] || lines.idle;
    return variants[Math.floor(Math.random() * variants.length)];
}
