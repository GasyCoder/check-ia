<script setup>
/**
 * ToastProvider — Global toast notification display.
 * Place in AppLayout to enable toasts across all pages.
 */
import { computed } from 'vue';
import { useToast } from '../Composables/useToast';

const { toasts, remove } = useToast();

const TOAST_CONFIG = {
    success: {
        icon: 'M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
        bg: 'bg-emerald-50 dark:bg-emerald-500/10',
        border: 'border-emerald-200 dark:border-emerald-500/20',
        iconColor: 'text-emerald-500',
        textColor: 'text-emerald-800 dark:text-emerald-300',
        progressColor: 'bg-emerald-500',
    },
    error: {
        icon: 'M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z',
        bg: 'bg-rose-50 dark:bg-rose-500/10',
        border: 'border-rose-200 dark:border-rose-500/20',
        iconColor: 'text-rose-500',
        textColor: 'text-rose-800 dark:text-rose-300',
        progressColor: 'bg-rose-500',
    },
    info: {
        icon: 'M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z',
        bg: 'bg-blue-50 dark:bg-blue-500/10',
        border: 'border-blue-200 dark:border-blue-500/20',
        iconColor: 'text-blue-500',
        textColor: 'text-blue-800 dark:text-blue-300',
        progressColor: 'bg-blue-500',
    },
    warning: {
        icon: 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z',
        bg: 'bg-amber-50 dark:bg-amber-500/10',
        border: 'border-amber-200 dark:border-amber-500/20',
        iconColor: 'text-amber-500',
        textColor: 'text-amber-800 dark:text-amber-300',
        progressColor: 'bg-amber-500',
    },
};

function getConfig(type) {
    return TOAST_CONFIG[type] || TOAST_CONFIG.info;
}
</script>

<template>
    <!-- Toast container — fixed top-right -->
    <teleport to="body">
        <div
            class="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none"
            style="max-width: 380px; width: 100%"
            aria-live="polite"
        >
            <transition-group
                enter-active-class="animate-toast-in"
                leave-active-class="animate-toast-out"
                move-class="transition-all duration-300 ease-out"
            >
                <div
                    v-for="toast in toasts"
                    :key="toast.id"
                    class="pointer-events-auto relative overflow-hidden rounded-xl border shadow-lg backdrop-blur-sm"
                    :class="[getConfig(toast.type).bg, getConfig(toast.type).border]"
                >
                    <div class="flex items-start gap-3 px-4 py-3">
                        <!-- Icon -->
                        <svg
                            class="mt-0.5 h-5 w-5 shrink-0"
                            :class="getConfig(toast.type).iconColor"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            stroke-width="1.5"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                :d="getConfig(toast.type).icon"
                            />
                        </svg>

                        <!-- Message -->
                        <p
                            class="flex-1 text-sm font-medium leading-relaxed"
                            :class="getConfig(toast.type).textColor"
                        >
                            {{ toast.message }}
                        </p>

                        <!-- Close button -->
                        <button
                            type="button"
                            class="shrink-0 rounded-lg p-0.5 transition-colors hover:bg-black/5 dark:hover:bg-white/10 cursor-pointer"
                            :class="getConfig(toast.type).textColor"
                            @click="remove(toast.id)"
                        >
                            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    <!-- Progress bar -->
                    <div
                        v-if="toast.duration > 0"
                        class="h-0.5 origin-left"
                        :class="getConfig(toast.type).progressColor"
                        :style="{
                            animation: `toast-progress ${toast.duration}ms linear forwards`,
                        }"
                    ></div>
                </div>
            </transition-group>
        </div>
    </teleport>
</template>

<style scoped>
@keyframes toast-progress {
    from { transform: scaleX(1); }
    to { transform: scaleX(0); }
}
</style>
