<script setup>
defineProps({
    percent: { type: Number, default: 0 },
    label: { type: String, default: 'Analyse en cours...' },
});
</script>

<template>
    <transition enter-active-class="transition duration-300 ease-out" enter-from-class="opacity-0 scale-95" enter-to-class="opacity-100 scale-100" leave-active-class="transition duration-200 ease-in" leave-from-class="opacity-100 scale-100" leave-to-class="opacity-0 scale-95">
        <div class="rounded-2xl border overflow-hidden bg-white dark:bg-slate-900/50 border-slate-200 dark:border-slate-700/60 shadow-sm">
            <div class="p-6 sm:p-8">
                <div class="flex items-center gap-6">
                    <!-- Circular progress -->
                    <div class="relative w-20 h-20 shrink-0">
                        <svg class="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
                            <circle cx="40" cy="40" r="34" fill="none" stroke-width="6" class="stroke-slate-100 dark:stroke-slate-800" />
                            <circle cx="40" cy="40" r="34" fill="none" stroke-width="6" stroke-linecap="round"
                                class="stroke-blue-500 transition-all duration-300 ease-out"
                                :stroke-dasharray="`${(percent / 100) * 213.6} 213.6`"
                            />
                        </svg>
                        <div class="absolute inset-0 flex items-center justify-center">
                            <span class="text-lg font-bold tabular-nums text-slate-800 dark:text-white">{{ Math.round(percent) }}<span class="text-xs text-slate-400">%</span></span>
                        </div>
                    </div>
                    <!-- Progress info -->
                    <div class="flex-1 min-w-0">
                        <p class="text-base font-semibold text-slate-800 dark:text-white">Analyse en cours</p>
                        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1 truncate">{{ label }}</p>
                        <div class="mt-3 w-full h-2 rounded-full overflow-hidden bg-slate-100 dark:bg-slate-800">
                            <div class="h-full rounded-full bg-gradient-to-r from-blue-500 to-violet-500 transition-all duration-300 ease-out relative" :style="{ width: percent + '%' }">
                                <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </transition>
</template>
