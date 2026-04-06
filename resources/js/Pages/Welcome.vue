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

onMounted(() => {
    const params = new URLSearchParams(window.location.search);
    const detectionId = params.get('from_history');
    if (detectionId) {
        loading.value = true;
        mode.value = 'text';
        axios.get(`/history/${detectionId}`)
            .then((res) => {
                text.value = res.data.full_text || '';
                result.value = res.data.ai_probability;
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
    if (charPercent.value > 90) return 'text-red-500 dark:text-red-400';
    if (charPercent.value > 70) return 'text-amber-500 dark:text-amber-400';
    return 'text-slate-400 dark:text-slate-500';
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
            result.value = res.data.result;
            chunkResults.value = res.data.chunks || null;
            sentences.value = res.data.sentences || null;
        } else {
            const formData = new FormData();
            formData.append('file', fileObj.value);
            const res = await axios.post('/analyze-file', formData, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 300000 });
            stopProgress();
            text.value = res.data.extracted_text || '';
            result.value = res.data.result;
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
        <div class="flex items-start justify-center px-4 sm:px-6 lg:px-8 py-6 sm:py-10">
            <div class="w-full max-w-6xl space-y-6">

                <!-- Header -->
                <div>
                    <div class="flex items-center gap-3 mb-1">
                        <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                            <svg class="w-[18px] h-[18px] text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" /></svg>
                        </div>
                        <div>
                            <h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Analyseur de texte IA</h1>
                            <p class="text-sm text-slate-500 dark:text-slate-400">Détectez le contenu généré par intelligence artificielle</p>
                        </div>
                    </div>
                </div>

                <!-- Tabs -->
                <div class="flex items-center gap-1 p-1 rounded-xl w-fit bg-slate-100 dark:bg-slate-800/80">
                    <button @click="switchMode('text')" class="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200" :class="mode === 'text' ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'">
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" /></svg>
                        Coller un texte
                    </button>
                    <button @click="switchMode('file')" class="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200" :class="mode === 'file' ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'">
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" /></svg>
                        Importer un fichier
                    </button>
                </div>

                <!-- TEXT MODE -->
                <div v-if="mode === 'text'" class="rounded-2xl border transition-all duration-500 bg-white dark:bg-slate-900/50 border-slate-200 dark:border-slate-700/60 shadow-sm overflow-hidden">
                    <!-- Collapsed -->
                    <div v-if="textCollapsed && text" class="cursor-pointer group" @click="textCollapsed = false">
                        <div class="px-4 sm:px-6 py-3 flex items-center justify-between bg-slate-50/80 dark:bg-slate-800/30 border-b border-slate-100 dark:border-slate-800/60">
                            <div class="flex items-center gap-2">
                                <svg class="w-4 h-4 text-slate-400 transition-transform duration-300 -rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" /></svg>
                                <span class="text-xs font-medium text-slate-500 dark:text-slate-400">Texte analysé</span>
                                <span class="text-[10px] px-1.5 py-0.5 rounded-md bg-slate-100 dark:bg-slate-700 text-slate-400 dark:text-slate-500 tabular-nums">{{ charCount.toLocaleString() }} car.</span>
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="text-[11px] text-slate-400 dark:text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity">Cliquer pour déplier</span>
                                <button @click.stop="clearAll" class="text-xs transition-colors text-slate-400 hover:text-red-500 p-1 rounded-lg hover:bg-red-50 dark:hover:bg-red-500/10">
                                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                                </button>
                            </div>
                        </div>
                        <div class="px-4 sm:px-6 py-3">
                            <p class="text-sm leading-relaxed line-clamp-3 text-slate-500 dark:text-slate-400">{{ text }}</p>
                        </div>
                    </div>
                    <!-- Expanded -->
                    <template v-else>
                        <div class="p-4 sm:p-6">
                            <textarea v-model="text" rows="18" :maxlength="maxChars" placeholder="Collez ou saisissez votre texte ici...

Le texte doit contenir au minimum 10 caractères pour être analysé." class="w-full bg-transparent border-0 focus:outline-none focus:ring-0 resize-none text-[15px] leading-7 text-slate-800 dark:text-slate-200 placeholder-slate-300 dark:placeholder-slate-600" autofocus></textarea>
                        </div>
                        <div class="px-4 sm:px-6 py-3 border-t flex items-center justify-between border-slate-100 dark:border-slate-800/60 bg-slate-50/80 dark:bg-slate-800/30">
                            <div class="flex items-center gap-1.5">
                                <div class="w-20 h-1.5 rounded-full overflow-hidden bg-slate-200 dark:bg-slate-700">
                                    <div class="h-full rounded-full transition-all duration-300" :class="charPercent > 90 ? 'bg-red-500' : charPercent > 70 ? 'bg-amber-500' : 'bg-blue-500'" :style="{ width: charPercent + '%' }"></div>
                                </div>
                                <span class="text-[11px] tabular-nums" :class="charColor">{{ charCount.toLocaleString() }} / {{ maxChars.toLocaleString() }}</span>
                            </div>
                            <button v-if="text" @click="clearAll" class="text-xs transition-colors text-slate-400 hover:text-red-500 flex items-center gap-1">
                                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                                Effacer tout
                            </button>
                        </div>
                    </template>
                </div>

                <!-- FILE MODE -->
                <FileInput v-if="mode === 'file'" :file-name="fileName" :file-obj="fileObj" @select="selectFile" @remove="fileObj = null; fileName = null;" />

                <!-- Analyze button -->
                <button v-if="!loading" @click="analyze" :disabled="!canAnalyze" class="w-full relative overflow-hidden bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 disabled:from-slate-300 disabled:to-slate-300 dark:disabled:from-slate-700 dark:disabled:to-slate-700 disabled:cursor-not-allowed text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 shadow-lg shadow-blue-500/25 disabled:shadow-none active:scale-[0.98] text-base">
                    <span class="flex items-center justify-center gap-2.5">
                        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" /></svg>
                        Lancer l'analyse
                    </span>
                </button>

                <!-- Progress -->
                <ProgressPanel v-if="loading" :percent="progressPercent" :label="loadingProgress" />

                <!-- Error -->
                <transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0 -translate-y-2" enter-to-class="opacity-100 translate-y-0" leave-active-class="transition duration-150 ease-in" leave-from-class="opacity-100" leave-to-class="opacity-0">
                    <div v-if="error" class="p-4 rounded-xl border flex items-start gap-3 bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-500/25">
                        <svg class="w-5 h-5 text-red-500 dark:text-red-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" /></svg>
                        <div>
                            <p class="text-sm font-medium text-red-700 dark:text-red-400">Erreur d'analyse</p>
                            <p class="text-sm text-red-600/80 dark:text-red-400/70 mt-0.5">{{ error }}</p>
                        </div>
                    </div>
                </transition>

                <!-- Result -->
                <AnalysisResult v-if="result !== null" :result="result" :chunk-results="chunkResults" :sentences="sentences" :preprocessing="preprocessing" />

            </div>
        </div>
    </AppLayout>
</template>
