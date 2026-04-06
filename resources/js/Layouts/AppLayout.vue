<script setup>
import { ref, computed, onMounted } from 'vue';
import { usePage, router } from '@inertiajs/vue3';
import axios from 'axios';

const page = usePage();
const user = computed(() => page.props.auth?.user);
const isSuperAdmin = computed(() => user.value?.role === 'superadmin');
const dark = ref(true);
const sidebarOpen = ref(false);
const userMenuOpen = ref(false);
const recentDetections = ref([]);
const deleteDialogOpen = ref(false);
const detectionToDelete = ref(null);
const currentPath = computed(() => {
    const url = page.url || '';
    return url.split('?')[0] || '/app';
});
const currentAnalysisRef = computed(() => {
    const url = page.url || '';
    const queryString = url.includes('?') ? url.split('?')[1] : '';
    const params = new URLSearchParams(queryString);

    return params.get('analysis') || params.get('from_history') || null;
});

onMounted(() => {
    const saved = localStorage.getItem('theme');
    dark.value = saved ? saved === 'dark' : true;
    applyTheme();
    loadRecentDetections();
});

function toggleTheme() {
    dark.value = !dark.value;
    localStorage.setItem('theme', dark.value ? 'dark' : 'light');
    applyTheme();
}

function applyTheme() {
    document.documentElement.classList.toggle('dark', dark.value);
}

function logout() {
    router.post('/logout');
}

async function loadRecentDetections() {
    try {
        const res = await axios.get('/history/sidebar');
        recentDetections.value = res.data;
    } catch {
        // ignore
    }
}

function truncate(text, len = 38) {
    return text.length > len ? text.substring(0, len) + '...' : text;
}

function scoreColor(val) {
    if (val >= 75) return 'bg-red-500';
    if (val >= 50) return 'bg-orange-500';
    if (val >= 25) return 'bg-amber-500';
    return 'bg-emerald-500';
}

function analysisLink(reference) {
    return reference ? `/app?analysis=${reference}` : '/app';
}

function isActivePath(path) {
    return currentPath.value === path;
}

function isNewAnalysisActive() {
    return currentPath.value === '/app' && !currentAnalysisRef.value;
}

function isRecentDetectionActive(detection) {
    const reference = detection?.public_id || detection?.uuid || detection?.id;

    return currentPath.value === '/app'
        && currentAnalysisRef.value
        && String(reference) === String(currentAnalysisRef.value);
}

function requestDeleteRecentDetection(detection) {
    if (!detection) return;

    detectionToDelete.value = detection;
    deleteDialogOpen.value = true;
}

function closeDeleteDialog() {
    deleteDialogOpen.value = false;
    detectionToDelete.value = null;
}

async function confirmDeleteRecentDetection() {
    const reference = detectionToDelete.value?.public_id || detectionToDelete.value?.uuid || detectionToDelete.value?.id;

    if (!reference) return;

    try {
        await axios.delete(`/history/${reference}`);
        recentDetections.value = recentDetections.value.filter(
            (det) => (det.public_id || det.uuid || det.id) !== reference,
        );

        const params = new URLSearchParams(window.location.search);
        if (params.get('analysis') === String(reference) || params.get('from_history') === String(reference)) {
            router.get('/app');
        }
    } catch {
        // keep dialog closed; failure feedback stays minimal and consistent
    } finally {
        closeDeleteDialog();
    }
}
</script>

<template>
    <div :class="dark ? 'dark' : ''">
        <div class="min-h-screen flex transition-colors duration-300 bg-slate-50 dark:bg-[#212121]">

            <!-- Sidebar overlay (mobile) -->
            <div v-if="sidebarOpen" class="fixed inset-0 bg-black/60 z-40 lg:hidden" @click="sidebarOpen = false"></div>

            <!-- Sidebar -->
            <aside
                class="fixed lg:sticky top-0 left-0 z-50 h-screen w-[260px] flex flex-col transition-transform duration-300 bg-[#f9f9f9] dark:bg-[#171717] lg:translate-x-0 overflow-hidden"
                :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'"
            >
                <!-- Header: logo + new analysis -->
                <div class="px-3 pt-3 pb-1 shrink-0">
                    <div class="flex items-center justify-between mb-3 px-1">
                        <a href="/app" class="flex min-w-0 items-center gap-3" @click="sidebarOpen = false">
                            <span class="flex h-10 w-10 items-center justify-center rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
                                <span class="h-4 w-4 rounded-full bg-teal-500 dark:bg-cyan-400"></span>
                            </span>
                            <span class="min-w-0">
                                <span class="block text-sm font-semibold tracking-tight text-slate-950 dark:text-white sm:text-base">ReinIA</span>
                                <span class="block text-xs text-slate-500 dark:text-slate-400">Détection de texte IA</span>
                            </span>
                        </a>
                        <button @click="sidebarOpen = false" class="lg:hidden p-1 rounded-md text-slate-400 dark:text-[#999] hover:bg-slate-200 dark:hover:bg-[#2a2a2a]">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                        </button>
                    </div>
                    <a
                        href="/app"
                        class="flex items-center gap-2.5 w-full px-3 py-2.5 rounded-lg text-sm font-medium transition-all border border-dashed"
                        :class="isNewAnalysisActive()
                            ? 'border-slate-400 bg-slate-200/70 text-slate-900 dark:border-[#666] dark:bg-[#2a2a2a] dark:text-white'
                            : 'text-slate-600 dark:text-[#ccc] border-slate-300 dark:border-[#444] hover:border-slate-400 dark:hover:border-[#666] hover:bg-slate-200/50 dark:hover:bg-[#2a2a2a]'"
                        @click="sidebarOpen = false"
                    >
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg>
                        Nouvelle analyse
                    </a>
                </div>

                <!-- Recent detections -->
                <div class="flex-1 overflow-y-auto px-3 py-2">
                    <div class="space-y-px">
                        <div
                            v-for="det in recentDetections"
                            :key="det.public_id || det.uuid || det.id"
                            class="group flex items-center gap-1 rounded-lg px-1 py-1 transition-colors"
                            :class="isRecentDetectionActive(det) ? 'bg-slate-200/70 dark:bg-[#2a2a2a]' : 'hover:bg-slate-200/70 dark:hover:bg-[#2a2a2a]'"
                        >
                            <a
                                :href="analysisLink(det.public_id || det.uuid || det.id)"
                                class="flex min-w-0 flex-1 items-center gap-2.5 rounded-md px-2 py-1 text-[13px] transition-colors"
                                :class="isRecentDetectionActive(det) ? 'text-slate-900 dark:text-white' : 'text-slate-600 dark:text-[#b4b4b4]'"
                                @click="sidebarOpen = false"
                            >
                                <span class="w-2 h-2 rounded-full shrink-0" :class="scoreColor(det.ai_probability)"></span>
                                <span class="truncate">{{ truncate(det.text_excerpt) }}</span>
                            </a>
                            <button
                                type="button"
                                class="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-slate-400 opacity-0 transition hover:bg-red-50 hover:text-red-500 group-hover:opacity-100 focus:opacity-100 dark:text-[#777] dark:hover:bg-red-500/10 dark:hover:text-red-400 cursor-pointer"
                                title="Supprimer"
                                aria-label="Supprimer cette analyse"
                                @click.stop.prevent="requestDeleteRecentDetection(det)"
                            >
                                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Bottom menu -->
                <div class="shrink-0 border-t border-slate-200 dark:border-[#2a2a2a]">
                    <!-- User menu popup -->
                    <transition
                        enter-active-class="transition duration-150 ease-out"
                        enter-from-class="opacity-0 translate-y-2"
                        enter-to-class="opacity-100 translate-y-0"
                        leave-active-class="transition duration-100 ease-in"
                        leave-from-class="opacity-100"
                        leave-to-class="opacity-0 translate-y-2"
                    >
                        <div v-if="userMenuOpen" class="mx-3 mb-1 rounded-xl border bg-white dark:bg-[#2a2a2a] border-slate-200 dark:border-[#3a3a3a] shadow-lg overflow-hidden">
                            <div class="px-4 py-2.5 border-b border-slate-100 dark:border-[#3a3a3a]">
                                <p class="text-xs text-slate-400 dark:text-[#888] truncate">{{ user?.email }}</p>
                            </div>
                            <div class="py-1">
                                <a href="/profile" class="flex items-center gap-3 px-4 py-2 text-sm transition-colors text-slate-700 dark:text-[#ccc] hover:bg-slate-50 dark:hover:bg-[#333]" @click="sidebarOpen = false; userMenuOpen = false">
                                    <svg class="w-4 h-4 text-slate-400 dark:text-[#888]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" /></svg>
                                    Mon profil
                                </a>
                                <a
                                    href="/history"
                                    class="flex items-center gap-3 px-4 py-2 text-sm transition-colors"
                                    :class="isActivePath('/history')
                                        ? 'bg-slate-100 text-slate-900 dark:bg-[#333] dark:text-white'
                                        : 'text-slate-700 dark:text-[#ccc] hover:bg-slate-50 dark:hover:bg-[#333]'"
                                    @click="sidebarOpen = false; userMenuOpen = false"
                                >
                                    <svg class="w-4 h-4 text-slate-400 dark:text-[#888]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                    Historique
                                </a>
                                <a href="/faq" class="flex items-center gap-3 px-4 py-2 text-sm transition-colors text-slate-700 dark:text-[#ccc] hover:bg-slate-50 dark:hover:bg-[#333]" @click="sidebarOpen = false; userMenuOpen = false">
                                    <svg class="w-4 h-4 text-slate-400 dark:text-[#888]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" /></svg>
                                    FAQ
                                </a>
                                <button @click="toggleTheme(); userMenuOpen = false" class="w-full flex items-center gap-3 px-4 py-2 text-sm transition-colors text-slate-700 dark:text-[#ccc] hover:bg-slate-50 dark:hover:bg-[#333] cursor-pointer">
                                    <svg v-if="dark" class="w-4 h-4 text-slate-400 dark:text-[#888]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" /></svg>
                                    <svg v-else class="w-4 h-4 text-slate-400 dark:text-[#888]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" /></svg>
                                    {{ dark ? 'Mode clair' : 'Mode sombre' }}
                                </button>
                                <a v-if="isSuperAdmin" href="/admin" class="flex items-center gap-3 px-4 py-2 text-sm transition-colors text-slate-700 dark:text-[#ccc] hover:bg-slate-50 dark:hover:bg-[#333]" @click="sidebarOpen = false; userMenuOpen = false">
                                    <svg class="w-4 h-4 text-slate-400 dark:text-[#888]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 010-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                                    Administration
                                </a>
                            </div>
                            <div class="border-t border-slate-100 dark:border-[#3a3a3a] py-1">
                                <button @click="logout" class="w-full flex items-center gap-3 px-4 py-2 text-sm transition-colors text-slate-700 dark:text-[#ccc] hover:bg-slate-50 dark:hover:bg-[#333] cursor-pointer">
                                    <svg class="w-4 h-4 text-slate-400 dark:text-[#888]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" /></svg>
                                    Se déconnecter
                                </button>
                            </div>
                        </div>
                    </transition>

                    <!-- User bar -->
                    <button @click="userMenuOpen = !userMenuOpen" class="w-full flex items-center gap-3 px-4 py-3 transition-colors hover:bg-slate-200/50 dark:hover:bg-[#2a2a2a] cursor-pointer">
                        <div class="shrink-0">
                            <img v-if="user?.avatar_url" :src="user.avatar_url" :alt="user.name" class="w-8 h-8 rounded-full object-cover" />
                            <div v-else class="w-8 h-8 rounded-full bg-slate-300 dark:bg-[#555] flex items-center justify-center text-white dark:text-[#ddd] text-xs font-semibold">
                                {{ user?.name?.charAt(0).toUpperCase() }}
                            </div>
                        </div>
                        <div class="flex-1 min-w-0 text-left">
                            <p class="text-sm font-medium truncate text-slate-800 dark:text-[#ececec]">{{ user?.name }}</p>
                            <p class="text-[11px] truncate text-slate-400 dark:text-[#888]">{{ user?.status || (isSuperAdmin ? 'Super Admin' : 'Utilisateur') }}</p>
                        </div>
                        <svg class="w-4 h-4 text-slate-400 dark:text-[#666] shrink-0 transition-transform" :class="userMenuOpen ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 9.75L12 5.25l4.5 4.5" />
                            <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 14.25L12 18.75l4.5-4.5" />
                        </svg>
                    </button>
                </div>
            </aside>

            <!-- Click outside to close user menu -->
            <div v-if="userMenuOpen" class="fixed inset-0 z-40" @click="userMenuOpen = false"></div>

            <!-- Delete confirm dialog -->
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
                    <div class="relative w-full max-w-md rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl dark:border-[#3a3a3a] dark:bg-[#1f1f1f]">
                        <div class="flex items-start gap-3">
                            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400">
                                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m0 3.75h.008v.008H12v-.008zm9-3.758c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z" />
                                </svg>
                            </div>
                            <div class="min-w-0 flex-1">
                                <h3 class="text-base font-semibold text-slate-900 dark:text-[#f3f3f3]">Supprimer cette analyse ?</h3>
                                <p class="mt-1 text-sm leading-6 text-slate-500 dark:text-[#a3a3a3]">
                                    Cette action retirera l’analyse de votre historique.
                                </p>
                                <p class="mt-3 rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:bg-[#262626] dark:text-[#d4d4d4]">
                                    {{ truncate(detectionToDelete?.text_excerpt || '', 90) }}
                                </p>
                            </div>
                        </div>
                        <div class="mt-5 flex items-center justify-end gap-2">
                            <button
                                type="button"
                                class="inline-flex items-center rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-[#3a3a3a] dark:text-[#d4d4d4] dark:hover:bg-[#2a2a2a] cursor-pointer"
                                @click="closeDeleteDialog"
                            >
                                Annuler
                            </button>
                            <button
                                type="button"
                                class="inline-flex items-center rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-500 cursor-pointer"
                                @click="confirmDeleteRecentDetection"
                            >
                                Supprimer
                            </button>
                        </div>
                    </div>
                </div>
            </transition>

            <!-- Main -->
            <div class="flex-1 flex flex-col min-h-screen">
                <!-- Mobile header -->
                <header class="h-12 flex items-center justify-between px-4 lg:hidden bg-[#f9f9f9] dark:bg-[#171717]">
                    <button @click="sidebarOpen = true" class="p-1.5 rounded-lg text-slate-500 dark:text-[#999] hover:bg-slate-200 dark:hover:bg-[#2a2a2a]">
                        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" /></svg>
                    </button>
                    <span class="text-sm font-semibold text-slate-800 dark:text-[#ececec]">ReinIA</span>
                    <div class="w-8"></div>
                </header>

                <main class="flex-1 bg-white dark:bg-[#212121]">
                    <slot />
                </main>
            </div>
        </div>
    </div>
</template>
