<script setup>
/**
 * AppLayout — Main application shell with premium sidebar, mobile nav, and toast provider.
 */
import { ref, computed, onMounted, watch } from 'vue';
import { usePage, router } from '@inertiajs/vue3';
import axios from 'axios';
import ToastProvider from '../Components/ToastProvider.vue';

const page = usePage();
const user = computed(() => page.props.auth?.user);
const isSuperAdmin = computed(() => user.value?.role === 'superadmin');
const dark = ref(true);
const sidebarOpen = ref(false);
const desktopSidebarHidden = ref(false);
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
    
    const savedSidebar = localStorage.getItem('desktopSidebarHidden');
    if (savedSidebar === 'true') {
        desktopSidebarHidden.value = true;
    }

    applyTheme();
    loadRecentDetections();
});

watch(desktopSidebarHidden, (val) => {
    localStorage.setItem('desktopSidebarHidden', val);
});

function toggleTheme() {
    // Add transition class for smooth theme switch
    document.documentElement.classList.add('theme-transitioning');
    dark.value = !dark.value;
    localStorage.setItem('theme', dark.value ? 'dark' : 'light');
    applyTheme();
    setTimeout(() => document.documentElement.classList.remove('theme-transitioning'), 400);
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

function scoreBadgeClass(val) {
    if (val >= 75) return 'text-emerald-600 dark:text-emerald-400';
    if (val >= 50) return 'text-cyan-600 dark:text-cyan-400';
    if (val >= 25) return 'text-amber-600 dark:text-amber-400';
    return 'text-rose-600 dark:text-rose-400';
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

/* Navigation items for the sidebar/menu */
const navItems = [
    { label: 'Mon profil', href: '/profile', icon: 'M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z' },
    { label: 'Historique', href: '/history', icon: 'M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z' },
    { label: 'FAQ', href: '/faq', icon: 'M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z' },
];
</script>

<template>
    <div :class="dark ? 'dark' : ''">
        <div class="flex min-h-screen transition-colors duration-300 bg-zinc-50 dark:bg-[#0a0a0a]">

            <!-- Sidebar overlay (mobile) -->
            <transition
                enter-active-class="transition-opacity duration-300"
                enter-from-class="opacity-0"
                enter-to-class="opacity-100"
                leave-active-class="transition-opacity duration-200"
                leave-from-class="opacity-100"
                leave-to-class="opacity-0"
            >
                <div v-if="sidebarOpen" class="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden" @click="sidebarOpen = false"></div>
            </transition>

            <!-- ═══ Sidebar ═══ -->
            <aside
                class="fixed left-0 top-0 z-50 flex h-screen shrink-0 flex-col overflow-x-hidden overflow-y-auto transition-all duration-300 lg:sticky"
                :class="[
                    sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
                    desktopSidebarHidden ? 'w-[260px] lg:w-[68px]' : 'w-[260px]',
                    'bg-white/80 dark:bg-[#111111]/90 backdrop-blur-xl border-r border-zinc-200/50 dark:border-zinc-800/50'
                ]"
            >
                <!-- Header: logo + new analysis -->
                <div class="shrink-0 pb-1 pt-3" :class="desktopSidebarHidden ? 'px-3 lg:px-2' : 'px-3'">
                    <div class="mb-4 flex items-center justify-between px-1" :class="desktopSidebarHidden ? 'lg:flex-col lg:justify-center lg:gap-4' : ''">
                        <a href="/app" class="flex min-w-0 items-center gap-3 w-full" :class="desktopSidebarHidden ? 'lg:justify-center' : ''" @click="sidebarOpen = false">
                            <span class="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/20">
                                <svg class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
                                </svg>
                            </span>
                            <span class="min-w-0 transition-opacity" :class="desktopSidebarHidden ? 'lg:hidden' : 'lg:block'">
                                <span class="block font-display text-sm font-bold tracking-tight text-zinc-900 dark:text-white sm:text-base">ReinIA</span>
                                <span class="block text-[11px] text-zinc-500 dark:text-zinc-500">Détection & Humanisation</span>
                            </span>
                        </a>
                        <div class="flex items-center gap-1 shrink-0">
                            <!-- Desktop toggle -->
                            <button @click="desktopSidebarHidden = !desktopSidebarHidden" class="group hidden rounded-lg p-1 text-zinc-400 transition-colors hover:bg-zinc-100 dark:text-zinc-500 dark:hover:bg-zinc-800 lg:flex items-center justify-center cursor-pointer" title="Basculer la barre latérale">
                                <div class="relative flex h-5 w-5 items-center justify-center">
                                    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg" class="transition-colors group-hover:text-zinc-700 dark:group-hover:text-zinc-200" aria-hidden="true" style="flex-shrink: 0;"><path d="M16.5 4A1.5 1.5 0 0 1 18 5.5v9a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 2 14.5v-9A1.5 1.5 0 0 1 3.5 4zM7 15h9.5a.5.5 0 0 0 .5-.5v-9a.5.5 0 0 0-.5-.5H7zM3.5 5a.5.5 0 0 0-.5.5v9a.5.5 0 0 0 .5.5H6V5z"></path></svg>
                                </div>
                            </button>
                            <!-- Mobile close -->
                            <button @click="sidebarOpen = false" class="rounded-lg p-1 text-zinc-400 transition-colors hover:bg-zinc-100 dark:text-zinc-500 dark:hover:bg-zinc-800 lg:hidden cursor-pointer">
                                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                            </button>
                        </div>
                    </div>
                    <a
                        href="/app"
                        class="group flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200"
                        :class="[
                            isNewAnalysisActive()
                                ? 'bg-gradient-to-r from-indigo-500/10 to-purple-500/10 text-indigo-700 dark:from-indigo-500/15 dark:to-purple-500/15 dark:text-indigo-300 ring-1 ring-indigo-500/20'
                                : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800/60 border border-dashed border-zinc-300 dark:border-zinc-700 hover:border-zinc-400 dark:hover:border-zinc-600',
                            desktopSidebarHidden ? 'lg:justify-center' : ''
                        ]"
                        title="Nouvelle analyse"
                        @click="sidebarOpen = false"
                    >
                        <svg class="h-4 w-4 shrink-0 transition-transform duration-200 group-hover:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg>
                        <span :class="desktopSidebarHidden ? 'lg:hidden' : 'lg:block'">Nouvelle analyse</span>
                    </a>
                </div>

                <!-- Recent detections -->
                <div class="flex-1 overflow-y-auto overflow-x-hidden px-3 py-2 scrollbar-thin overflow-x-hidden whitespace-nowrap">
                    <p v-if="recentDetections.length && !desktopSidebarHidden" class="mb-2 px-2 text-[11px] font-semibold uppercase tracking-wider text-zinc-400 dark:text-zinc-600 hidden lg:block">Récent</p>
                    <div class="space-y-1">
                        <div
                            v-for="det in recentDetections"
                            :key="det.public_id || det.uuid || det.id"
                            class="group flex items-center gap-1 rounded-lg transition-all duration-200"
                            :class="[
                                desktopSidebarHidden ? 'lg:px-0 lg:justify-center' : 'px-1',
                                isRecentDetectionActive(det) ? 'bg-zinc-100 dark:bg-zinc-800/70' : 'hover:bg-zinc-50 dark:hover:bg-zinc-800/40'
                            ]"
                        >
                            <a
                                :href="analysisLink(det.public_id || det.uuid || det.id)"
                                class="flex min-w-0 flex-1 items-center gap-2.5 rounded-md py-1.5 text-[13px] transition-colors"
                                :class="[
                                    desktopSidebarHidden ? 'lg:justify-center lg:px-0' : 'px-2',
                                    isRecentDetectionActive(det) ? 'text-zinc-900 dark:text-white font-medium' : 'text-zinc-600 dark:text-zinc-400'
                                ]"
                                :title="det.text_excerpt"
                                @click="sidebarOpen = false"
                            >
                                <span class="flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-[11px] font-bold" :class="scoreBadgeClass(100 - det.ai_probability)">
                                    {{ Math.round(100 - det.ai_probability) }}
                                </span>
                                <span class="truncate" :class="desktopSidebarHidden ? 'lg:hidden' : 'lg:block'">{{ truncate(det.text_excerpt) }}</span>
                            </a>
                            <button
                                type="button"
                                class="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-zinc-400 opacity-0 transition-all duration-200 hover:bg-rose-50 hover:text-rose-500 group-hover:opacity-100 focus:opacity-100 dark:text-zinc-600 dark:hover:bg-rose-500/10 dark:hover:text-rose-400 cursor-pointer"
                                :class="desktopSidebarHidden ? 'lg:hidden' : ''"
                                title="Supprimer"
                                aria-label="Supprimer cette analyse"
                                @click.stop.prevent="requestDeleteRecentDetection(det)"
                            >
                                <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Bottom menu -->
                <div class="shrink-0 border-t border-zinc-200/50 dark:border-zinc-800/50">
                    <!-- User menu popup -->
                    <transition
                        enter-active-class="transition duration-200 ease-out"
                        enter-from-class="opacity-0 translate-y-2 scale-95"
                        enter-to-class="opacity-100 translate-y-0 scale-100"
                        leave-active-class="transition duration-150 ease-in"
                        leave-from-class="opacity-100"
                        leave-to-class="opacity-0 translate-y-2 scale-95"
                    >
                        <div v-if="userMenuOpen" class="mx-3 mb-1 overflow-hidden rounded-xl border border-zinc-200/80 bg-white shadow-xl dark:border-zinc-800 dark:bg-zinc-900">
                            <div class="border-b border-zinc-100 px-4 py-2.5 dark:border-zinc-800">
                                <p class="truncate text-xs text-zinc-400 dark:text-zinc-500">{{ user?.email }}</p>
                            </div>
                            <div class="py-1">
                                <a
                                    v-for="item in navItems"
                                    :key="item.href"
                                    :href="item.href"
                                    class="flex items-center gap-3 px-4 py-2 text-sm transition-colors"
                                    :class="isActivePath(item.href)
                                        ? 'bg-zinc-50 text-zinc-900 dark:bg-zinc-800 dark:text-white'
                                        : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800'"
                                    @click="sidebarOpen = false; userMenuOpen = false"
                                >
                                    <svg class="h-4 w-4 text-zinc-400 dark:text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                                        <path stroke-linecap="round" stroke-linejoin="round" :d="item.icon" />
                                    </svg>
                                    {{ item.label }}
                                </a>
                                <button @click="toggleTheme(); userMenuOpen = false" class="flex w-full items-center gap-3 px-4 py-2 text-sm text-zinc-600 transition-colors hover:bg-zinc-50 dark:text-zinc-400 dark:hover:bg-zinc-800 cursor-pointer">
                                    <svg v-if="dark" class="h-4 w-4 text-zinc-400 dark:text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" /></svg>
                                    <svg v-else class="h-4 w-4 text-zinc-400 dark:text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" /></svg>
                                    {{ dark ? 'Mode clair' : 'Mode sombre' }}
                                </button>
                                <a v-if="isSuperAdmin" href="/admin" class="flex items-center gap-3 px-4 py-2 text-sm text-zinc-600 transition-colors hover:bg-zinc-50 dark:text-zinc-400 dark:hover:bg-zinc-800" @click="sidebarOpen = false; userMenuOpen = false">
                                    <svg class="h-4 w-4 text-zinc-400 dark:text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 010-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                                    Administration
                                </a>
                            </div>
                            <div class="border-t border-zinc-100 py-1 dark:border-zinc-800">
                                <button @click="logout" class="flex w-full items-center gap-3 px-4 py-2 text-sm text-zinc-600 transition-colors hover:bg-zinc-50 dark:text-zinc-400 dark:hover:bg-zinc-800 cursor-pointer">
                                    <svg class="h-4 w-4 text-zinc-400 dark:text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" /></svg>
                                    Se déconnecter
                                </button>
                            </div>
                        </div>
                    </transition>

                    <!-- User bar -->
                    <button @click="userMenuOpen = !userMenuOpen" class="flex items-center transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-800/50 cursor-pointer" :class="desktopSidebarHidden ? 'lg:justify-center lg:py-4 w-full py-3 px-4' : 'w-full gap-3 px-4 py-3'">
                        <div class="shrink-0 flex items-center justify-center pointer-events-none">
                            <img v-if="user?.avatar_url" :src="user.avatar_url" :alt="user.name" class="h-8 w-8 rounded-full object-cover ring-2 ring-zinc-200 dark:ring-zinc-700" />
                            <div v-else class="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-xs font-semibold text-white shadow-sm">
                                {{ user?.name?.charAt(0).toUpperCase() }}
                            </div>
                        </div>
                        <div class="min-w-0 flex-1 text-left" :class="desktopSidebarHidden ? 'lg:hidden' : 'lg:block'">
                            <p class="truncate text-sm font-medium text-zinc-800 dark:text-zinc-200">{{ user?.name }}</p>
                            <p class="truncate text-[11px] text-zinc-400 dark:text-zinc-500">{{ user?.status || (isSuperAdmin ? 'Super Admin' : 'Utilisateur') }}</p>
                        </div>
                        <svg class="h-4 w-4 shrink-0 text-zinc-400 transition-transform dark:text-zinc-500" :class="[userMenuOpen ? 'rotate-180' : '', desktopSidebarHidden ? 'lg:hidden' : 'lg:block']" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 15L12 18.75 15.75 15m-7.5-6L12 5.25 15.75 9" />
                        </svg>
                    </button>
                </div>
            </aside>

            <!-- Click outside to close user menu -->
            <div v-if="userMenuOpen" class="fixed inset-0 z-40" @click="userMenuOpen = false"></div>

            <!-- Delete confirm dialog -->
            <transition
                enter-active-class="transition duration-200 ease-out"
                enter-from-class="opacity-0"
                enter-to-class="opacity-100"
                leave-active-class="transition duration-150 ease-in"
                leave-from-class="opacity-100"
                leave-to-class="opacity-0"
            >
                <div v-if="deleteDialogOpen" class="fixed inset-0 z-[60] flex items-center justify-center p-4">
                    <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeDeleteDialog"></div>
                    <div class="animate-scale-in relative w-full max-w-md rounded-2xl border border-zinc-200 bg-white p-6 shadow-2xl dark:border-zinc-800 dark:bg-zinc-900">
                        <div class="flex items-start gap-4">
                            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-rose-100 text-rose-600 dark:bg-rose-500/15 dark:text-rose-400">
                                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m0 3.75h.008v.008H12v-.008zm9-3.758c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z" />
                                </svg>
                            </div>
                            <div class="min-w-0 flex-1">
                                <h3 class="text-base font-semibold text-zinc-900 dark:text-zinc-100">Supprimer cette analyse ?</h3>
                                <p class="mt-1 text-sm leading-6 text-zinc-500 dark:text-zinc-400">
                                    Cette action retirera l'analyse de votre historique.
                                </p>
                                <p class="mt-3 rounded-xl bg-zinc-50 px-3 py-2 text-sm text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
                                    {{ truncate(detectionToDelete?.text_excerpt || '', 90) }}
                                </p>
                            </div>
                        </div>
                        <div class="mt-5 flex items-center justify-end gap-2">
                            <button
                                type="button"
                                class="inline-flex items-center rounded-lg border border-zinc-200 px-4 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800 cursor-pointer"
                                @click="closeDeleteDialog"
                            >
                                Annuler
                            </button>
                            <button
                                type="button"
                                class="inline-flex items-center rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-rose-500 cursor-pointer"
                                @click="confirmDeleteRecentDetection"
                            >
                                Supprimer
                            </button>
                        </div>
                    </div>
                </div>
            </transition>

            <!-- ═══ Main Content ═══ -->
            <div class="flex min-h-screen flex-1 flex-col overflow-hidden transition-all duration-300 relative">
                <!-- Mobile header -->
                <header class="flex h-12 shrink-0 items-center justify-between border-b border-zinc-200/50 bg-white/80 px-4 backdrop-blur-lg dark:border-zinc-800/50 dark:bg-zinc-900/80 lg:hidden">
                    <button @click="sidebarOpen = true" class="rounded-lg p-1.5 text-zinc-500 transition-colors hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800 cursor-pointer">
                        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" /></svg>
                    </button>
                    <span class="font-display text-sm font-bold text-zinc-800 dark:text-zinc-200">ReinIA</span>
                    <div class="w-8"></div>
                </header>

                <main class="flex-1 bg-zinc-50 dark:bg-[#0a0a0a] min-w-0">
                    <slot />
                </main>
            </div>
        </div>

        <!-- Global Toast Provider -->
        <ToastProvider />
    </div>
</template>
