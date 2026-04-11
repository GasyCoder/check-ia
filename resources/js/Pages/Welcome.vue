<script setup>
/**
 * Welcome — ReinIA Command Center.
 *
 * Dual-flow workspace (Detect / Humanize) with an integrated input bar,
 * per-column progress (%, step labels, gradient bar), and a rich split-view
 * result layout (hero score, distribution, metrics, sentence highlights).
 */
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import axios from 'axios';
import AppLayout from '../Layouts/AppLayout.vue';
import { useToast } from '../Composables/useToast';

const toast = useToast();

// ─── State ──────────────────────────────────────────────────────────────────
const mode = ref('detect'); // 'detect' | 'humanize'
const intensity = ref('medium'); // 'light' | 'medium' | 'aggressive'

const text = ref('');
const analyzedText = ref('');       // frozen snapshot shown in result column
const detectionScore = ref(null);
const sentences = ref([]);
const humanizedText = ref('');
const humanizedAt = ref(null);

const loadingDetect = ref(false);
const loadingHumanize = ref(false);
const error = ref(null);
const hasRun = ref(false);

const copied = ref(false);
const shared = ref(false);
const textareaRef = ref(null);
const fileInputRef = ref(null);

const fileObj = ref(null);
const fileName = ref(null);
const fileSize = ref(0);

const maxChars = 50000;
const maxFileSize = 25 * 1024 * 1024; // 25 MB
const acceptedMime = [
    'text/plain',
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];

const intensityOptions = [
    { value: 'light', label: 'Light', hint: 'Subtle edits' },
    { value: 'medium', label: 'Medium', hint: 'Balanced rewrite' },
    { value: 'aggressive', label: 'Aggressive', hint: 'Deep rewrite' },
];

// ─── Progress state ─────────────────────────────────────────────────────────
const detectSteps = [
    { at: 0,  label: 'Préparation du texte…' },
    { at: 10, label: 'Nettoyage & normalisation' },
    { at: 22, label: 'Découpage en sections' },
    { at: 34, label: 'Traduction vers l\'anglais' },
    { at: 48, label: 'Analyse RoBERTa' },
    { at: 62, label: 'Calcul de la perplexité' },
    { at: 76, label: 'Analyse de la burstiness' },
    { at: 86, label: 'Agrégation des signaux' },
    { at: 93, label: 'Finalisation' },
];

const humanizeSteps = [
    { at: 0,  label: 'Chargement du modèle…' },
    { at: 14, label: 'Analyse du style source' },
    { at: 28, label: 'Segmentation en phrases' },
    { at: 42, label: 'Réécriture lexicale' },
    { at: 58, label: 'Variation syntaxique' },
    { at: 72, label: 'Rythme & burstiness' },
    { at: 84, label: 'Relecture finale' },
    { at: 92, label: 'Application de l\'intensité' },
];

const detectPercent = ref(0);
const detectStepIdx = ref(0);
const humanizePercent = ref(0);
const humanizeStepIdx = ref(0);

let detectTimer = null;
let humanizeTimer = null;

function startDetectProgress() {
    stopDetectProgress();
    detectPercent.value = 0;
    detectStepIdx.value = 0;
    detectTimer = setInterval(() => {
        const remaining = 92 - detectPercent.value;
        detectPercent.value = Math.min(92, detectPercent.value + Math.max(0.45, remaining * 0.024));
        while (
            detectStepIdx.value < detectSteps.length - 1 &&
            detectPercent.value >= detectSteps[detectStepIdx.value + 1].at
        ) {
            detectStepIdx.value += 1;
        }
    }, 220);
}

function stopDetectProgress(finished = false) {
    if (detectTimer) {
        clearInterval(detectTimer);
        detectTimer = null;
    }
    if (finished) {
        detectPercent.value = 100;
        detectStepIdx.value = detectSteps.length - 1;
    }
}

function startHumanizeProgress() {
    stopHumanizeProgress();
    humanizePercent.value = 0;
    humanizeStepIdx.value = 0;
    humanizeTimer = setInterval(() => {
        const remaining = 91 - humanizePercent.value;
        humanizePercent.value = Math.min(91, humanizePercent.value + Math.max(0.4, remaining * 0.02));
        while (
            humanizeStepIdx.value < humanizeSteps.length - 1 &&
            humanizePercent.value >= humanizeSteps[humanizeStepIdx.value + 1].at
        ) {
            humanizeStepIdx.value += 1;
        }
    }, 240);
}

function stopHumanizeProgress(finished = false) {
    if (humanizeTimer) {
        clearInterval(humanizeTimer);
        humanizeTimer = null;
    }
    if (finished) {
        humanizePercent.value = 100;
        humanizeStepIdx.value = humanizeSteps.length - 1;
    }
}

onBeforeUnmount(() => {
    stopDetectProgress();
    stopHumanizeProgress();
});

// ─── Derived ────────────────────────────────────────────────────────────────
const charCount = computed(() => text.value.length);
const trimmedLength = computed(() => text.value.trim().length);

const loading = computed(() => loadingDetect.value || loadingHumanize.value);

const hasFile = computed(() => !!fileObj.value);

const canRun = computed(() => {
    if (loading.value) return false;
    if (hasFile.value) return true;
    return trimmedLength.value >= 10 && charCount.value <= maxChars;
});

const showRightColumn = computed(
    () => mode.value === 'humanize' && (loadingHumanize.value || humanizedText.value)
);

const aiPercent = computed(() => (detectionScore.value !== null ? Math.max(0, Math.min(100, detectionScore.value)) : 0));
const humanPercent = computed(() => (detectionScore.value !== null ? Math.max(0, 100 - aiPercent.value) : 0));

const verdict = computed(() => {
    if (detectionScore.value === null) return null;
    const v = detectionScore.value;
    if (v >= 80) return {
        label: 'IA détectée',
        sub: 'Signal très fort de génération artificielle',
        dot: 'bg-rose-400',
        text: 'text-rose-300',
        ring: 'ring-rose-500/25',
        bar: 'from-rose-500 to-rose-400',
        glow: 'shadow-[0_0_40px_-12px_rgba(244,63,94,0.45)]',
    };
    if (v >= 60) return {
        label: 'Probablement IA',
        sub: 'Marqueurs typiques d\'un contenu généré',
        dot: 'bg-violet-400',
        text: 'text-violet-300',
        ring: 'ring-violet-500/25',
        bar: 'from-violet-500 to-violet-400',
        glow: 'shadow-[0_0_40px_-12px_rgba(139,92,246,0.4)]',
    };
    if (v >= 40) return {
        label: 'Résultat mixte',
        sub: 'Signaux partagés entre humain et IA',
        dot: 'bg-amber-400',
        text: 'text-amber-300',
        ring: 'ring-amber-500/25',
        bar: 'from-amber-500 to-amber-400',
        glow: 'shadow-[0_0_40px_-12px_rgba(245,158,11,0.35)]',
    };
    if (v >= 20) return {
        label: 'Probablement humain',
        sub: 'Style naturel, faibles marqueurs IA',
        dot: 'bg-emerald-400',
        text: 'text-emerald-300',
        ring: 'ring-emerald-500/25',
        bar: 'from-emerald-500 to-emerald-400',
        glow: 'shadow-[0_0_40px_-12px_rgba(16,185,129,0.35)]',
    };
    return {
        label: 'Écriture humaine',
        sub: 'Aucun marqueur IA significatif',
        dot: 'bg-emerald-400',
        text: 'text-emerald-300',
        ring: 'ring-emerald-500/25',
        bar: 'from-emerald-500 to-emerald-400',
        glow: 'shadow-[0_0_40px_-12px_rgba(16,185,129,0.4)]',
    };
});

const sourceMetrics = computed(() => {
    const t = analyzedText.value || text.value || '';
    const chars = t.length;
    const words = t.trim() ? t.trim().split(/\s+/).length : 0;
    const sent = sentences.value?.length || t.split(/[.!?]+/).filter((s) => s.trim().length > 0).length;
    const readingMin = Math.max(1, Math.round(words / 220));
    return { chars, words, sentences: sent, readingMin };
});

const humanizedMetrics = computed(() => {
    const t = humanizedText.value || '';
    const chars = t.length;
    const words = t.trim() ? t.trim().split(/\s+/).length : 0;
    const original = analyzedText.value || text.value || '';
    const deltaChars = chars - original.length;
    const deltaWords = words - (original.trim() ? original.trim().split(/\s+/).length : 0);
    return { chars, words, deltaChars, deltaWords };
});

const highlightedSentences = computed(() => {
    if (!Array.isArray(sentences.value) || sentences.value.length === 0) return null;
    return sentences.value.map((s, i) => {
        const score = Number(s.score) || 0;
        let tone = 'text-zinc-300';
        if (score >= 70) tone = 'bg-violet-500/10 text-violet-100 ring-1 ring-inset ring-violet-500/15';
        else if (score >= 45) tone = 'bg-amber-500/[0.06] text-amber-100/95 ring-1 ring-inset ring-amber-500/10';
        return {
            id: s.id ?? `s-${i}`,
            text: s.text || '',
            score,
            tone,
        };
    });
});

// ─── Helpers ────────────────────────────────────────────────────────────────
function normalizePercent(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return null;
    if (numeric >= 0 && numeric <= 1) return Math.round(numeric * 1000) / 10;
    return Math.max(0, Math.min(100, Math.round(numeric * 10) / 10));
}

function formatBytes(bytes) {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB'];
    let value = bytes;
    let unit = 0;
    while (value >= 1024 && unit < units.length - 1) {
        value /= 1024;
        unit += 1;
    }
    return `${value.toFixed(value >= 10 || unit === 0 ? 0 : 1)} ${units[unit]}`;
}

function fileExtLabel() {
    if (!fileName.value) return '';
    const dot = fileName.value.lastIndexOf('.');
    return dot >= 0 ? fileName.value.slice(dot + 1).toUpperCase() : 'FILE';
}

function formatNumber(value) {
    return Number(value || 0).toLocaleString();
}

function resetResults() {
    analyzedText.value = '';
    detectionScore.value = null;
    sentences.value = [];
    humanizedText.value = '';
    humanizedAt.value = null;
    error.value = null;
    hasRun.value = false;
}

function setMode(value) {
    if (mode.value === value) return;
    mode.value = value;
    error.value = null;
}

function autoGrow() {
    const el = textareaRef.value;
    if (!el) return;
    el.style.height = 'auto';
    const next = Math.min(480, Math.max(180, el.scrollHeight));
    el.style.height = `${next}px`;
}

watch(text, () => nextTick(autoGrow));

// ─── File attach ────────────────────────────────────────────────────────────
function openFilePicker() {
    if (loading.value) return;
    fileInputRef.value?.click();
}

function handleFileInput(event) {
    const file = event.target?.files?.[0];
    event.target.value = '';
    attachFile(file);
}

function attachFile(file) {
    if (!file) return;
    if (file.size > maxFileSize) {
        error.value = `Fichier trop volumineux (${(file.size / 1024 / 1024).toFixed(1)} Mo / 25 Mo max).`;
        toast.error(error.value);
        return;
    }
    const typeOk = acceptedMime.includes(file.type) || /\.(txt|pdf|docx)$/i.test(file.name);
    if (!typeOk) {
        error.value = 'Format non supporté. Utilisez .txt, .pdf ou .docx.';
        toast.error(error.value);
        return;
    }
    error.value = null;
    fileObj.value = file;
    fileName.value = file.name;
    fileSize.value = file.size;
}

function detachFile() {
    fileObj.value = null;
    fileName.value = null;
    fileSize.value = 0;
    if (fileInputRef.value) fileInputRef.value.value = '';
}

function handleDrop(event) {
    event.preventDefault();
    if (loading.value) return;
    const file = event.dataTransfer?.files?.[0];
    if (file) attachFile(file);
}

function handleDragOver(event) {
    event.preventDefault();
}

// ─── Actions ────────────────────────────────────────────────────────────────
async function runDetection(payloadText) {
    loadingDetect.value = true;
    startDetectProgress();
    try {
        const res = await axios.post('/analyze-text', { text: payloadText, mode: 'detect' }, { timeout: 300000 });
        detectionScore.value = normalizePercent(res.data.result);
        sentences.value = Array.isArray(res.data.sentences) ? res.data.sentences : [];
        analyzedText.value = res.data.analyzed_text || payloadText;
        stopDetectProgress(true);
    } catch (err) {
        stopDetectProgress();
        detectPercent.value = 0;
        detectionScore.value = null;
        throw err;
    } finally {
        setTimeout(() => { loadingDetect.value = false; }, 300);
    }
}

async function runFileDetection() {
    loadingDetect.value = true;
    startDetectProgress();
    try {
        const formData = new FormData();
        formData.append('file', fileObj.value);
        formData.append('mode', 'detect');
        const res = await axios.post('/analyze-file', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 300000,
        });
        const extracted = res.data.extracted_text || '';
        text.value = extracted;
        analyzedText.value = extracted;
        detectionScore.value = normalizePercent(res.data.result);
        sentences.value = Array.isArray(res.data.sentences) ? res.data.sentences : [];
        stopDetectProgress(true);
        nextTick(autoGrow);
        return extracted;
    } catch (err) {
        stopDetectProgress();
        detectPercent.value = 0;
        detectionScore.value = null;
        throw err;
    } finally {
        setTimeout(() => { loadingDetect.value = false; }, 300);
    }
}

async function runHumanization(payloadText) {
    loadingHumanize.value = true;
    startHumanizeProgress();
    try {
        const res = await axios.post('/humanize', {
            text: payloadText,
            intensity: intensity.value,
            mode: 'manual-humanize',
        }, { timeout: 180000 });
        humanizedText.value = res.data.humanized_text || '';
        humanizedAt.value = new Date();
        stopHumanizeProgress(true);
    } catch (err) {
        stopHumanizeProgress();
        humanizePercent.value = 0;
        humanizedText.value = '';
        throw err;
    } finally {
        setTimeout(() => { loadingHumanize.value = false; }, 300);
    }
}

async function run() {
    if (!canRun.value) return;
    error.value = null;
    hasRun.value = true;
    humanizedText.value = '';
    analyzedText.value = text.value;
    detectionScore.value = null;
    sentences.value = [];

    try {
        if (hasFile.value) {
            const extracted = await runFileDetection();
            detachFile();

            if (mode.value === 'humanize' && extracted && extracted.trim().length >= 10) {
                await runHumanization(extracted);
                toast.success('Fichier analysé et humanisé');
            } else {
                toast.success('Fichier analysé');
            }
            return;
        }

        const snapshot = text.value;
        if (mode.value === 'detect') {
            await runDetection(snapshot);
            toast.success('Analyse terminée');
        } else {
            const tasks = [runDetection(snapshot), runHumanization(snapshot)];
            const results = await Promise.allSettled(tasks);
            const failures = results.filter((r) => r.status === 'rejected');
            if (failures.length === results.length) {
                throw failures[0].reason;
            }
            if (failures.length > 0) {
                toast.warning('Une des deux tâches a échoué.');
            } else {
                toast.success('Détection et humanisation terminées');
            }
        }
    } catch (err) {
        const msg = err?.response?.data?.error || 'Une erreur est survenue.';
        error.value = msg;
        toast.error(msg);
    }
}

function clearAll() {
    text.value = '';
    detachFile();
    resetResults();
    nextTick(autoGrow);
}

// ─── Toolbar actions ────────────────────────────────────────────────────────
async function copyHumanized() {
    if (!humanizedText.value) return;
    try {
        await navigator.clipboard.writeText(humanizedText.value);
    } catch {
        const ta = document.createElement('textarea');
        ta.value = humanizedText.value;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
    }
    copied.value = true;
    toast.success('Texte copié');
    setTimeout(() => { copied.value = false; }, 1800);
}

async function shareHumanized() {
    if (!humanizedText.value) return;
    try {
        const res = await axios.post('/humanize/share', {
            text: humanizedText.value,
            intensity: intensity.value,
        });
        const url = res.data.share_url;
        try { await navigator.clipboard.writeText(url); } catch { /* ignore */ }
        shared.value = true;
        toast.success('Lien de partage copié (valable 1h)');
        setTimeout(() => { shared.value = false; }, 1800);
    } catch (err) {
        toast.error(err?.response?.data?.error || 'Partage indisponible.');
    }
}

async function downloadHumanized(format = 'txt') {
    if (!humanizedText.value) return;
    try {
        const res = await axios.post('/humanize/export', {
            text: humanizedText.value,
            format,
        }, { responseType: 'blob' });

        const blob = new Blob([res.data], { type: res.headers['content-type'] || 'application/octet-stream' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `reinia-humanise-${new Date().toISOString().slice(0, 10)}.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success('Téléchargement démarré');
    } catch (err) {
        toast.error(err?.response?.data?.error || 'Export indisponible.');
    }
}

function handleKeydown(event) {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
        event.preventDefault();
        run();
    }
}

// ─── Restore from history (?analysis=) ─────────────────────────────────────
onMounted(() => {
    autoGrow();
    const params = new URLSearchParams(window.location.search);
    const historyRef = params.get('analysis') || params.get('from_history');
    if (historyRef && historyRef !== 'undefined' && historyRef !== 'null') {
        loadingDetect.value = true;
        startDetectProgress();
        axios.get(`/history/${historyRef}`)
            .then((res) => {
                text.value = res.data.full_text || '';
                analyzedText.value = res.data.full_text || '';
                detectionScore.value = normalizePercent(res.data.ai_probability);
                sentences.value = [];
                hasRun.value = true;
                stopDetectProgress(true);
                nextTick(autoGrow);
            })
            .catch(() => {
                stopDetectProgress();
                error.value = 'Impossible de charger cette analyse.';
            })
            .finally(() => {
                setTimeout(() => { loadingDetect.value = false; }, 300);
            });
    }
});
</script>

<template>
    <AppLayout>
        <div class="relative min-h-full bg-[#0a0a0a] text-zinc-100">
            <!-- Subtle grid backdrop -->
            <div
                class="pointer-events-none absolute inset-0 opacity-[0.035]"
                style="background-image: radial-gradient(circle at 1px 1px, #fff 1px, transparent 0); background-size: 32px 32px;"
            ></div>

            <div class="relative mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 sm:py-14 lg:px-8">

                <!-- ─── Header ─── -->
                <header class="mb-10 max-w-2xl">
                    <div class="mb-3 inline-flex items-center gap-2 rounded-full border border-[#1f1f1f] bg-[#0f0f0f] px-3 py-1 text-[11px] font-medium tracking-wide text-zinc-400">
                        <span class="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]"></span>
                        Command Center
                    </div>
                    <h1 class="text-[32px] font-semibold tracking-tight text-zinc-50 sm:text-[38px]">
                        Detect. Humanize. Ship.
                    </h1>
                    <p class="mt-2 text-[15px] leading-relaxed text-zinc-500">
                        Lancez la détection d'IA et l'humanisation depuis un seul champ. Deux flux indépendants, un résultat en clair.
                    </p>
                </header>

                <!-- ─── Integrated Input Bar ─── -->
                <section
                    class="group relative overflow-hidden rounded-2xl border border-[#1f1f1f] bg-[#0c0c0c] shadow-[0_1px_0_rgba(255,255,255,0.02)_inset,0_20px_60px_-30px_rgba(0,0,0,0.8)] transition-colors focus-within:border-[#2a2a2a]"
                    @drop="handleDrop"
                    @dragover="handleDragOver"
                >
                    <!-- Hidden file input -->
                    <input
                        ref="fileInputRef"
                        type="file"
                        accept=".txt,.pdf,.docx,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        class="hidden"
                        @change="handleFileInput"
                    />

                    <!-- Pinned file chip -->
                    <transition
                        enter-active-class="transition duration-200 ease-out"
                        enter-from-class="opacity-0 -translate-y-1"
                        enter-to-class="opacity-100 translate-y-0"
                        leave-active-class="transition duration-150 ease-in"
                        leave-from-class="opacity-100"
                        leave-to-class="opacity-0 -translate-y-1"
                    >
                        <div v-if="hasFile" class="flex items-start gap-3 border-b border-[#1a1a1a] bg-[#0a0a0a]/60 px-5 py-3 sm:px-6">
                            <div class="flex min-w-0 flex-1 items-center gap-3">
                                <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-indigo-500/10 ring-1 ring-inset ring-indigo-500/20">
                                    <svg class="h-4 w-4 text-indigo-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/>
                                    </svg>
                                </span>
                                <div class="min-w-0 flex-1">
                                    <div class="flex items-center gap-2">
                                        <p class="truncate text-[13px] font-medium text-zinc-200">{{ fileName }}</p>
                                        <span class="shrink-0 rounded border border-[#1f1f1f] bg-[#0f0f0f] px-1.5 py-0.5 font-mono text-[9px] font-semibold tracking-wide text-zinc-400">{{ fileExtLabel() }}</span>
                                    </div>
                                    <p class="mt-0.5 flex items-center gap-1.5 text-[11px] text-zinc-500">
                                        <svg class="h-3 w-3 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                            <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
                                        </svg>
                                        Fichier épinglé · {{ formatBytes(fileSize) }}
                                    </p>
                                </div>
                            </div>
                            <button
                                type="button"
                                @click="detachFile"
                                :disabled="loading"
                                title="Détacher le fichier"
                                class="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-zinc-500 transition-colors hover:bg-[#161616] hover:text-rose-300 disabled:cursor-not-allowed disabled:opacity-40 cursor-pointer"
                            >
                                <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                                </svg>
                            </button>
                        </div>
                    </transition>

                    <!-- Textarea -->
                    <div class="px-5 pt-5 sm:px-6 sm:pt-6">
                        <textarea
                            ref="textareaRef"
                            v-model="text"
                            :maxlength="maxChars"
                            :disabled="loading || hasFile"
                            :placeholder="hasFile
                                ? 'Fichier joint — le texte sera extrait à l\'analyse.'
                                : 'Collez ou saisissez votre texte ici\n\n10 caractères minimum. ⌘+Entrée pour lancer. Glissez un .txt / .pdf / .docx ici pour l\'épingler.'"
                            class="block w-full resize-none bg-transparent text-[15px] leading-7 text-zinc-100 placeholder:text-zinc-600 focus:outline-none disabled:opacity-60"
                            style="min-height: 180px;"
                            @keydown="handleKeydown"
                        ></textarea>
                    </div>

                    <!-- Bottom control bar -->
                    <div class="flex flex-col gap-3 border-t border-[#1a1a1a] bg-[#0a0a0a]/50 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4 sm:px-5">
                        <div class="flex flex-wrap items-center gap-3">
                            <!-- Attach -->
                            <button
                                type="button"
                                @click="openFilePicker"
                                :disabled="loading"
                                :title="hasFile ? 'Remplacer le fichier' : 'Joindre un .txt / .pdf / .docx'"
                                :class="[
                                    'inline-flex h-8 w-8 items-center justify-center rounded-lg border transition-colors cursor-pointer disabled:cursor-not-allowed disabled:opacity-40',
                                    hasFile
                                        ? 'border-indigo-500/30 bg-indigo-500/10 text-indigo-300 hover:bg-indigo-500/15'
                                        : 'border-[#1f1f1f] bg-[#0f0f0f] text-zinc-500 hover:border-[#2a2a2a] hover:text-zinc-300'
                                ]"
                            >
                                <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
                                </svg>
                            </button>

                            <!-- Mode switch -->
                            <div class="inline-flex items-center gap-1 rounded-lg border border-[#1f1f1f] bg-[#0f0f0f] p-1">
                                <button
                                    type="button"
                                    @click="setMode('detect')"
                                    :class="[
                                        'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[12px] font-medium transition-all cursor-pointer',
                                        mode === 'detect'
                                            ? 'bg-[#1a1a1a] text-zinc-50 shadow-[0_0_0_1px_#262626]'
                                            : 'text-zinc-500 hover:text-zinc-300'
                                    ]"
                                >
                                    <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 12h10"/>
                                    </svg>
                                    Détecter
                                </button>
                                <button
                                    type="button"
                                    @click="setMode('humanize')"
                                    :class="[
                                        'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[12px] font-medium transition-all cursor-pointer',
                                        mode === 'humanize'
                                            ? 'bg-[#1a1a1a] text-zinc-50 shadow-[0_0_0_1px_#262626]'
                                            : 'text-zinc-500 hover:text-zinc-300'
                                    ]"
                                >
                                    <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/>
                                    </svg>
                                    Humaniser
                                </button>
                            </div>

                            <div v-if="mode === 'humanize'" class="hidden h-5 w-px bg-[#1f1f1f] sm:block"></div>

                            <transition
                                enter-active-class="transition duration-200 ease-out"
                                enter-from-class="opacity-0 -translate-x-2"
                                enter-to-class="opacity-100 translate-x-0"
                                leave-active-class="transition duration-150 ease-in"
                                leave-from-class="opacity-100"
                                leave-to-class="opacity-0"
                            >
                                <div v-if="mode === 'humanize'" class="inline-flex items-center gap-1 rounded-lg border border-[#1f1f1f] bg-[#0f0f0f] p-1">
                                    <button
                                        v-for="opt in intensityOptions"
                                        :key="opt.value"
                                        type="button"
                                        :title="opt.hint"
                                        @click="intensity = opt.value"
                                        :class="[
                                            'rounded-md px-2.5 py-1 text-[11px] font-medium tracking-wide transition-all cursor-pointer',
                                            intensity === opt.value
                                                ? 'bg-emerald-500/10 text-emerald-300 shadow-[0_0_0_1px_rgba(16,185,129,0.25)]'
                                                : 'text-zinc-500 hover:text-zinc-300'
                                        ]"
                                    >
                                        {{ opt.label }}
                                    </button>
                                </div>
                            </transition>
                        </div>

                        <div class="flex items-center justify-end gap-3">
                            <span class="text-[11px] tabular-nums text-zinc-600">
                                {{ charCount.toLocaleString() }} / {{ maxChars.toLocaleString() }}
                            </span>
                            <button
                                v-if="text && !loading"
                                type="button"
                                @click="clearAll"
                                class="inline-flex h-8 items-center justify-center rounded-md border border-[#1f1f1f] px-2 text-[11px] font-medium text-zinc-500 transition-colors hover:border-[#2a2a2a] hover:text-zinc-300 cursor-pointer"
                            >
                                Effacer
                            </button>
                            <button
                                type="button"
                                :disabled="!canRun"
                                @click="run"
                                :class="[
                                    'group/btn inline-flex h-8 items-center gap-1.5 rounded-md px-3.5 text-[12px] font-semibold transition-all',
                                    canRun
                                        ? 'bg-zinc-50 text-zinc-950 shadow-[0_0_0_1px_rgba(255,255,255,0.08),0_8px_24px_-12px_rgba(255,255,255,0.3)] hover:bg-white cursor-pointer'
                                        : 'cursor-not-allowed bg-[#151515] text-zinc-600'
                                ]"
                            >
                                <template v-if="loading">
                                    <svg class="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                                        <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                                    </svg>
                                    Analyse…
                                </template>
                                <template v-else>
                                    Lancer
                                    <svg class="h-3.5 w-3.5 transition-transform group-hover/btn:translate-x-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
                                    </svg>
                                </template>
                            </button>
                        </div>
                    </div>
                </section>

                <!-- ─── Error strip ─── -->
                <transition
                    enter-active-class="transition duration-200 ease-out"
                    enter-from-class="opacity-0 -translate-y-1"
                    enter-to-class="opacity-100 translate-y-0"
                    leave-active-class="transition duration-150 ease-in"
                    leave-from-class="opacity-100"
                    leave-to-class="opacity-0"
                >
                    <div
                        v-if="error"
                        class="mt-6 flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/[0.04] px-4 py-3 text-[13px] text-rose-300"
                    >
                        <svg class="mt-0.5 h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                        </svg>
                        <span>{{ error }}</span>
                    </div>
                </transition>

                <!-- ─── Results (split view) ─── -->
                <section
                    v-if="hasRun || loading"
                    class="mt-10 grid gap-5"
                    :class="showRightColumn ? 'lg:grid-cols-2' : 'lg:grid-cols-1'"
                >
                    <!-- ═══ LEFT: Detection ═══ -->
                    <article class="flex flex-col overflow-hidden rounded-2xl border border-[#1f1f1f] bg-[#0c0c0c]">
                        <header class="flex items-center justify-between gap-4 border-b border-[#1a1a1a] px-5 py-4">
                            <div class="flex items-center gap-2.5">
                                <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-violet-500/10 ring-1 ring-inset ring-violet-500/20">
                                    <svg class="h-3.5 w-3.5 text-violet-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 12h10"/>
                                    </svg>
                                </span>
                                <div>
                                    <p class="text-[13px] font-semibold text-zinc-200">Détection IA</p>
                                    <p class="text-[11px] text-zinc-500">
                                        <template v-if="loadingDetect">Analyse en cours…</template>
                                        <template v-else-if="detectionScore !== null">Analyse terminée</template>
                                        <template v-else>En attente</template>
                                    </p>
                                </div>
                            </div>
                            <div v-if="!loadingDetect && detectionScore !== null && verdict" class="flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ring-1 ring-inset"
                                 :class="[verdict.text, verdict.ring]">
                                <span class="h-1.5 w-1.5 rounded-full" :class="verdict.dot"></span>
                                {{ verdict.label }}
                            </div>
                        </header>

                        <!-- ─ Progress state ─ -->
                        <div v-if="loadingDetect" class="px-5 py-8 sm:px-8">
                            <div class="flex items-start gap-5">
                                <div class="relative flex h-[84px] w-[84px] shrink-0 items-center justify-center">
                                    <svg class="absolute inset-0 h-full w-full -rotate-90" viewBox="0 0 100 100">
                                        <circle cx="50" cy="50" r="44" fill="none" stroke="#161616" stroke-width="6"/>
                                        <circle
                                            cx="50" cy="50" r="44" fill="none"
                                            stroke="url(#detect-grad)" stroke-width="6" stroke-linecap="round"
                                            :stroke-dasharray="276.46"
                                            :stroke-dashoffset="276.46 - (276.46 * detectPercent) / 100"
                                            class="transition-[stroke-dashoffset] duration-300 ease-out"
                                        />
                                        <defs>
                                            <linearGradient id="detect-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                                                <stop offset="0%" stop-color="#8b5cf6"/>
                                                <stop offset="100%" stop-color="#6366f1"/>
                                            </linearGradient>
                                        </defs>
                                    </svg>
                                    <div class="flex flex-col items-center">
                                        <span class="font-display text-[20px] font-bold tabular-nums text-zinc-50">{{ Math.round(detectPercent) }}</span>
                                        <span class="-mt-1 text-[9px] font-medium text-zinc-500">PERCENT</span>
                                    </div>
                                </div>
                                <div class="min-w-0 flex-1">
                                    <div class="flex items-center gap-2">
                                        <p class="text-[13px] font-semibold text-zinc-100">Détection en cours</p>
                                        <span class="typing-dots text-violet-400"><span></span><span></span><span></span></span>
                                    </div>
                                    <p class="mt-0.5 truncate text-[12px] text-zinc-500">{{ detectSteps[detectStepIdx]?.label }}</p>

                                    <div class="mt-4 h-1 overflow-hidden rounded-full bg-[#141414]">
                                        <div
                                            class="relative h-full rounded-full bg-gradient-to-r from-violet-500 via-indigo-500 to-violet-500 bg-[length:200%_100%] transition-[width] duration-300 ease-out"
                                            :style="{ width: detectPercent + '%' }"
                                        >
                                            <div class="absolute inset-0 animate-shimmer bg-gradient-to-r from-transparent via-white/20 to-transparent"></div>
                                        </div>
                                    </div>

                                    <ul class="mt-4 grid grid-cols-1 gap-1.5 sm:grid-cols-2">
                                        <li
                                            v-for="(step, i) in detectSteps.slice(0, 8)"
                                            :key="i"
                                            class="flex items-center gap-2 text-[11px]"
                                            :class="i < detectStepIdx ? 'text-zinc-400' : i === detectStepIdx ? 'text-violet-300' : 'text-zinc-600'"
                                        >
                                            <span class="flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full"
                                                  :class="i < detectStepIdx ? 'bg-violet-500/15' : i === detectStepIdx ? 'bg-violet-500/20 ring-1 ring-violet-500/30' : 'bg-[#141414]'">
                                                <svg v-if="i < detectStepIdx" class="h-2 w-2 text-violet-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                                                    <polyline points="20 6 9 17 4 12"/>
                                                </svg>
                                                <span v-else-if="i === detectStepIdx" class="h-1 w-1 animate-pulse rounded-full bg-violet-400"></span>
                                            </span>
                                            <span class="truncate">{{ step.label }}</span>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        <!-- ─ Result state ─ -->
                        <div v-else-if="detectionScore !== null" class="flex flex-col">
                            <!-- Hero score -->
                            <div class="border-b border-[#1a1a1a] px-5 py-6 sm:px-8 sm:py-8">
                                <div class="flex items-start gap-6">
                                    <!-- Gauge -->
                                    <div class="relative flex h-[104px] w-[104px] shrink-0 items-center justify-center">
                                        <svg class="absolute inset-0 h-full w-full -rotate-90" viewBox="0 0 100 100">
                                            <circle cx="50" cy="50" r="44" fill="none" stroke="#161616" stroke-width="7"/>
                                            <circle
                                                cx="50" cy="50" r="44" fill="none"
                                                stroke="url(#score-grad)" stroke-width="7" stroke-linecap="round"
                                                :stroke-dasharray="276.46"
                                                :stroke-dashoffset="276.46 - (276.46 * aiPercent) / 100"
                                                class="transition-[stroke-dashoffset] duration-1000 ease-out"
                                            />
                                            <defs>
                                                <linearGradient id="score-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                                                    <stop offset="0%" :stop-color="detectionScore >= 60 ? '#a78bfa' : detectionScore >= 40 ? '#fbbf24' : '#34d399'"/>
                                                    <stop offset="100%" :stop-color="detectionScore >= 60 ? '#8b5cf6' : detectionScore >= 40 ? '#f59e0b' : '#10b981'"/>
                                                </linearGradient>
                                            </defs>
                                        </svg>
                                        <div class="flex flex-col items-center">
                                            <span class="font-display text-[28px] font-bold leading-none tabular-nums text-zinc-50">{{ aiPercent.toFixed(1) }}</span>
                                            <span class="mt-0.5 text-[9px] font-medium tracking-wider text-zinc-500">% IA</span>
                                        </div>
                                    </div>

                                    <!-- Verdict + distribution -->
                                    <div class="min-w-0 flex-1">
                                        <p class="text-[11px] font-medium uppercase tracking-wider text-zinc-500">Verdict</p>
                                        <h3 class="mt-0.5 font-display text-[20px] font-semibold text-zinc-50">{{ verdict?.label }}</h3>
                                        <p class="mt-1 text-[12px] leading-relaxed text-zinc-500">{{ verdict?.sub }}</p>

                                        <!-- Distribution bar -->
                                        <div class="mt-4">
                                            <div class="mb-1.5 flex items-center justify-between text-[10px] font-medium uppercase tracking-wider">
                                                <span class="text-violet-400">IA {{ aiPercent.toFixed(1) }}%</span>
                                                <span class="text-emerald-400">Humain {{ humanPercent.toFixed(1) }}%</span>
                                            </div>
                                            <div class="relative h-2 overflow-hidden rounded-full bg-[#141414] ring-1 ring-inset ring-[#1f1f1f]">
                                                <div
                                                    class="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r transition-all duration-1000 ease-out"
                                                    :class="verdict?.bar"
                                                    :style="{ width: aiPercent + '%' }"
                                                ></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Metric strip -->
                                <div class="mt-6 grid grid-cols-2 gap-2 sm:grid-cols-4">
                                    <div class="rounded-lg border border-[#1a1a1a] bg-[#0f0f0f] px-3 py-2.5">
                                        <p class="text-[9px] font-medium uppercase tracking-wider text-zinc-500">Mots</p>
                                        <p class="mt-0.5 font-display text-[15px] font-semibold tabular-nums text-zinc-100">{{ formatNumber(sourceMetrics.words) }}</p>
                                    </div>
                                    <div class="rounded-lg border border-[#1a1a1a] bg-[#0f0f0f] px-3 py-2.5">
                                        <p class="text-[9px] font-medium uppercase tracking-wider text-zinc-500">Caractères</p>
                                        <p class="mt-0.5 font-display text-[15px] font-semibold tabular-nums text-zinc-100">{{ formatNumber(sourceMetrics.chars) }}</p>
                                    </div>
                                    <div class="rounded-lg border border-[#1a1a1a] bg-[#0f0f0f] px-3 py-2.5">
                                        <p class="text-[9px] font-medium uppercase tracking-wider text-zinc-500">Phrases</p>
                                        <p class="mt-0.5 font-display text-[15px] font-semibold tabular-nums text-zinc-100">{{ formatNumber(sourceMetrics.sentences) }}</p>
                                    </div>
                                    <div class="rounded-lg border border-[#1a1a1a] bg-[#0f0f0f] px-3 py-2.5">
                                        <p class="text-[9px] font-medium uppercase tracking-wider text-zinc-500">Lecture</p>
                                        <p class="mt-0.5 font-display text-[15px] font-semibold tabular-nums text-zinc-100">{{ sourceMetrics.readingMin }} min</p>
                                    </div>
                                </div>
                            </div>

                            <!-- Analyzed text -->
                            <div class="px-5 py-5 sm:px-8 sm:py-6">
                                <div class="mb-3 flex items-center justify-between">
                                    <p class="text-[11px] font-medium uppercase tracking-wider text-zinc-500">Texte analysé</p>
                                    <p v-if="highlightedSentences" class="flex items-center gap-1.5 text-[10px] text-zinc-600">
                                        <span class="h-1.5 w-1.5 rounded-full bg-violet-500/40"></span>
                                        Phrases teintées selon leur score
                                    </p>
                                </div>
                                <div class="max-h-[480px] overflow-y-auto rounded-xl border border-[#1a1a1a] bg-[#090909] p-4 text-[14px] leading-7 scrollbar-thin sm:p-5">
                                    <template v-if="highlightedSentences">
                                        <span
                                            v-for="s in highlightedSentences"
                                            :key="s.id"
                                            :class="['rounded px-0.5 transition-colors', s.tone]"
                                        >{{ s.text }} </span>
                                    </template>
                                    <p v-else class="whitespace-pre-wrap text-zinc-300">{{ analyzedText }}</p>
                                </div>
                            </div>
                        </div>
                    </article>

                    <!-- ═══ RIGHT: Humanization ═══ -->
                    <article
                        v-if="showRightColumn"
                        class="flex flex-col overflow-hidden rounded-2xl border border-emerald-500/20 bg-[#0c0c0c] shadow-[0_0_40px_-20px_rgba(16,185,129,0.25)]"
                    >
                        <header class="flex items-center justify-between gap-4 border-b border-[#1a1a1a] px-5 py-4">
                            <div class="flex items-center gap-2.5">
                                <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/10 ring-1 ring-inset ring-emerald-500/20">
                                    <svg class="h-3.5 w-3.5 text-emerald-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275Z"/>
                                    </svg>
                                </span>
                                <div>
                                    <p class="text-[13px] font-semibold text-zinc-200">Résultat humanisé</p>
                                    <p class="text-[11px] text-zinc-500 capitalize">
                                        <template v-if="loadingHumanize">Réécriture · {{ intensity }}…</template>
                                        <template v-else>Intensité · {{ intensity }}</template>
                                    </p>
                                </div>
                            </div>

                            <div v-if="humanizedText && !loadingHumanize" class="flex items-center gap-1">
                                <button
                                    type="button"
                                    @click="copyHumanized"
                                    :title="copied ? 'Copié' : 'Copier'"
                                    class="inline-flex h-7 w-7 items-center justify-center rounded-md text-zinc-400 transition-colors hover:bg-[#161616] hover:text-zinc-100 cursor-pointer"
                                >
                                    <svg v-if="!copied" class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                        <rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>
                                    </svg>
                                    <svg v-else class="h-3.5 w-3.5 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <polyline points="20 6 9 17 4 12"/>
                                    </svg>
                                </button>
                                <button
                                    type="button"
                                    @click="shareHumanized"
                                    :title="shared ? 'Lien copié' : 'Partager'"
                                    class="inline-flex h-7 w-7 items-center justify-center rounded-md text-zinc-400 transition-colors hover:bg-[#161616] hover:text-zinc-100 cursor-pointer"
                                >
                                    <svg v-if="!shared" class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                        <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
                                    </svg>
                                    <svg v-else class="h-3.5 w-3.5 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <polyline points="20 6 9 17 4 12"/>
                                    </svg>
                                </button>
                                <button
                                    type="button"
                                    @click="downloadHumanized('txt')"
                                    title="Télécharger .txt"
                                    class="inline-flex h-7 w-7 items-center justify-center rounded-md text-zinc-400 transition-colors hover:bg-[#161616] hover:text-zinc-100 cursor-pointer"
                                >
                                    <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                                    </svg>
                                </button>
                                <div class="mx-1 h-4 w-px bg-[#1f1f1f]"></div>
                                <button
                                    type="button"
                                    @click="downloadHumanized('docx')"
                                    title="Exporter .docx"
                                    class="inline-flex h-7 items-center gap-1 rounded-md px-2 text-[11px] font-medium text-zinc-400 transition-colors hover:bg-[#161616] hover:text-zinc-100 cursor-pointer"
                                >
                                    DOCX
                                </button>
                            </div>
                        </header>

                        <!-- ─ Humanize progress ─ -->
                        <div v-if="loadingHumanize" class="px-5 py-8 sm:px-8">
                            <div class="flex items-start gap-5">
                                <div class="relative flex h-[84px] w-[84px] shrink-0 items-center justify-center">
                                    <svg class="absolute inset-0 h-full w-full -rotate-90" viewBox="0 0 100 100">
                                        <circle cx="50" cy="50" r="44" fill="none" stroke="#0f1a15" stroke-width="6"/>
                                        <circle
                                            cx="50" cy="50" r="44" fill="none"
                                            stroke="url(#hum-grad)" stroke-width="6" stroke-linecap="round"
                                            :stroke-dasharray="276.46"
                                            :stroke-dashoffset="276.46 - (276.46 * humanizePercent) / 100"
                                            class="transition-[stroke-dashoffset] duration-300 ease-out"
                                        />
                                        <defs>
                                            <linearGradient id="hum-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                                                <stop offset="0%" stop-color="#34d399"/>
                                                <stop offset="100%" stop-color="#10b981"/>
                                            </linearGradient>
                                        </defs>
                                    </svg>
                                    <div class="flex flex-col items-center">
                                        <span class="font-display text-[20px] font-bold tabular-nums text-zinc-50">{{ Math.round(humanizePercent) }}</span>
                                        <span class="-mt-1 text-[9px] font-medium text-zinc-500">PERCENT</span>
                                    </div>
                                </div>
                                <div class="min-w-0 flex-1">
                                    <div class="flex items-center gap-2">
                                        <p class="text-[13px] font-semibold text-zinc-100">Humanisation en cours</p>
                                        <span class="typing-dots text-emerald-400"><span></span><span></span><span></span></span>
                                    </div>
                                    <p class="mt-0.5 truncate text-[12px] text-zinc-500">{{ humanizeSteps[humanizeStepIdx]?.label }}</p>

                                    <div class="mt-4 h-1 overflow-hidden rounded-full bg-[#141414]">
                                        <div
                                            class="relative h-full rounded-full bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-500 bg-[length:200%_100%] transition-[width] duration-300 ease-out"
                                            :style="{ width: humanizePercent + '%' }"
                                        >
                                            <div class="absolute inset-0 animate-shimmer bg-gradient-to-r from-transparent via-white/20 to-transparent"></div>
                                        </div>
                                    </div>

                                    <ul class="mt-4 grid grid-cols-1 gap-1.5 sm:grid-cols-2">
                                        <li
                                            v-for="(step, i) in humanizeSteps"
                                            :key="i"
                                            class="flex items-center gap-2 text-[11px]"
                                            :class="i < humanizeStepIdx ? 'text-zinc-400' : i === humanizeStepIdx ? 'text-emerald-300' : 'text-zinc-600'"
                                        >
                                            <span class="flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full"
                                                  :class="i < humanizeStepIdx ? 'bg-emerald-500/15' : i === humanizeStepIdx ? 'bg-emerald-500/20 ring-1 ring-emerald-500/30' : 'bg-[#141414]'">
                                                <svg v-if="i < humanizeStepIdx" class="h-2 w-2 text-emerald-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                                                    <polyline points="20 6 9 17 4 12"/>
                                                </svg>
                                                <span v-else-if="i === humanizeStepIdx" class="h-1 w-1 animate-pulse rounded-full bg-emerald-400"></span>
                                            </span>
                                            <span class="truncate">{{ step.label }}</span>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        <!-- ─ Humanize result ─ -->
                        <div v-else-if="humanizedText" class="flex flex-col">
                            <!-- Metric strip -->
                            <div class="border-b border-[#1a1a1a] px-5 py-5 sm:px-8 sm:py-6">
                                <div class="grid grid-cols-2 gap-2 sm:grid-cols-4">
                                    <div class="rounded-lg border border-emerald-500/15 bg-emerald-500/[0.03] px-3 py-2.5">
                                        <p class="text-[9px] font-medium uppercase tracking-wider text-emerald-300/70">Mots</p>
                                        <p class="mt-0.5 flex items-baseline gap-1 font-display text-[15px] font-semibold tabular-nums text-zinc-100">
                                            {{ formatNumber(humanizedMetrics.words) }}
                                            <span v-if="humanizedMetrics.deltaWords !== 0"
                                                  class="text-[10px] font-medium tabular-nums"
                                                  :class="humanizedMetrics.deltaWords > 0 ? 'text-emerald-400' : 'text-zinc-500'">
                                                {{ humanizedMetrics.deltaWords > 0 ? '+' : '' }}{{ humanizedMetrics.deltaWords }}
                                            </span>
                                        </p>
                                    </div>
                                    <div class="rounded-lg border border-[#1a1a1a] bg-[#0f0f0f] px-3 py-2.5">
                                        <p class="text-[9px] font-medium uppercase tracking-wider text-zinc-500">Caractères</p>
                                        <p class="mt-0.5 font-display text-[15px] font-semibold tabular-nums text-zinc-100">{{ formatNumber(humanizedMetrics.chars) }}</p>
                                    </div>
                                    <div class="rounded-lg border border-[#1a1a1a] bg-[#0f0f0f] px-3 py-2.5">
                                        <p class="text-[9px] font-medium uppercase tracking-wider text-zinc-500">Intensité</p>
                                        <p class="mt-0.5 font-display text-[15px] font-semibold capitalize text-zinc-100">{{ intensity }}</p>
                                    </div>
                                    <div class="rounded-lg border border-[#1a1a1a] bg-[#0f0f0f] px-3 py-2.5">
                                        <p class="text-[9px] font-medium uppercase tracking-wider text-zinc-500">Delta</p>
                                        <p class="mt-0.5 font-display text-[15px] font-semibold tabular-nums"
                                           :class="humanizedMetrics.deltaChars >= 0 ? 'text-emerald-300' : 'text-amber-300'">
                                            {{ humanizedMetrics.deltaChars > 0 ? '+' : '' }}{{ formatNumber(humanizedMetrics.deltaChars) }}
                                        </p>
                                    </div>
                                </div>

                                <div class="mt-4 flex items-center gap-2 rounded-lg bg-emerald-500/[0.04] px-3 py-2 text-[11px] text-emerald-300/90 ring-1 ring-inset ring-emerald-500/15">
                                    <svg class="h-3.5 w-3.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                        <polyline points="20 6 9 17 4 12"/>
                                    </svg>
                                    <span>Texte réécrit avec succès — {{ intensity === 'aggressive' ? 'réécriture profonde' : intensity === 'medium' ? 'équilibre naturel' : 'édition subtile' }}.</span>
                                </div>
                            </div>

                            <!-- Humanized text body -->
                            <div class="px-5 py-5 sm:px-8 sm:py-6">
                                <div class="mb-3 flex items-center justify-between">
                                    <p class="text-[11px] font-medium uppercase tracking-wider text-emerald-300/80">Texte humanisé</p>
                                    <p class="text-[10px] text-zinc-600">Prêt à exporter</p>
                                </div>
                                <div class="max-h-[480px] overflow-y-auto rounded-xl border border-emerald-500/15 bg-[#090c0a] p-4 scrollbar-thin sm:p-5">
                                    <p class="whitespace-pre-wrap text-[14px] leading-7 text-zinc-200">{{ humanizedText }}</p>
                                </div>
                            </div>
                        </div>
                    </article>
                </section>

                <!-- ─── Empty state hint ─── -->
                <div v-if="!hasRun && !loading" class="mt-8 flex flex-wrap items-center gap-x-5 gap-y-2 text-[11px] text-zinc-600">
                    <span class="inline-flex items-center gap-1.5">
                        <kbd class="rounded border border-[#1f1f1f] bg-[#0f0f0f] px-1.5 py-0.5 font-mono text-[10px] text-zinc-400">⌘</kbd>
                        <kbd class="rounded border border-[#1f1f1f] bg-[#0f0f0f] px-1.5 py-0.5 font-mono text-[10px] text-zinc-400">↵</kbd>
                        pour lancer
                    </span>
                    <span class="h-3 w-px bg-[#1f1f1f]"></span>
                    <span>50 000 caractères max.</span>
                    <span class="h-3 w-px bg-[#1f1f1f]"></span>
                    <span>Les deux flux sont indépendants — basculez sans perdre vos résultats.</span>
                </div>
            </div>
        </div>
    </AppLayout>
</template>
