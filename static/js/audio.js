const STORAGE_KEY = "motus-maximus-muted";
const VOLUME_KEY = "motus-maximus-volume";

function readSetting(key) {
    try {
        return localStorage.getItem(key);
    } catch {
        return null;
    }
}

function saveSetting(key, value) {
    try {
        localStorage.setItem(key, value);
    } catch {
        // The sound controls still work for this page if storage is unavailable.
    }
}

class SoundBoard {
    constructor() {
        this.context = null;
        this.muted = readSetting(STORAGE_KEY) === "true";
        const storedVolume = readSetting(VOLUME_KEY);
        const savedVolume = storedVolume === null ? Number.NaN : Number(storedVolume);
        this.volume = Number.isFinite(savedVolume) && savedVolume >= 0 && savedVolume <= 1
            ? savedVolume
            : 0.55;
    }

    setMuted(muted) {
        this.muted = Boolean(muted);
        saveSetting(STORAGE_KEY, String(this.muted));
        return this.muted;
    }

    toggle() {
        if (this.muted && this.volume === 0) {
            this.setVolume(0.55);
            return false;
        }
        return this.setMuted(!this.muted);
    }

    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, Number(volume) || 0));
        saveSetting(VOLUME_KEY, String(this.volume));
        if (this.volume === 0) this.setMuted(true);
        else if (this.muted) this.setMuted(false);
        return this.volume;
    }

    async #audioContext() {
        if (this.muted) return null;
        const Context = window.AudioContext || window.webkitAudioContext;
        if (!Context) return null;
        if (!this.context) this.context = new Context();
        if (this.context.state === "suspended") await this.context.resume();
        return this.context;
    }

    async #tone(frequency, start, duration, type = "sine", volume = 0.12) {
        const context = await this.#audioContext();
        volume *= this.volume;
        if (!context || volume <= 0) return;
        const oscillator = context.createOscillator();
        const gain = context.createGain();
        oscillator.type = type;
        oscillator.frequency.setValueAtTime(frequency, context.currentTime + start);
        gain.gain.setValueAtTime(0.0001, context.currentTime + start);
        gain.gain.exponentialRampToValueAtTime(volume, context.currentTime + start + 0.018);
        gain.gain.exponentialRampToValueAtTime(0.0001, context.currentTime + start + duration);
        oscillator.connect(gain);
        gain.connect(context.destination);
        oscillator.start(context.currentTime + start);
        oscillator.stop(context.currentTime + start + duration + 0.03);
    }

    async play(kind) {
        if (this.muted || this.volume <= 0) return;
        const patterns = {
            key: [[520, 0, .07, "sine", .045]],
            good: [[540, 0, .12, "sine", .09], [760, .065, .16, "sine", .08]],
            wrong: [[190, 0, .12, "triangle", .09], [145, .07, .16, "triangle", .07]],
            hint: [[660, 0, .12, "sine", .06], [880, .08, .16, "sine", .07]],
            win: [[523, 0, .18, "sine", .08], [659, .12, .2, "sine", .08], [784, .25, .34, "sine", .09], [1046, .38, .4, "sine", .07]],
            lose: [[330, 0, .18, "triangle", .07], [262, .15, .2, "triangle", .06], [196, .31, .32, "sine", .05]],
            streak: [[660, 0, .12, "sine", .08], [880, .11, .14, "sine", .08], [1174, .23, .22, "sine", .08]],
        };
        for (const [frequency, start, duration, type, volume] of patterns[kind] || []) {
            this.#tone(frequency, start, duration, type, volume);
        }
    }
}

export const audio = new SoundBoard();
