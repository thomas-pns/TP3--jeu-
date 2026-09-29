const BOT_ART = {
    beginner: {
        colors: ["#ffc970", "#ef9278", "#614b61"],
        face: `<circle cx="32" cy="34" r="18" fill="#ffc970"/><path d="M24 34v2m16-2v2M27 43q5 6 10 0" stroke="#614b61" stroke-width="3" stroke-linecap="round"/>`,
        badge: "✦",
    },
    clever: {
        colors: ["#9c8ae8", "#ffc970", "#403652"],
        face: `<path d="M15 31q1-16 17-16t17 16v11q-1 9-17 10T15 42Z" fill="#9c8ae8"/><circle cx="25" cy="34" r="6" fill="none" stroke="#403652" stroke-width="3"/><circle cx="40" cy="34" r="6" fill="none" stroke="#403652" stroke-width="3"/><path d="M31 34h3m-10 11q7-6 14 0" stroke="#403652" stroke-width="3" stroke-linecap="round"/>`,
        badge: "⌁",
    },
    expert: {
        colors: ["#7ee7db", "#6673bd", "#35405e"],
        face: `<path d="M15 28q2-14 17-14t17 14v15q-2 11-17 11T15 43Z" fill="#7ee7db"/><path d="m11 20 21-11 21 11-21 10Z" fill="#6673bd" stroke="#35405e" stroke-width="3"/><path d="M21 36h5m12 0h5m-16 9q5 4 10 0" stroke="#35405e" stroke-width="3" stroke-linecap="round"/>`,
        badge: "π",
    },
    nightmare: {
        colors: ["#c78cff", "#fb718d", "#593b70"],
        face: `<path d="m16 25 6-13 8 8 9-8 9 14 1 17q-1 13-17 13T15 43Z" fill="#c78cff"/><path d="m22 34 8 3-7 4m19-7-8 3 7 4" fill="#fff0cf" stroke="#593b70" stroke-width="2" stroke-linejoin="round"/><path d="M27 48q5-5 10 0" stroke="#593b70" stroke-width="3" stroke-linecap="round"/>`,
        badge: "!",
    },
    boss: {
        colors: ["#ff8aa8", "#ffc970", "#51314e"],
        face: `<path d="M15 29q0-17 17-17t17 17v13q-1 14-17 14T15 42Z" fill="#ff8aa8"/><path d="m16 22 1-12 10 8 7-14 8 14 8-8 1 12Z" fill="#ffc970" stroke="#51314e" stroke-width="3" stroke-linejoin="round"/><circle cx="25" cy="36" r="3" fill="#51314e"/><circle cx="40" cy="36" r="3" fill="#51314e"/><path d="M26 47q6-6 12 0" fill="none" stroke="#51314e" stroke-width="3" stroke-linecap="round"/>`,
        badge: "♛",
    },
};

export function botAvatarSvg(botId = "beginner", compact = false) {
    const bot = BOT_ART[botId] || BOT_ART.beginner;
    const [primary, accent, outline] = bot.colors;
    const scale = compact ? 64 : 80;
    return `<svg viewBox="0 0 64 64" width="${scale}" height="${scale}" role="img" aria-label="Avatar ${botId}" xmlns="http://www.w3.org/2000/svg">
        <circle cx="32" cy="33" r="28" fill="${primary}" fill-opacity=".13"/>
        <path d="M13 49q2-13 19-13t19 13v7H13Z" fill="${accent}" stroke="${outline}" stroke-width="3" stroke-linejoin="round"/>
        ${bot.face}
        <circle cx="52" cy="15" r="8" fill="${accent}" stroke="${outline}" stroke-width="2"/>
        <text x="52" y="18" text-anchor="middle" font-size="8" font-weight="900" fill="${outline}">${bot.badge}</text>
    </svg>`;
}

