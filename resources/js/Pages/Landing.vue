<script setup>
import { ref, computed } from 'vue';
import axios from 'axios';

const text = ref('');
const result = ref(null);
const sentences = ref(null);
const error = ref(null);
const loading = ref(false);
const maxChars = 20000;

const charCount = computed(() => text.value.length);
const canAnalyze = computed(() => !loading.value && text.value.trim().length >= 10);

async function analyze() {
    if (!canAnalyze.value) return;
    loading.value = true;
    result.value = null;
    sentences.value = null;
    error.value = null;

    try {
        const res = await axios.post('/guest/analyze-text', { text: text.value }, { timeout: 120000 });
        result.value = res.data.result;
        sentences.value = res.data.sentences || null;
    } catch (err) {
        if (err.response?.status === 429) {
            error.value = 'Trop de requêtes. Veuillez patienter avant de réessayer.';
        } else {
            error.value = err.response?.data?.error || 'Une erreur est survenue.';
        }
    } finally {
        loading.value = false;
    }
}

const humanPercent = computed(() => result.value !== null ? (100 - result.value).toFixed(1) : '0');
const aiPercent = computed(() => result.value !== null ? result.value.toFixed(1) : '0');

function verdictText(val) {
    if (val >= 75) return 'Contenu IA';
    if (val >= 50) return 'Probablement IA';
    if (val >= 25) return 'Mixte';
    return 'Humain';
}

function verdictColor(val) {
    if (val >= 75) return 'text-red-500';
    if (val >= 50) return 'text-orange-500';
    if (val >= 25) return 'text-amber-500';
    return 'text-emerald-500';
}

function sentenceBg(score) {
    if (score >= 75) return 'bg-red-200/60 dark:bg-red-500/20';
    if (score >= 50) return 'bg-orange-200/50 dark:bg-orange-500/15';
    if (score >= 25) return 'bg-amber-100/60 dark:bg-amber-500/10';
    return '';
}
</script>

<template>
    <div class="min-h-screen bg-[#fafafa] dark:bg-[#171717] text-slate-800 dark:text-[#ececec]">
        <!-- Nav -->
        <nav class="flex items-center justify-between px-6 py-4 max-w-6xl mx-auto">
            <span class="text-xl font-semibold tracking-tight">ReinIA</span>
            <div class="flex items-center gap-3">
                <a href="/login" class="text-sm text-slate-500 dark:text-[#999] hover:text-slate-800 dark:hover:text-white transition-colors">Se connecter</a>
                <a href="/register" class="text-sm px-4 py-2 rounded-lg bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-medium hover:bg-slate-700 dark:hover:bg-slate-100 transition-colors">Commencer</a>
            </div>
        </nav>

        <!-- Hero -->
        <div class="max-w-4xl mx-auto px-6 pt-16 pb-12 text-center">
            <h1 class="text-4xl sm:text-5xl font-bold tracking-tight leading-tight text-slate-900 dark:text-white">
                Détecteur de texte IA
            </h1>
            <p class="mt-4 text-lg text-slate-500 dark:text-[#999] max-w-2xl mx-auto leading-relaxed">
                Analysez vos textes pour identifier le contenu généré par intelligence artificielle.
                Combinaison de RoBERTa, perplexité GPT-2 et analyse de burstiness.
            </p>
        </div>

        <!-- Analysis box -->
        <div class="max-w-3xl mx-auto px-6 pb-8">
            <div class="rounded-xl border border-slate-200 dark:border-[#333] bg-white dark:bg-[#1e1e1e] overflow-hidden">
                <textarea
                    v-model="text"
                    rows="8"
                    :maxlength="maxChars"
                    placeholder="Collez votre texte ici pour l'analyser..."
                    class="w-full bg-transparent border-0 focus:outline-none focus:ring-0 resize-none text-[15px] leading-7 px-5 py-4 text-slate-800 dark:text-[#ddd] placeholder-slate-300 dark:placeholder-[#555]"
                ></textarea>
                <div class="px-5 py-3 border-t border-slate-100 dark:border-[#2a2a2a] flex items-center justify-between">
                    <span class="text-xs tabular-nums text-slate-400 dark:text-[#666]">{{ charCount.toLocaleString() }} / {{ maxChars.toLocaleString() }} caractères</span>
                    <div class="flex items-center gap-3">
                        <span class="text-[11px] text-slate-400 dark:text-[#666]">Limite gratuite : 20 000 car.</span>
                    </div>
                </div>
            </div>

            <button
                @click="analyze"
                :disabled="!canAnalyze"
                class="w-full mt-4 py-3.5 rounded-xl text-sm font-semibold transition-all bg-slate-900 dark:bg-white text-white dark:text-slate-900 hover:bg-slate-700 dark:hover:bg-slate-100 disabled:bg-slate-200 dark:disabled:bg-[#333] disabled:text-slate-400 dark:disabled:text-[#666] disabled:cursor-not-allowed"
            >
                <span v-if="loading" class="flex items-center justify-center gap-2">
                    <svg class="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                    Analyse en cours...
                </span>
                <span v-else>Analyser le texte</span>
            </button>

            <!-- Error -->
            <div v-if="error" class="mt-4 p-4 rounded-xl border border-red-200 dark:border-red-500/25 bg-red-50 dark:bg-red-500/10 text-sm text-red-600 dark:text-red-400">
                {{ error }}
            </div>

            <!-- Result -->
            <div v-if="result !== null" class="mt-6 rounded-xl border border-slate-200 dark:border-[#333] bg-white dark:bg-[#1e1e1e] overflow-hidden">
                <div class="p-6">
                    <div class="flex items-center justify-center gap-8">
                        <div class="text-center">
                            <p class="text-3xl font-black tabular-nums text-emerald-500">{{ humanPercent }}%</p>
                            <p class="text-xs text-slate-400 dark:text-[#888] mt-1">Humain</p>
                        </div>
                        <div class="w-px h-12 bg-slate-200 dark:bg-[#333]"></div>
                        <div class="text-center">
                            <p class="text-3xl font-black tabular-nums text-red-500">{{ aiPercent }}%</p>
                            <p class="text-xs text-slate-400 dark:text-[#888] mt-1">IA</p>
                        </div>
                    </div>
                    <p class="text-center mt-3 text-sm font-semibold" :class="verdictColor(result)">{{ verdictText(result) }}</p>

                    <!-- Bar -->
                    <div class="mt-4 w-full h-2 rounded-full overflow-hidden bg-slate-100 dark:bg-[#2a2a2a]">
                        <div class="h-full rounded-full transition-all duration-1000" :class="result >= 50 ? 'bg-red-500' : result >= 25 ? 'bg-amber-500' : 'bg-emerald-500'" :style="{ width: result + '%' }"></div>
                    </div>
                </div>

                <!-- Sentences -->
                <div v-if="sentences && sentences.length > 0" class="px-6 pb-5 border-t border-slate-100 dark:border-[#2a2a2a] pt-4">
                    <p class="text-xs font-medium text-slate-400 dark:text-[#888] mb-3">Analyse phrase par phrase</p>
                    <p class="text-sm leading-8 text-slate-700 dark:text-[#ccc]">
                        <template v-for="(sent, i) in sentences" :key="i">
                            <span
                                class="rounded px-0.5 py-0.5 cursor-default"
                                :class="sentenceBg(sent.score)"
                                :title="`Score IA : ${sent.score}%`"
                            >{{ sent.text }}</span>{{ ' ' }}
                        </template>
                    </p>
                </div>

                <!-- Upsell -->
                <div class="px-6 py-4 border-t border-slate-100 dark:border-[#2a2a2a] bg-slate-50 dark:bg-[#1a1a1a]">
                    <div class="flex items-center justify-between">
                        <p class="text-xs text-slate-400 dark:text-[#888]">
                            Analyse gratuite limitee a 20 000 caracteres
                        </p>
                        <a href="/register" class="text-xs font-medium px-3 py-1.5 rounded-lg bg-slate-900 dark:bg-white text-white dark:text-slate-900 hover:bg-slate-700 dark:hover:bg-slate-100 transition-colors">
                            Illimite &rarr;
                        </a>
                    </div>
                </div>
            </div>
        </div>

        <!-- Features -->
        <div class="max-w-4xl mx-auto px-6 py-16">
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-8">
                <div>
                    <div class="w-10 h-10 rounded-lg bg-slate-100 dark:bg-[#2a2a2a] flex items-center justify-center mb-3">
                        <svg class="w-5 h-5 text-slate-500 dark:text-[#999]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3" /></svg>
                    </div>
                    <h3 class="text-sm font-semibold text-slate-800 dark:text-white">RoBERTa</h3>
                    <p class="text-sm text-slate-500 dark:text-[#999] mt-1 leading-relaxed">Modele de deep learning entraine sur des textes humains et generes par IA.</p>
                </div>
                <div>
                    <div class="w-10 h-10 rounded-lg bg-slate-100 dark:bg-[#2a2a2a] flex items-center justify-center mb-3">
                        <svg class="w-5 h-5 text-slate-500 dark:text-[#999]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" /></svg>
                    </div>
                    <h3 class="text-sm font-semibold text-slate-800 dark:text-white">Perplexite GPT-2</h3>
                    <p class="text-sm text-slate-500 dark:text-[#999] mt-1 leading-relaxed">Mesure la previsibilite du texte. L'IA produit du texte tres previsible.</p>
                </div>
                <div>
                    <div class="w-10 h-10 rounded-lg bg-slate-100 dark:bg-[#2a2a2a] flex items-center justify-center mb-3">
                        <svg class="w-5 h-5 text-slate-500 dark:text-[#999]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" /></svg>
                    </div>
                    <h3 class="text-sm font-semibold text-slate-800 dark:text-white">Burstiness</h3>
                    <p class="text-sm text-slate-500 dark:text-[#999] mt-1 leading-relaxed">Analyse la variation entre phrases. L'humain alterne phrases courtes et longues.</p>
                </div>
            </div>
        </div>

        <!-- Comparison table -->
        <div class="max-w-3xl mx-auto px-6 pb-16">
            <div class="rounded-xl border border-slate-200 dark:border-[#333] overflow-hidden">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="border-b border-slate-200 dark:border-[#333]">
                            <th class="text-left px-5 py-3 font-medium text-slate-500 dark:text-[#888]"></th>
                            <th class="text-center px-5 py-3 font-medium text-slate-500 dark:text-[#888]">Gratuit</th>
                            <th class="text-center px-5 py-3 font-medium text-slate-800 dark:text-white bg-slate-50 dark:bg-[#1e1e1e]">Inscrit</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 dark:divide-[#2a2a2a]">
                        <tr>
                            <td class="px-5 py-3 text-slate-600 dark:text-[#ccc]">Limite de caracteres</td>
                            <td class="text-center px-5 py-3 text-slate-500 dark:text-[#999]">20 000</td>
                            <td class="text-center px-5 py-3 font-medium text-slate-800 dark:text-white bg-slate-50 dark:bg-[#1e1e1e]">1 500 000</td>
                        </tr>
                        <tr>
                            <td class="px-5 py-3 text-slate-600 dark:text-[#ccc]">Import fichier (PDF, DOCX)</td>
                            <td class="text-center px-5 py-3 text-slate-400">-</td>
                            <td class="text-center px-5 py-3 bg-slate-50 dark:bg-[#1e1e1e]"><svg class="w-4 h-4 text-emerald-500 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg></td>
                        </tr>
                        <tr>
                            <td class="px-5 py-3 text-slate-600 dark:text-[#ccc]">Analyse par section</td>
                            <td class="text-center px-5 py-3 text-slate-400">-</td>
                            <td class="text-center px-5 py-3 bg-slate-50 dark:bg-[#1e1e1e]"><svg class="w-4 h-4 text-emerald-500 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg></td>
                        </tr>
                        <tr>
                            <td class="px-5 py-3 text-slate-600 dark:text-[#ccc]">Historique des analyses</td>
                            <td class="text-center px-5 py-3 text-slate-400">-</td>
                            <td class="text-center px-5 py-3 bg-slate-50 dark:bg-[#1e1e1e]"><svg class="w-4 h-4 text-emerald-500 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg></td>
                        </tr>
                        <tr>
                            <td class="px-5 py-3 text-slate-600 dark:text-[#ccc]">Traitement intelligent (RAG)</td>
                            <td class="text-center px-5 py-3 text-slate-400">-</td>
                            <td class="text-center px-5 py-3 bg-slate-50 dark:bg-[#1e1e1e]"><svg class="w-4 h-4 text-emerald-500 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg></td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div class="text-center mt-6">
                <a href="/register" class="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold bg-slate-900 dark:bg-white text-white dark:text-slate-900 hover:bg-slate-700 dark:hover:bg-slate-100 transition-colors">
                    Creer un compte gratuit
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" /></svg>
                </a>
            </div>
        </div>

        <!-- Footer -->
        <footer class="border-t border-slate-200 dark:border-[#2a2a2a] py-6 text-center text-xs text-slate-400 dark:text-[#666]">
            ReinIA Detector &mdash; Analyse locale, aucune donnee envoyee a des tiers.
        </footer>
    </div>
</template>
