<script setup>
/**
 * ScoreGauge — Animated circular SVG gauge for AI detection scores.
 *
 * Props:
 *   score: number (0-100) — the percentage to display
 *   label: string — text label below the gauge
 *   size: 'sm' | 'md' | 'lg' — gauge size
 *   animated: boolean — enable/disable fill animation
 *   invertColors: boolean — if true, high = green (for "authenticity" display)
 */
import { computed, ref, onMounted, watch } from 'vue';

const props = defineProps({
    score: { type: Number, default: 0 },
    label: { type: String, default: '' },
    size: { type: String, default: 'md', validator: (v) => ['sm', 'md', 'lg'].includes(v) },
    animated: { type: Boolean, default: true },
    invertColors: { type: Boolean, default: false },
    palette: {
        type: String,
        default: 'auto',
        validator: (v) => ['auto', 'cyan', 'violet', 'emerald', 'amber', 'rose'].includes(v),
    },
});

const displayValue = ref(0);
const hasAnimated = ref(false);

const sizeConfig = computed(() => {
    const configs = {
        sm: { dimension: 96, strokeWidth: 6, fontSize: 'text-xl', labelSize: 'text-xs', radius: 38 },
        md: { dimension: 136, strokeWidth: 7, fontSize: 'text-3xl', labelSize: 'text-sm', radius: 56 },
        lg: { dimension: 176, strokeWidth: 8, fontSize: 'text-4xl', labelSize: 'text-sm', radius: 72 },
    };
    return configs[props.size];
});

const circumference = computed(() => 2 * Math.PI * sizeConfig.value.radius);

const dashOffset = computed(() => {
    const progress = Math.min(100, Math.max(0, props.score)) / 100;
    return circumference.value * (1 - progress);
});

const paletteColors = {
    cyan: { stroke: '#06b6d4', glow: 'rgba(6, 182, 212, 0.2)', text: 'text-cyan-500' },
    violet: { stroke: '#8b5cf6', glow: 'rgba(139, 92, 246, 0.22)', text: 'text-violet-500' },
    emerald: { stroke: '#10b981', glow: 'rgba(16, 185, 129, 0.2)', text: 'text-emerald-500' },
    amber: { stroke: '#f59e0b', glow: 'rgba(245, 158, 11, 0.2)', text: 'text-amber-500' },
    rose: { stroke: '#ef4444', glow: 'rgba(239, 68, 68, 0.2)', text: 'text-rose-500' },
};

const scoreColor = computed(() => {
    if (props.palette !== 'auto') {
        return paletteColors[props.palette];
    }

    const value = props.invertColors ? 100 - props.score : props.score;
    if (value >= 75) return { stroke: '#ef4444', glow: 'rgba(239, 68, 68, 0.2)', text: 'text-rose-500' };
    if (value >= 50) return { stroke: '#f59e0b', glow: 'rgba(245, 158, 11, 0.2)', text: 'text-amber-500' };
    if (value >= 25) return { stroke: '#06b6d4', glow: 'rgba(6, 182, 212, 0.2)', text: 'text-cyan-500' };
    return { stroke: '#10b981', glow: 'rgba(16, 185, 129, 0.2)', text: 'text-emerald-500' };
});

const gradientId = computed(() => `gauge-gradient-${Math.random().toString(36).slice(2, 9)}`);

function animateCounter(target, duration = 1200) {
    const start = displayValue.value;
    const diff = target - start;
    const startTime = performance.now();

    function step(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Ease-out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        displayValue.value = Math.round((start + diff * eased) * 10) / 10;

        if (progress < 1) {
            requestAnimationFrame(step);
        }
    }

    requestAnimationFrame(step);
}

onMounted(() => {
    if (props.animated) {
        setTimeout(() => {
            animateCounter(props.score);
            hasAnimated.value = true;
        }, 200);
    } else {
        displayValue.value = props.score;
        hasAnimated.value = true;
    }
});

watch(() => props.score, (newScore) => {
    if (hasAnimated.value) {
        animateCounter(newScore);
    }
});
</script>

<template>
    <div class="flex flex-col items-center gap-2">
        <div class="relative" :style="{ width: sizeConfig.dimension + 'px', height: sizeConfig.dimension + 'px' }">
            <svg
                :width="sizeConfig.dimension"
                :height="sizeConfig.dimension"
                :viewBox="`0 0 ${sizeConfig.dimension} ${sizeConfig.dimension}`"
                class="transform -rotate-90"
            >
                <defs>
                    <linearGradient :id="gradientId" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" :stop-color="scoreColor.stroke" stop-opacity="1" />
                        <stop offset="100%" :stop-color="scoreColor.stroke" stop-opacity="0.6" />
                    </linearGradient>

                    <!-- Glow filter -->
                    <filter :id="gradientId + '-glow'" x="-20%" y="-20%" width="140%" height="140%">
                        <feGaussianBlur stdDeviation="3" result="blur" />
                        <feComposite in="SourceGraphic" in2="blur" operator="over" />
                    </filter>
                </defs>

                <!-- Background track -->
                <circle
                    :cx="sizeConfig.dimension / 2"
                    :cy="sizeConfig.dimension / 2"
                    :r="sizeConfig.radius"
                    fill="none"
                    :stroke-width="sizeConfig.strokeWidth"
                    class="stroke-zinc-100 dark:stroke-zinc-800"
                    stroke-linecap="round"
                />

                <!-- Score arc -->
                <circle
                    :cx="sizeConfig.dimension / 2"
                    :cy="sizeConfig.dimension / 2"
                    :r="sizeConfig.radius"
                    fill="none"
                    :stroke="`url(#${gradientId})`"
                    :stroke-width="sizeConfig.strokeWidth"
                    stroke-linecap="round"
                    :stroke-dasharray="circumference"
                    :stroke-dashoffset="dashOffset"
                    :filter="`url(#${gradientId}-glow)`"
                    class="transition-all duration-1000 ease-out"
                />
            </svg>

            <!-- Center text -->
            <div class="absolute inset-0 flex flex-col items-center justify-center">
                <span class="font-display font-bold tabular-nums" :class="[sizeConfig.fontSize, scoreColor.text]">
                    {{ displayValue.toFixed(1) }}
                </span>
                <span class="text-[10px] font-medium text-zinc-400 dark:text-zinc-500">%</span>
            </div>
        </div>

        <!-- Label -->
        <span v-if="label" :class="sizeConfig.labelSize" class="font-medium text-zinc-500 dark:text-zinc-400">
            {{ label }}
        </span>
    </div>
</template>
