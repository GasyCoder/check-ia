/**
 * useToast — Global toast notification composable.
 *
 * Usage:
 *   import { useToast } from '../Composables/useToast';
 *   const toast = useToast();
 *   toast.success('Analyse terminée');
 *   toast.error('Service indisponible');
 */

import { reactive, readonly } from 'vue';

let nextId = 0;

const state = reactive({
    toasts: [],
});

const DEFAULT_DURATION = 4000;

function addToast(type, message, options = {}) {
    const id = ++nextId;
    const duration = options.duration ?? DEFAULT_DURATION;

    const toast = {
        id,
        type,
        message,
        duration,
        createdAt: Date.now(),
    };

    state.toasts.push(toast);

    if (duration > 0) {
        setTimeout(() => removeToast(id), duration);
    }

    return id;
}

function removeToast(id) {
    const index = state.toasts.findIndex((t) => t.id === id);
    if (index !== -1) {
        state.toasts.splice(index, 1);
    }
}

function clearAll() {
    state.toasts.splice(0, state.toasts.length);
}

export function useToast() {
    return {
        toasts: readonly(state.toasts),
        success: (message, options) => addToast('success', message, options),
        error: (message, options) => addToast('error', message, options),
        info: (message, options) => addToast('info', message, options),
        warning: (message, options) => addToast('warning', message, options),
        remove: removeToast,
        clear: clearAll,
    };
}
