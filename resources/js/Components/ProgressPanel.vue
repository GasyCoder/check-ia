<script setup>
defineProps({
    percent: { type: Number, default: 0 },
    label: { type: String, default: 'Analyse en cours...' },
});
</script>

<template>
    <transition enter-active-class="transition duration-300 ease-out" enter-from-class="opacity-0 scale-95" enter-to-class="opacity-100 scale-100" leave-active-class="transition duration-200 ease-in" leave-from-class="opacity-100 scale-100" leave-to-class="opacity-0 scale-95">
        <div class="overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900/90">
            <div class="p-6 sm:p-8">
                <div class="flex flex-col gap-5 sm:flex-row sm:items-center">
                    <div class="shrink-0 rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-950">
                        <p class="text-sm text-zinc-500 dark:text-zinc-400">Progression</p>
                        <p class="mt-1 text-2xl font-semibold text-zinc-950 dark:text-zinc-50">{{ Math.round(percent) }}%</p>
                    </div>

                    <div class="min-w-0 flex-1">
                        <p class="text-sm font-semibold text-zinc-950 dark:text-zinc-50">Analyse en cours</p>
                        <p class="mt-1 truncate text-sm text-zinc-500 dark:text-zinc-400">{{ label }}</p>
                        <div class="mt-4 h-2 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                            <div class="relative h-full rounded-full bg-zinc-900 transition-all duration-300 ease-out" :style="{ width: percent + '%' }">
                                <div class="absolute inset-0 animate-shimmer bg-gradient-to-r from-transparent via-white/20 to-transparent"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </transition>
</template>
