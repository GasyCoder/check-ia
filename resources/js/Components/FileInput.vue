<script setup>
/**
 * FileInput — Premium file upload with animated drop zone.
 */
import { ref } from 'vue';

const props = defineProps({
    fileName: String,
    fileObj: Object,
});

const emit = defineEmits(['select', 'remove']);
const dragOver = ref(false);

function fileIcon(name) {
    if (!name) return 'file';
    const ext = name.split('.').pop().toLowerCase();
    if (ext === 'pdf') return 'pdf';
    if (ext === 'docx') return 'docx';
    return 'txt';
}

function fileSize(file) {
    if (!file) return '';
    const s = file.size;
    if (s < 1024) return s + ' o';
    if (s < 1048576) return (s / 1024).toFixed(1) + ' Ko';
    return (s / 1048576).toFixed(1) + ' Mo';
}

function onFileInput(e) { emit('select', e.target.files[0]); e.target.value = ''; }
function onDrop(e) { dragOver.value = false; emit('select', e.dataTransfer.files[0]); }
</script>

<template>
    <div
        class="overflow-hidden rounded-xl border bg-white transition-all duration-300"
        :class="dragOver ? 'border-indigo-500 ring-2 ring-indigo-500/20 dark:border-indigo-400 dark:ring-indigo-400/20' : 'border-zinc-200/60 shadow-sm dark:border-zinc-800/60 dark:bg-zinc-900/80'"
        @dragover.prevent="dragOver = true"
        @dragleave.prevent="dragOver = false"
        @drop.prevent="onDrop"
    >
        <!-- No file -->
        <div v-if="!fileObj" class="p-5 sm:p-6">
            <label class="group flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed py-12 transition-all duration-300 sm:py-16"
                :class="dragOver
                    ? 'border-indigo-500 bg-indigo-50 dark:border-indigo-400 dark:bg-indigo-500/10'
                    : 'border-zinc-200 hover:border-zinc-400 hover:bg-zinc-50 dark:border-zinc-700 dark:hover:border-zinc-500 dark:hover:bg-zinc-800/40'"
            >
                <div class="mb-4 flex h-14 w-14 items-center justify-center rounded-xl border border-zinc-200 bg-white transition-all duration-200 group-hover:shadow-md dark:border-zinc-700 dark:bg-zinc-800"
                    :class="dragOver ? 'border-indigo-300 shadow-md shadow-indigo-500/10 dark:border-indigo-500/50' : ''"
                >
                    <svg class="h-7 w-7 transition-all duration-200" :class="dragOver ? 'text-indigo-500 scale-110' : 'text-zinc-400 group-hover:text-zinc-600 dark:text-zinc-500 dark:group-hover:text-zinc-300'" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" /></svg>
                </div>
                <p class="text-sm font-semibold text-zinc-800 dark:text-zinc-200">Glissez-déposez votre fichier ici</p>
                <p class="mt-2 text-sm text-zinc-500 dark:text-zinc-400">ou <span class="font-medium text-indigo-600 underline underline-offset-2 dark:text-indigo-400">parcourir vos fichiers</span></p>
                <div class="mt-5 flex items-center gap-3">
                    <span class="flex items-center gap-1.5 rounded-full border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-400">
                        <span class="h-1.5 w-1.5 rounded-full bg-rose-500"></span>PDF
                    </span>
                    <span class="flex items-center gap-1.5 rounded-full border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-400">
                        <span class="h-1.5 w-1.5 rounded-full bg-blue-500"></span>DOCX
                    </span>
                    <span class="flex items-center gap-1.5 rounded-full border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-400">
                        <span class="h-1.5 w-1.5 rounded-full bg-zinc-400"></span>TXT
                    </span>
                </div>
                <p class="mt-3 text-xs text-zinc-400 dark:text-zinc-500">Taille maximale : 25 Mo</p>
                <input type="file" class="hidden" accept=".txt,.pdf,.docx" @change="onFileInput" />
            </label>
        </div>

        <!-- File selected -->
        <div v-else class="p-5 sm:p-6">
            <div class="animate-slide-up flex items-center gap-4 rounded-xl border border-zinc-200/60 bg-zinc-50/50 p-4 dark:border-zinc-800/60 dark:bg-zinc-800/30">
                <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg border border-zinc-200 bg-white dark:border-zinc-700 dark:bg-zinc-800">
                    <svg v-if="fileIcon(fileName) === 'pdf'" class="h-6 w-6 text-rose-500" viewBox="0 0 24 24" fill="currentColor"><path d="M7 18h10V6H7v12zm2-10h2v2h1V8h1v4h-1v-1h-1v1H9V8zm5 0h2v6h-2V8z" /></svg>
                    <svg v-else-if="fileIcon(fileName) === 'docx'" class="h-6 w-6 text-blue-500" viewBox="0 0 24 24" fill="currentColor"><path d="M6 2h8l6 6v12c0 1.1-.9 2-2 2H6c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2zm7 1.5V9h5.5L13 3.5zM8 13h2v5H8v-5zm3-2h2v7h-2v-7zm3 4h2v3h-2v-3z" /></svg>
                    <svg v-else class="h-6 w-6 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>
                </div>
                <div class="min-w-0 flex-1">
                    <p class="truncate text-sm font-semibold text-zinc-900 dark:text-zinc-100">{{ fileName }}</p>
                    <p class="mt-0.5 text-xs text-zinc-500 dark:text-zinc-400">{{ fileSize(fileObj) }} · Prêt pour l'analyse</p>
                </div>
                <button @click="emit('remove')" class="rounded-lg p-2 text-zinc-400 transition-colors hover:bg-white hover:text-rose-500 dark:hover:bg-zinc-700 cursor-pointer" title="Retirer">
                    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
            </div>
            <p class="mt-3 text-center">
                <label class="cursor-pointer text-xs font-medium text-indigo-600 hover:underline dark:text-indigo-400">
                    Choisir un autre fichier
                    <input type="file" class="hidden" accept=".txt,.pdf,.docx" @change="onFileInput" />
                </label>
            </p>
        </div>
    </div>
</template>
