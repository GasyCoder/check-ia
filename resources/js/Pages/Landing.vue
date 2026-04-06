<script setup>
import { computed, ref, watch } from 'vue';
import { Head } from '@inertiajs/vue3';
import axios from 'axios';

const text = ref('');
const result = ref(null);
const sentences = ref(null);
const error = ref(null);
const loading = ref(false);
const dark = ref(typeof window !== 'undefined' ? localStorage.getItem('theme') === 'dark' : false);
const analysisCard = ref(null);
const resultsSection = ref(null);

const maxChars = 20000;
const minChars = 10;

const charCount = computed(() => text.value.length);
const canAnalyze = computed(() => !loading.value && text.value.trim().length >= minChars);
const currentYear = new Date().getFullYear();
const humanPercent = computed(() => (result.value !== null ? (100 - result.value).toFixed(1) : '0.0'));
const aiPercent = computed(() => (result.value !== null ? result.value.toFixed(1) : '0.0'));

const verdict = computed(() => {
    if (result.value === null) return 'Lancez une analyse pour voir le résultat.';
    if (result.value >= 75) return 'Le texte présente un signal IA élevé.';
    if (result.value >= 50) return 'Le texte semble partiellement généré.';
    if (result.value >= 25) return 'Le texte paraît mixte.';
    return 'Le texte paraît plutôt humain.';
});

function sentenceBg(score) {
    if (score >= 75) return 'bg-red-100 dark:bg-red-500/15';
    if (score >= 50) return 'bg-orange-100 dark:bg-orange-500/15';
    if (score >= 25) return 'bg-amber-100 dark:bg-amber-500/15';
    return 'bg-emerald-100 dark:bg-emerald-500/15';
}

function clearText() {
    text.value = '';
    result.value = null;
    sentences.value = null;
    error.value = null;
}

watch(
    dark,
    value => {
        document.documentElement.classList.toggle('dark', value);
        localStorage.setItem('theme', value ? 'dark' : 'light');
    },
    { immediate: true },
);

function toggleTheme() {
    dark.value = !dark.value;
}

async function analyze() {
    if (!canAnalyze.value) return;

    loading.value = true;
    result.value = null;
    sentences.value = null;
    error.value = null;

    try {
        const response = await axios.post('/guest/analyze-text', { text: text.value }, { timeout: 120000 });
        result.value = response.data.result;
        sentences.value = response.data.sentences || [];
        requestAnimationFrame(() => {
            resultsSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    } catch (err) {
        if (err.response?.status === 429) {
            error.value = 'Trop de requêtes. Réessayez dans une minute.';
        } else {
            error.value = err.response?.data?.error || 'Une erreur est survenue pendant l’analyse.';
        }
    } finally {
        loading.value = false;
    }
}
</script>

<template>
    <Head title="ReinIA" />

    <div class="min-h-screen bg-slate-50 text-slate-900 transition-colors dark:bg-[#0f1720] dark:text-slate-100">
        <div class="absolute inset-x-0 top-0 -z-10 h-[320px] bg-[radial-gradient(circle_at_top,rgba(15,23,42,0.07),transparent_68%)] dark:bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.08),transparent_60%)]"></div>

        <nav class="sticky top-0 z-50 border-b border-slate-200/80 bg-slate-50/90 backdrop-blur-xl supports-[backdrop-filter]:bg-slate-50/75 dark:border-slate-800/80 dark:bg-[#0f1720]/85">
            <div class="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6 xl:max-w-[1400px]">
                <a href="/" class="flex items-center gap-3">
                    <span class="flex h-10 w-10 items-center justify-center rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
                        <span class="h-4 w-4 rounded-full bg-teal-500 dark:bg-cyan-400"></span>
                    </span>
                    <span class="min-w-0">
                        <span class="block text-sm font-semibold tracking-tight text-slate-950 dark:text-white sm:text-base">ReinIA</span>
                        <span class="block text-xs text-slate-500 dark:text-slate-400">Détection de texte IA</span>
                    </span>
                </a>

                <div class="flex w-full items-center justify-between gap-2 sm:w-auto sm:justify-end sm:gap-3">
                    <div class="flex items-center gap-2">
                        <button
                            type="button"
                            class="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
                            :aria-label="dark ? 'Activer le mode clair' : 'Activer le mode sombre'"
                            @click="toggleTheme"
                        >
                            <svg v-if="dark" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
                            </svg>
                            <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1.5m0 15V21m9-9h-1.5m-15 0H3m15.364 6.364l-1.06-1.06M6.696 6.696l-1.06-1.06m12.728 0l-1.06 1.06M6.696 17.304l-1.06 1.06M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
                            </svg>
                        </button>
                        <a href="/login" class="hidden rounded-xl border border-transparent px-3 py-2 text-sm text-slate-600 transition hover:border-slate-200 hover:bg-white hover:text-slate-950 dark:text-slate-300 dark:hover:border-slate-700 dark:hover:bg-slate-900 dark:hover:text-white sm:inline-flex">Se connecter</a>
                    </div>
                    <a href="/register" class="inline-flex rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-700 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white">Créer un compte</a>
                </div>
            </div>
        </nav>

        <main class="mx-auto max-w-7xl px-4 pb-12 pt-6 sm:px-6 sm:pb-16 sm:pt-8 xl:max-w-[1400px]">
            <section class="grid gap-8 border-b border-slate-200 pb-10 dark:border-slate-800 lg:grid-cols-[0.84fr_1.16fr] lg:items-start lg:gap-10 lg:pb-14">
                <div class="max-w-xl">
                    <h1 class="mt-8 text-[26px] font-semibold tracking-tight text-slate-950 dark:text-white sm:mt-10 sm:text-[38px]">
                        Détecter un texte en quelques secondes.
                    </h1>
                    <p class="mt-3 max-w-lg text-sm leading-6 text-slate-600 dark:text-slate-300 sm:mt-4 sm:text-[15px]">
                        Collez un extrait, obtenez un score lisible et repérez les phrases à relire. Sans surcharge visuelle, sans étapes inutiles.
                    </p>

                    <div class="mt-5 flex flex-wrap gap-2 text-xs text-slate-600 dark:text-slate-300 sm:text-sm">
                        <span class="rounded-full border border-slate-200 bg-white px-3 py-1.5 dark:border-slate-700 dark:bg-slate-900">20 000 caractères</span>
                        <span class="rounded-full border border-slate-200 bg-white px-3 py-1.5 dark:border-slate-700 dark:bg-slate-900">Lecture phrase par phrase</span>
                        <span class="rounded-full border border-slate-200 bg-white px-3 py-1.5 dark:border-slate-700 dark:bg-slate-900">Compte optionnel</span>
                    </div>

                </div>

                <div
                    id="analyse"
                    ref="analysisCard"
                    class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-950 lg:sticky lg:top-24 lg:self-start"
                >
                    <div class="border-b border-slate-200 px-5 pb-5 pt-7 dark:border-slate-800">
                        <p class="text-[11px] font-medium uppercase tracking-[0.16em] text-slate-400 dark:text-slate-500">Analyse libre</p>
                        <h2 class="mt-2 text-lg font-semibold text-slate-950 dark:text-white">Détecter un texte</h2>
                        <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
                            Collez un extrait puis lancez l’analyse.
                        </p>
                    </div>

                    <div class="p-5">
                        <textarea
                            v-model="text"
                            rows="10"
                            :maxlength="maxChars"
                            placeholder="Collez votre texte ici..."
                            class="min-h-[240px] w-full resize-none rounded-xl border border-slate-200 bg-slate-50 px-4 py-4 text-[15px] leading-7 text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-slate-400 focus:bg-white dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:border-slate-500 dark:focus:bg-slate-900 sm:min-h-[300px]"
                        ></textarea>

                        <div class="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                            <div class="flex items-center justify-between gap-3 sm:justify-start">
                                <p class="text-sm font-medium text-slate-500 dark:text-slate-400">
                                    {{ charCount.toLocaleString() }} / {{ maxChars.toLocaleString() }} caractères
                                </p>
                                <button
                                    v-if="text"
                                    type="button"
                                    class="inline-flex items-center rounded-lg bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-100 dark:bg-slate-950 dark:text-slate-300 dark:hover:bg-slate-800"
                                    @click="clearText"
                                >
                                    Effacer
                                </button>
                            </div>

                            <button
                                type="button"
                                :disabled="!canAnalyze"
                                class="w-full rounded-lg bg-slate-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white dark:disabled:bg-slate-700 dark:disabled:text-slate-400 sm:w-auto"
                                @click="analyze"
                            >
                                <span v-if="loading">Analyse en cours...</span>
                                <span v-else>Analyser</span>
                            </button>
                        </div>

                        <p class="mt-3 text-xs text-slate-400 dark:text-slate-500">
                            Minimum {{ minChars }} caractères. L’analyse gratuite est limitée à {{ maxChars.toLocaleString() }} caractères.
                        </p>

                        <div v-if="error" class="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
                            {{ error }}
                        </div>
                    </div>
                </div>
            </section>

            <section
                v-if="result !== null || (sentences && sentences.length)"
                ref="resultsSection"
                id="resultats"
                class="mt-10 border-b border-slate-200 pb-10 dark:border-slate-800 sm:mt-12"
            >
                <div class="grid gap-4">
                    <div v-if="result !== null" class="rounded-2xl border border-slate-200 bg-slate-50 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                        <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                            <div>
                                <p class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">Lecture</p>
                                <p class="mt-1 text-sm font-medium text-slate-900 dark:text-white">{{ verdict }}</p>
                            </div>
                            <div class="grid grid-cols-2 gap-2 text-center sm:min-w-[220px]">
                                <div class="rounded-lg bg-white px-3 py-2 dark:bg-slate-950">
                                    <p class="text-xs text-slate-500 dark:text-slate-400">Humain</p>
                                    <p class="mt-1 text-xl font-semibold text-emerald-600">{{ humanPercent }}%</p>
                                </div>
                                <div class="rounded-lg bg-white px-3 py-2 dark:bg-slate-950">
                                    <p class="text-xs text-slate-500 dark:text-slate-400">IA</p>
                                    <p class="mt-1 text-xl font-semibold text-red-600">{{ aiPercent }}%</p>
                                </div>
                            </div>
                        </div>

                        <div class="mt-4 border-t border-slate-200 pt-4 dark:border-slate-800">
                            <p class="text-sm text-slate-600 dark:text-slate-300">
                                Vous voulez aller plus loin ? Connectez-vous pour analyser plus librement, retrouver vos analyses et accéder à une expérience complète.
                            </p>
                            <a
                                href="/login"
                                class="mt-3 inline-flex text-sm font-medium text-slate-900 underline underline-offset-4 transition hover:text-slate-600 dark:text-white dark:hover:text-slate-300"
                            >
                                Se connecter
                            </a>
                        </div>
                    </div>

                    <div v-if="sentences && sentences.length" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-950">
                        <p class="text-sm font-medium text-slate-900 dark:text-white">Détail des phrases</p>
                        <p class="mt-3 text-sm leading-8 text-slate-700 dark:text-slate-300">
                            <template v-for="(sentence, index) in sentences" :key="index">
                                <span
                                    class="rounded px-1 py-0.5"
                                    :class="sentenceBg(sentence.score)"
                                    :title="`Score IA : ${sentence.score}%`"
                                >{{ sentence.text }}</span>{{ ' ' }}
                            </template>
                        </p>
                    </div>
                </div>
            </section>

            <section id="faq" class="mt-10 sm:mt-14">
                <div class="max-w-3xl border-b border-slate-200 pb-4 dark:border-slate-800">
                    <p class="text-sm font-medium text-slate-500 dark:text-slate-400">FAQ</p>
                    <h2 class="mt-2 text-xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-2xl">Questions fréquentes</h2>
                </div>

                <div class="mt-6 rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-950">
                    <div class="border-b border-slate-200 p-4 dark:border-slate-800 sm:p-5">
                        <p class="text-sm font-semibold text-slate-900 dark:text-white">Faut-il un compte pour tester ?</p>
                        <p class="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">
                            Non. La landing permet déjà de coller un extrait et d’obtenir un résultat.
                        </p>
                    </div>
                    <div class="border-b border-slate-200 p-4 dark:border-slate-800 sm:p-5">
                        <p class="text-sm font-semibold text-slate-900 dark:text-white">Que montre le score ?</p>
                        <p class="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">
                            Le score indique un niveau de probabilité. Il aide à repérer des passages à relire, pas à prouver seul l’origine du texte.
                        </p>
                    </div>
                    <div class="border-b border-slate-200 p-4 dark:border-slate-800 sm:p-5">
                        <p class="text-sm font-semibold text-slate-900 dark:text-white">Pourquoi certaines phrases sont colorées ?</p>
                        <p class="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">
                            La coloration sert à localiser les segments qui semblent plus artificiels ou plus réguliers que le reste du texte.
                        </p>
                    </div>
                    <div class="p-4 sm:p-5">
                        <p class="text-sm font-semibold text-slate-900 dark:text-white">Quand créer un compte ?</p>
                        <p class="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">
                            Quand vous voulez aller plus loin avec l’historique, l’analyse de fichiers et un usage plus régulier.
                        </p>
                    </div>
                </div>
            </section>

            <footer class="mt-12 border-t border-slate-200 pt-8 dark:border-slate-800 sm:mt-16 sm:pt-10">
                <div class="flex items-center gap-3">
                    <span class="flex h-11 w-11 items-center justify-center rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
                        <span class="h-4 w-4 rounded-full bg-teal-500 dark:bg-cyan-400"></span>
                    </span>
                    <div>
                        <p class="text-base font-semibold text-slate-950 dark:text-white">ReinIA</p>
                        <p class="text-sm text-slate-500 dark:text-slate-400">Détection claire, lecture rapide.</p>
                    </div>
                </div>

                <div class="mt-8 flex flex-col gap-2 border-t border-slate-200 py-5 text-sm text-slate-500 dark:border-slate-800 dark:text-slate-400 sm:flex-row sm:items-center sm:justify-between">
                    <p>&copy; {{ currentYear }} ReinIA</p>
                    <p>Le score aide à relire un texte. Il ne remplace pas un jugement humain.</p>
                </div>
            </footer>
        </main>
    </div>
</template>
