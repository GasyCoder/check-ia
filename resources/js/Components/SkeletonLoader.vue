<script setup>
/**
 * SkeletonLoader — Animated placeholder for loading states.
 *
 * Props:
 *   type: 'text' | 'card' | 'gauge' | 'result' — preset layout
 *   lines: number — number of text lines (for type='text')
 *   className: string — additional CSS classes
 */
defineProps({
    type: { type: String, default: 'text', validator: (v) => ['text', 'card', 'gauge', 'result'].includes(v) },
    lines: { type: Number, default: 3 },
    className: { type: String, default: '' },
});
</script>

<template>
    <!-- Text skeleton -->
    <div v-if="type === 'text'" class="space-y-3" :class="className">
        <div
            v-for="i in lines"
            :key="i"
            class="skeleton-line h-3.5 rounded-md"
            :style="{ width: i === lines ? '65%' : i % 2 === 0 ? '85%' : '100%', animationDelay: `${i * 100}ms` }"
        ></div>
    </div>

    <!-- Card skeleton -->
    <div v-else-if="type === 'card'" class="rounded-xl border border-zinc-200/60 p-6 dark:border-zinc-800/60" :class="className">
        <div class="flex items-start gap-4">
            <div class="skeleton-line h-12 w-12 shrink-0 rounded-xl"></div>
            <div class="flex-1 space-y-3">
                <div class="skeleton-line h-4 w-2/3 rounded-md"></div>
                <div class="skeleton-line h-3 w-full rounded-md" style="animation-delay: 100ms"></div>
                <div class="skeleton-line h-3 w-4/5 rounded-md" style="animation-delay: 200ms"></div>
            </div>
        </div>
    </div>

    <!-- Gauge skeleton -->
    <div v-else-if="type === 'gauge'" class="flex flex-col items-center gap-4" :class="className">
        <div class="skeleton-line h-32 w-32 rounded-full"></div>
        <div class="skeleton-line h-4 w-24 rounded-md" style="animation-delay: 200ms"></div>
        <div class="skeleton-line h-3 w-32 rounded-md" style="animation-delay: 300ms"></div>
    </div>

    <!-- Full result skeleton -->
    <div v-else-if="type === 'result'" class="space-y-6" :class="className">
        <!-- Tab bar skeleton -->
        <div class="flex gap-6 border-b border-zinc-200/60 pb-3 dark:border-zinc-800/60">
            <div class="skeleton-line h-4 w-20 rounded-md"></div>
            <div class="skeleton-line h-4 w-16 rounded-md" style="animation-delay: 100ms"></div>
            <div class="skeleton-line h-4 w-18 rounded-md" style="animation-delay: 200ms"></div>
        </div>

        <!-- Main result card -->
        <div class="rounded-xl border border-zinc-200/60 p-6 dark:border-zinc-800/60 sm:p-8">
            <div class="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
                <!-- Left -->
                <div class="space-y-6">
                    <div class="space-y-3">
                        <div class="skeleton-line h-4 w-36 rounded-md"></div>
                        <div class="skeleton-line h-7 w-44 rounded-full"></div>
                        <div class="skeleton-line h-3 w-full rounded-md" style="animation-delay: 150ms"></div>
                    </div>
                    <div class="grid gap-4 sm:grid-cols-3">
                        <div v-for="i in 3" :key="i" class="rounded-lg border border-zinc-200/50 p-4 dark:border-zinc-800/50">
                            <div class="skeleton-line h-3 w-16 rounded-md"></div>
                            <div class="skeleton-line mt-3 h-6 w-20 rounded-md" :style="{ animationDelay: `${i * 100}ms` }"></div>
                        </div>
                    </div>
                    <div class="space-y-2">
                        <div class="skeleton-line h-3 w-full rounded-md"></div>
                        <div class="skeleton-line h-2 w-full rounded-full"></div>
                    </div>
                </div>
                <!-- Right (gauge placeholder) -->
                <div class="flex flex-col items-center justify-center rounded-xl border border-zinc-200/50 p-6 dark:border-zinc-800/50">
                    <div class="skeleton-line h-28 w-28 rounded-full"></div>
                    <div class="skeleton-line mt-4 h-3 w-20 rounded-md" style="animation-delay: 300ms"></div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.skeleton-line {
    background: linear-gradient(
        90deg,
        rgba(0, 0, 0, 0.06) 25%,
        rgba(0, 0, 0, 0.1) 50%,
        rgba(0, 0, 0, 0.06) 75%
    );
    background-size: 200% 100%;
    animation: skeleton-shimmer 1.8s ease-in-out infinite;
}

:where(.dark, .dark *) .skeleton-line {
    background: linear-gradient(
        90deg,
        rgba(255, 255, 255, 0.04) 25%,
        rgba(255, 255, 255, 0.08) 50%,
        rgba(255, 255, 255, 0.04) 75%
    );
    background-size: 200% 100%;
}

@keyframes skeleton-shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}
</style>
