<script setup>
import { ref, watch } from 'vue';
import { router } from '@inertiajs/vue3';
import AppLayout from '../Layouts/AppLayout.vue';

const props = defineProps({
    detections: Object,
    filters: Object,
});

const search = ref(props.filters?.search || '');
const from = ref(props.filters?.from || '');
const to = ref(props.filters?.to || '');
const deleteDialogOpen = ref(false);
const detectionToDelete = ref(null);
let searchTimeout = null;

function analysisLink(reference) {
    return reference ? `/app?analysis=${reference}` : '/app';
}

function exportUrl(format) {
    const params = new URLSearchParams();

    if (search.value) params.set('search', search.value);
    if (from.value) params.set('from', from.value);
    if (to.value) params.set('to', to.value);

    const query = params.toString();

    return `/history/export/${format}${query ? `?${query}` : ''}`;
}

function applyFilters() {
    const params = {};
    if (search.value) params.search = search.value;
    if (from.value) params.from = from.value;
    if (to.value) params.to = to.value;
    router.get('/history', params, { preserveState: true, preserveScroll: true });
}

watch(search, () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(applyFilters, 400);
});

function clearFilters() {
    search.value = '';
    from.value = '';
    to.value = '';
    router.get('/history', {}, { preserveState: true });
}

function requestDeleteDetection(detection) {
    detectionToDelete.value = detection;
    deleteDialogOpen.value = true;
}

function closeDeleteDialog() {
    deleteDialogOpen.value = false;
    detectionToDelete.value = null;
}

function confirmDeleteDetection() {
    const reference = detectionToDelete.value?.public_id || detectionToDelete.value?.uuid || detectionToDelete.value?.id;

    if (!reference) {
        closeDeleteDialog();
        return;
    }

    router.delete(`/history/${reference}`, {
        preserveScroll: true,
        onFinish: closeDeleteDialog,
    });
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('fr-FR', {
        day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
    });
}

function probabilityColor(val) {
    if (val >= 75) return 'text-red-500 bg-red-50 dark:text-red-400 dark:bg-red-500/10 border-red-200 dark:border-red-500/20';
    if (val >= 50) return 'text-orange-500 bg-orange-50 dark:text-orange-400 dark:bg-orange-500/10 border-orange-200 dark:border-orange-500/20';
    if (val >= 25) return 'text-amber-500 bg-amber-50 dark:text-amber-400 dark:bg-amber-500/10 border-amber-200 dark:border-amber-500/20';
    return 'text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-500/10 border-emerald-200 dark:border-emerald-500/20';
}

function probabilityLabel(val) {
    if (val >= 75) return 'IA';
    if (val >= 50) return 'Probable IA';
    if (val >= 25) return 'Mixte';
    return 'Humain';
}

const hasFilters = () => search.value || from.value || to.value;
</script>

<template>
    <AppLayout>
        <div class="max-w-5xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
            <!-- Header -->
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
                <div>
                    <h1 class="text-3xl font-bold text-slate-900 dark:text-white">Historique</h1>
                    <p class="mt-1 text-slate-500 dark:text-slate-400">{{ detections.total || 0 }} analyse(s) au total</p>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                    <span class="text-xs font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500">Exporter</span>
                    <a
                        :href="exportUrl('json')"
                        class="inline-flex items-center rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                    >
                        JSON
                    </a>
                    <a
                        :href="exportUrl('csv')"
                        class="inline-flex items-center rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                    >
                        CSV
                    </a>
                    <a
                        :href="exportUrl('txt')"
                        class="inline-flex items-center rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                    >
                        TXT
                    </a>
                </div>
            </div>

            <!-- Filters -->
            <div class="rounded-xl border p-4 mb-6 bg-white dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/50">
                <div class="flex flex-col sm:flex-row gap-3">
                    <!-- Search -->
                    <div class="relative flex-1">
                        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" /></svg>
                        <input
                            v-model="search"
                            type="text"
                            placeholder="Rechercher dans les analyses..."
                            class="w-full text-sm pl-10 pr-4 py-2.5 rounded-lg border bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-600/50 text-slate-800 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition"
                        />
                    </div>

                    <!-- Date from -->
                    <div class="flex items-center gap-2">
                        <label class="text-xs text-slate-500 dark:text-slate-400 shrink-0">Du</label>
                        <input
                            v-model="from"
                            @change="applyFilters"
                            type="date"
                            class="text-sm px-3 py-2.5 rounded-lg border bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-600/50 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition"
                        />
                    </div>

                    <!-- Date to -->
                    <div class="flex items-center gap-2">
                        <label class="text-xs text-slate-500 dark:text-slate-400 shrink-0">Au</label>
                        <input
                            v-model="to"
                            @change="applyFilters"
                            type="date"
                            class="text-sm px-3 py-2.5 rounded-lg border bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-600/50 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition"
                        />
                    </div>

                    <!-- Clear -->
                    <button
                        v-if="hasFilters()"
                        @click="clearFilters"
                        class="text-xs px-3 py-2.5 rounded-lg border transition-colors text-slate-500 border-slate-200 dark:border-slate-600/50 hover:text-red-500 hover:border-red-300 dark:hover:border-red-500/30 shrink-0"
                    >
                        Effacer
                    </button>
                </div>
            </div>

            <!-- Empty state -->
            <div v-if="!detections.data.length" class="text-center py-20">
                <div class="w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center bg-slate-100 dark:bg-slate-800">
                    <svg v-if="hasFilters()" class="w-8 h-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" /></svg>
                    <svg v-else class="w-8 h-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                </div>
                <p class="text-lg font-medium text-slate-600 dark:text-slate-400">
                    {{ hasFilters() ? 'Aucun résultat trouvé' : 'Aucune analyse pour le moment' }}
                </p>
                <p class="text-sm mt-1 text-slate-400 dark:text-slate-500">
                    {{ hasFilters() ? 'Essayez avec d\'autres filtres' : 'Lancez votre première vérification !' }}
                </p>
                <a v-if="!hasFilters()" href="/" class="inline-flex items-center gap-2 mt-6 px-5 py-2.5 rounded-xl text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 transition-all shadow-lg shadow-blue-500/20">
                    Lancer une analyse
                </a>
            </div>

            <!-- Detections list -->
            <div v-else class="space-y-3">
                <div
                    v-for="detection in detections.data"
                    :key="detection.public_id || detection.uuid || detection.id"
                    class="group rounded-xl border p-4 sm:p-5 transition-all hover:shadow-md bg-white dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/50 hover:border-slate-300 dark:hover:border-slate-600/50"
                >
                    <div class="flex items-start gap-4">
                        <!-- Score badge -->
                        <div class="shrink-0 w-16 h-16 rounded-xl border flex flex-col items-center justify-center" :class="probabilityColor(detection.ai_probability)">
                            <span class="text-lg font-bold leading-none">{{ Math.round(detection.ai_probability) }}%</span>
                            <span class="text-[10px] font-medium mt-0.5 opacity-75">{{ probabilityLabel(detection.ai_probability) }}</span>
                        </div>

                        <!-- Content -->
                        <div class="flex-1 min-w-0">
                            <p class="text-sm leading-relaxed line-clamp-2 text-slate-700 dark:text-slate-300">{{ detection.text_excerpt }}</p>
                            <div class="flex items-center gap-3 mt-2">
                                <span class="text-xs text-slate-400 dark:text-slate-500">{{ formatDate(detection.created_at) }}</span>
                                <span v-if="detection.file_name" class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-700/50 text-slate-500 dark:text-slate-400">
                                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>
                                    {{ detection.file_name }}
                                </span>
                            </div>
                        </div>

                        <!-- Actions -->
                        <div class="shrink-0 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">
                            <a :href="analysisLink(detection.public_id || detection.uuid || detection.id)" class="p-2 rounded-lg transition-colors text-slate-400 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-500/10" title="Reprendre">
                                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" /></svg>
                            </a>
                            <button
                                @click="requestDeleteDetection(detection)"
                                class="p-2 rounded-lg transition-all text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 cursor-pointer"
                                title="Supprimer"
                            >
                                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" /></svg>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Pagination -->
            <div v-if="detections.last_page > 1" class="mt-8 flex items-center justify-center gap-1">
                <template v-for="link in detections.links" :key="link.label">
                    <a v-if="link.url" :href="link.url" class="px-3 py-1.5 rounded-lg text-sm transition-colors" :class="link.active ? 'bg-blue-600 text-white' : 'text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'" v-html="link.label" />
                    <span v-else class="px-3 py-1.5 text-sm text-slate-300 dark:text-slate-600" v-html="link.label" />
                </template>
            </div>

            <transition
                enter-active-class="transition duration-150 ease-out"
                enter-from-class="opacity-0"
                enter-to-class="opacity-100"
                leave-active-class="transition duration-100 ease-in"
                leave-from-class="opacity-100"
                leave-to-class="opacity-0"
            >
                <div v-if="deleteDialogOpen" class="fixed inset-0 z-[60] flex items-center justify-center p-4">
                    <div class="absolute inset-0 bg-black/50" @click="closeDeleteDialog"></div>
                    <div class="relative w-full max-w-md rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl dark:border-slate-700/50 dark:bg-slate-900">
                        <div class="flex items-start gap-3">
                            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400">
                                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m0 3.75h.008v.008H12v-.008zm9-3.758c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z" />
                                </svg>
                            </div>
                            <div class="min-w-0 flex-1">
                                <h3 class="text-base font-semibold text-slate-900 dark:text-white">Supprimer cette analyse ?</h3>
                                <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
                                    Cette action retirera définitivement l’analyse de votre historique.
                                </p>
                                <p class="mt-3 rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:bg-slate-800/70 dark:text-slate-300">
                                    {{ detectionToDelete?.text_excerpt }}
                                </p>
                            </div>
                        </div>
                        <div class="mt-5 flex items-center justify-end gap-2">
                            <button
                                type="button"
                                class="inline-flex items-center rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 cursor-pointer"
                                @click="closeDeleteDialog"
                            >
                                Annuler
                            </button>
                            <button
                                type="button"
                                class="inline-flex items-center rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-500 cursor-pointer"
                                @click="confirmDeleteDetection"
                            >
                                Supprimer
                            </button>
                        </div>
                    </div>
                </div>
            </transition>
        </div>
    </AppLayout>
</template>
