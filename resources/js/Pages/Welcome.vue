<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import AppLayout from '../Layouts/AppLayout.vue';
import AnalysisResult from '../Components/AnalysisResult.vue';
import ProgressPanel from '../Components/ProgressPanel.vue';
import FileInput from '../Components/FileInput.vue';

const mode = ref('text');
const text = ref('');
const result = ref(null);
const chunkResults = ref(null);
const sentences = ref(null);
const preprocessing = ref(null);
const error = ref(null);
const loading = ref(false);
const loadingProgress = ref('');
const progressPercent = ref(0);
const textCollapsed = ref(false);
const fileName = ref(null);
const fileObj = ref(null);
const maxChars = 1500000;
const maxFileSize = 25 * 1024 * 1024;
let progressInterval = null;

function normalizePercent(value) {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : null;
}

onMounted(() => {
    const params = new URLSearchParams(window.location.search);
    const detectionRef = params.get('analysis') || params.get('from_history');
    if (detectionRef && detectionRef !== 'undefined' && detectionRef !== 'null') {
        loading.value = true;
        mode.value = 'text';
        axios.get(`/history/${detectionRef}`)
            .then((res) => {
                text.value = res.data.full_text || '';
                result.value = normalizePercent(res.data.ai_probability);
                chunkResults.value = res.data.chunk_results || null;
                textCollapsed.value = true;
            })
            .catch(() => { error.value = 'Impossible de charger cette analyse.'; })
            .finally(() => { loading.value = false; });
    }
});

const charCount = computed(() => text.value.length);
const charPercent = computed(() => Math.min((charCount.value / maxChars) * 100, 100));
const charColor = computed(() => {
    if (charPercent.value > 90) return 'text-rose-500';
    if (charPercent.value > 70) return 'text-amber-500';
    return 'text-zinc-500';
});

const canAnalyze = computed(() => {
    if (loading.value) return false;
    if (mode.value === 'text') return text.value.trim().length >= 10;
    return !!fileObj.value;
});

function switchMode(m) {
    mode.value = m;
    result.value = null;
    chunkResults.value = null;
    sentences.value = null;
    preprocessing.value = null;
    error.value = null;
    textCollapsed.value = false;
}

const progressSteps = [
    { at: 0, label: 'Préparation du document...' },
    { at: 5, label: 'Nettoyage et extraction du texte...' },
    { at: 12, label: 'Suppression des artefacts...' },
    { at: 20, label: 'Découpage en sections...' },
    { at: 28, label: 'Traduction vers l\'anglais...' },
    { at: 38, label: 'Analyse RoBERTa en cours...' },
    { at: 52, label: 'Calcul de la perplexité...' },
    { at: 65, label: 'Analyse de la burstiness...' },
    { at: 78, label: 'Agrégation des résultats...' },
    { at: 88, label: 'Finalisation...' },
];

function startProgress(isFile) {
    progressPercent.value = 0;
    loadingProgress.value = isFile ? 'Envoi du fichier...' : 'Préparation...';
    let stepIndex = 0;
    progressInterval = setInterval(() => {
        if (stepIndex < progressSteps.length && progressPercent.value >= progressSteps[stepIndex].at) {
            loadingProgress.value = progressSteps[stepIndex].label;
            stepIndex++;
        }
        const remaining = 92 - progressPercent.value;
        progressPercent.value = Math.min(92, progressPercent.value + Math.max(0.3, remaining * 0.02));
    }, 200);
}

function stopProgress() {
    clearInterval(progressInterval);
    progressInterval = null;
    progressPercent.value = 100;
    loadingProgress.value = 'Terminé !';
}

async function analyze() {
    if (!canAnalyze.value) return;
    loading.value = true;
    textCollapsed.value = true;
    result.value = null;
    chunkResults.value = null;
    sentences.value = null;
    preprocessing.value = null;
    error.value = null;
    startProgress(mode.value === 'file');

    try {
        if (mode.value === 'text') {
            const res = await axios.post('/analyze-text', { text: text.value }, { timeout: 300000 });
            stopProgress();
            result.value = normalizePercent(res.data.result);
            chunkResults.value = res.data.chunks || null;
            sentences.value = res.data.sentences || null;
        } else {
            const formData = new FormData();
            formData.append('file', fileObj.value);
            const res = await axios.post('/analyze-file', formData, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 300000 });
            stopProgress();
            text.value = res.data.extracted_text || '';
            result.value = normalizePercent(res.data.result);
            chunkResults.value = res.data.chunks || null;
            sentences.value = res.data.sentences || null;
            preprocessing.value = res.data.preprocessing || null;
            mode.value = 'text';
        }
    } catch (err) {
        clearInterval(progressInterval);
        progressPercent.value = 0;
        error.value = err.response?.data?.error || 'Une erreur est survenue.';
    } finally {
        setTimeout(() => { loading.value = false; loadingProgress.value = ''; progressPercent.value = 0; }, 600);
    }
}

function selectFile(file) {
    if (!file) return;
    if (file.size > maxFileSize) { error.value = `Fichier trop volumineux (${(file.size / 1024 / 1024).toFixed(1)} Mo / 25 Mo max).`; return; }
    const allowed = ['text/plain', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowed.includes(file.type)) { error.value = 'Format non supporté. Utilisez .txt, .pdf ou .docx.'; return; }
    error.value = null;
    fileObj.value = file;
    fileName.value = file.name;
}

function clearAll() { text.value = ''; result.value = null; chunkResults.value = null; sentences.value = null; preprocessing.value = null; error.value = null; fileObj.value = null; fileName.value = null; textCollapsed.value = false; }
</script>

<template>
    <AppLayout>
        <div class="flex items-start justify-center bg-white px-4 py-8 dark:bg-[#18181b] sm:px-6 sm:py-10 lg:px-8">
            <div class="w-full max-w-6xl space-y-8">

                <!-- Header -->
                <div class="space-y-3">
                    <div class="space-y-2">
                        <h1 class="text-3xl font-semibold tracking-tight text-zinc-950 dark:text-zinc-50">Detection Workspace</h1>
                        <p class="max-w-3xl text-sm text-zinc-500 dark:text-zinc-400">
                            Détectez le contenu généré par intelligence artificielle dans une interface plus claire, plus lisible et pensée comme un produit SaaS professionnel.
                        </p>
                    </div>
                </div>

                <!-- Tabs -->
                <div class="border-b border-zinc-200 dark:border-zinc-800">
                    <div class="-mb-px flex items-center gap-8">
                    <button @click="switchMode('text')" class="flex items-center gap-2 border-b-2 px-1 pb-3 text-sm font-medium transition-colors cursor-pointer" :class="mode === 'text' ? 'border-blue-600 text-zinc-950 dark:text-zinc-50' : 'border-transparent text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200'">
                        Coller un texte
                    </button>
                    <button @click="switchMode('file')" class="flex items-center gap-2 border-b-2 px-1 pb-3 text-sm font-medium transition-colors cursor-pointer" :class="mode === 'file' ? 'border-blue-600 text-zinc-950 dark:text-zinc-50' : 'border-transparent text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200'">
                        Importer un fichier
                    </button>
                    </div>
                </div>

                <!-- TEXT MODE -->
                <div v-if="mode === 'text'" class="overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm transition-all duration-500 dark:border-zinc-800 dark:bg-zinc-900/90">
                    <!-- Collapsed -->
                    <div v-if="textCollapsed && text" class="cursor-pointer group" @click="textCollapsed = false">
                        <div class="flex items-center justify-between border-b border-zinc-200 bg-zinc-50 px-6 py-4 dark:border-zinc-800 dark:bg-zinc-900">
                            <div class="flex items-center gap-2">
                                <svg class="h-4 w-4 -rotate-90 text-zinc-400 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" /></svg>
                                <span class="text-sm font-medium text-zinc-950 dark:text-zinc-100">Texte analysé</span>
                                <span class="rounded-full border border-zinc-200 bg-white px-2 py-1 text-sm text-zinc-500 tabular-nums dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-400">{{ charCount.toLocaleString() }} car.</span>
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="text-sm text-zinc-500 opacity-0 transition-opacity group-hover:opacity-100 dark:text-zinc-400">Cliquer pour déplier</span>
                                <button @click.stop="clearAll" class="rounded-lg p-1 text-zinc-400 transition-colors hover:bg-zinc-100 hover:text-rose-500 dark:hover:bg-zinc-800 cursor-pointer">
                                    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                                </button>
                            </div>
                        </div>
                        <div class="px-6 py-4">
                            <p class="line-clamp-3 text-sm leading-7 text-zinc-500 dark:text-zinc-400">{{ text }}</p>
                        </div>
                    </div>
                    <!-- Expanded -->
                    <template v-else>
                        <div class="p-6 sm:p-8">
                            <textarea v-model="text" rows="18" :maxlength="maxChars" placeholder="Collez ou saisissez votre texte ici...

Le texte doit contenir au minimum 10 caractères pour être analysé." class="w-full resize-none border-0 bg-transparent text-[15px] leading-7 text-zinc-800 placeholder:text-zinc-400 focus:outline-none focus:ring-0 dark:text-zinc-100 dark:placeholder:text-zinc-500" autofocus></textarea>
                        </div>
                        <div class="flex items-center justify-between border-t border-zinc-200 bg-zinc-50 px-6 py-4 dark:border-zinc-800 dark:bg-zinc-900">
                            <div class="flex items-center gap-1.5">
                                <div class="h-2 w-24 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
                                    <div class="h-full rounded-full transition-all duration-300" :class="charPercent > 90 ? 'bg-rose-500' : charPercent > 70 ? 'bg-amber-400' : 'bg-zinc-900'" :style="{ width: charPercent + '%' }"></div>
                                </div>
                                <span class="text-sm tabular-nums" :class="charColor">{{ charCount.toLocaleString() }} / {{ maxChars.toLocaleString() }}</span>
                            </div>
                            <button v-if="text" @click="clearAll" class="flex items-center gap-1 text-sm text-zinc-500 transition-colors hover:text-rose-500 dark:text-zinc-400 cursor-pointer">
                                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                                Effacer tout
                            </button>
                        </div>
                    </template>
                </div>

                <!-- FILE MODE -->
                <FileInput v-if="mode === 'file'" :file-name="fileName" :file-obj="fileObj" @select="selectFile" @remove="fileObj = null; fileName = null;" />

                <!-- Analyze button -->
                <button v-if="!loading" @click="analyze" :disabled="!canAnalyze" class="w-full rounded-lg bg-zinc-900 px-6 py-4 text-base font-semibold text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-300 dark:bg-zinc-100 dark:text-zinc-950 dark:hover:bg-zinc-200 dark:disabled:bg-zinc-700 dark:disabled:text-zinc-400">
                    <span class="flex items-center justify-center gap-2.5">
                        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 5.25h16.5m-16.5 6h16.5m-16.5 6H12" /></svg>
                        Lancer l'analyse
                    </span>
                </button>

                <!-- Progress -->
                <ProgressPanel v-if="loading" :percent="progressPercent" :label="loadingProgress" />

                <!-- Error -->
                <transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0 -translate-y-2" enter-to-class="opacity-100 translate-y-0" leave-active-class="transition duration-150 ease-in" leave-from-class="opacity-100" leave-to-class="opacity-0">
                    <div v-if="error" class="flex items-start gap-3 rounded-lg border border-rose-200 bg-rose-50 p-4">
                        <svg class="mt-0.5 h-5 w-5 shrink-0 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" /></svg>
                        <div>
                            <p class="text-sm font-semibold text-rose-700">Erreur d'analyse</p>
                            <p class="mt-0.5 text-sm text-rose-600">{{ error }}</p>
                        </div>
                    </div>
                </transition>

                <!-- Result -->
                <AnalysisResult v-if="result !== null" :result="result" :chunk-results="chunkResults" :sentences="sentences" :preprocessing="preprocessing" />

            </div>
        </div>
    </AppLayout>
</template>
