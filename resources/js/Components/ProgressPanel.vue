<script setup>
/**
 * ProgressPanel — Premium loading indicator with orbital animation and typing effect.
 */
defineProps({
    percent: { type: Number, default: 0 },
    label: { type: String, default: 'Analyse en cours...' },
});
</script>

<template>
    <transition enter-active-class="transition duration-300 ease-out" enter-from-class="opacity-0 scale-95" enter-to-class="opacity-100 scale-100" leave-active-class="transition duration-200 ease-in" leave-from-class="opacity-100 scale-100" leave-to-class="opacity-0 scale-95">
        <div class="overflow-hidden rounded-xl border border-zinc-200/60 bg-white shadow-sm dark:border-zinc-800/60 dark:bg-zinc-900/80">
            <div class="p-6 sm:p-8">
                <div class="flex flex-col gap-5 sm:flex-row sm:items-center">
                    <!-- Orbital spinner -->
                    <div class="relative flex h-16 w-16 shrink-0 items-center justify-center self-center sm:self-auto">
                        <!-- Outer ring -->
                        <div class="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-indigo-500 dark:border-t-indigo-400" style="animation-duration: 2s"></div>
                        <!-- Inner ring -->
                        <div class="absolute inset-2 animate-spin rounded-full border-2 border-transparent border-b-purple-500 dark:border-b-purple-400" style="animation-duration: 1.5s; animation-direction: reverse"></div>
                        <!-- Center percentage -->
                        <span class="font-display text-sm font-bold tabular-nums text-zinc-900 dark:text-zinc-100">{{ Math.round(percent) }}<span class="text-[10px] text-zinc-400">%</span></span>
                    </div>

                    <div class="min-w-0 flex-1">
                        <div class="flex items-center gap-2">
                            <p class="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Analyse en cours</p>
                            <span class="typing-dots text-indigo-500">
                                <span></span><span></span><span></span>
                            </span>
                        </div>
                        <p class="mt-1 truncate text-sm text-zinc-500 dark:text-zinc-400">{{ label }}</p>

                        <!-- Progress bar -->
                        <div class="mt-4 h-1.5 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                            <div
                                class="relative h-full rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500 bg-[length:200%_100%] transition-[width] duration-300 ease-out"
                                :style="{ width: percent + '%' }"
                            >
                                <div class="absolute inset-0 animate-shimmer bg-gradient-to-r from-transparent via-white/25 to-transparent"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </transition>
</template>
