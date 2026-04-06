<script setup>
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
        class="overflow-hidden rounded-lg border bg-white transition-all duration-300"
        :class="dragOver ? 'border-zinc-900 ring-2 ring-zinc-900/10 dark:border-zinc-500 dark:ring-zinc-500/20' : 'border-zinc-200 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/90'"
        @dragover.prevent="dragOver = true"
        @dragleave.prevent="dragOver = false"
        @drop.prevent="onDrop"
    >
        <!-- No file -->
        <div v-if="!fileObj" class="p-6 sm:p-8">
            <label class="group flex cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed py-16 transition-all sm:py-20"
                :class="dragOver ? 'border-zinc-900 bg-zinc-50 dark:border-zinc-500 dark:bg-zinc-950' : 'border-zinc-300 hover:border-zinc-500 hover:bg-zinc-50 dark:border-zinc-700 dark:hover:border-zinc-500 dark:hover:bg-zinc-950'"
            >
                <div class="mb-4 flex h-14 w-14 items-center justify-center rounded-lg border border-zinc-200 bg-white transition-colors dark:border-zinc-800 dark:bg-zinc-900">
                    <svg class="h-7 w-7 transition-colors" :class="dragOver ? 'text-zinc-900 dark:text-zinc-100' : 'text-zinc-400 group-hover:text-zinc-700 dark:text-zinc-500 dark:group-hover:text-zinc-300'" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" /></svg>
                </div>
                <p class="text-sm font-semibold text-zinc-950 dark:text-zinc-50">Glissez-déposez votre fichier ici</p>
                <p class="mt-2 text-sm text-zinc-500 dark:text-zinc-400">ou <span class="font-medium text-zinc-900 underline underline-offset-2 dark:text-zinc-100">parcourir vos fichiers</span></p>
                <div class="mt-6 flex items-center gap-4">
                    <span class="flex items-center gap-1.5 rounded-full border border-zinc-200 bg-white px-3 py-1.5 text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400">
                        <svg class="w-3.5 h-3.5 text-red-500" viewBox="0 0 24 24" fill="currentColor"><path d="M7 18h10V6H7v12zm2-10h2v2h1V8h1v4h-1v-1h-1v1H9V8zm5 0h2v6h-2V8z" /></svg>PDF
                    </span>
                    <span class="flex items-center gap-1.5 rounded-full border border-zinc-200 bg-white px-3 py-1.5 text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400">
                        <svg class="w-3.5 h-3.5 text-blue-500" viewBox="0 0 24 24" fill="currentColor"><path d="M6 2h8l6 6v12c0 1.1-.9 2-2 2H6c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2zm7 1.5V9h5.5L13 3.5zM8 13h2v5H8v-5zm3-2h2v7h-2v-7zm3 4h2v3h-2v-3z" /></svg>DOCX
                    </span>
                    <span class="flex items-center gap-1.5 rounded-full border border-zinc-200 bg-white px-3 py-1.5 text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400">
                        <svg class="w-3.5 h-3.5 text-slate-500" viewBox="0 0 24 24" fill="currentColor"><path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6z" /></svg>TXT
                    </span>
                </div>
                <p class="mt-3 text-sm text-zinc-500 dark:text-zinc-400">Taille maximale : 25 Mo</p>
                <input type="file" class="hidden" accept=".txt,.pdf,.docx" @change="onFileInput" />
            </label>
        </div>
        <!-- File selected -->
        <div v-else class="p-6 sm:p-8">
            <div class="flex items-center gap-5 rounded-lg border border-zinc-200 bg-zinc-50 p-5 dark:border-zinc-800 dark:bg-zinc-950">
                <div class="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
                    <svg v-if="fileIcon(fileName) === 'pdf'" class="w-7 h-7 text-red-500" viewBox="0 0 24 24" fill="currentColor"><path d="M7 18h10V6H7v12zm2-10h2v2h1V8h1v4h-1v-1h-1v1H9V8zm5 0h2v6h-2V8z" /></svg>
                    <svg v-else-if="fileIcon(fileName) === 'docx'" class="w-7 h-7 text-blue-500" viewBox="0 0 24 24" fill="currentColor"><path d="M6 2h8l6 6v12c0 1.1-.9 2-2 2H6c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2zm7 1.5V9h5.5L13 3.5zM8 13h2v5H8v-5zm3-2h2v7h-2v-7zm3 4h2v3h-2v-3z" /></svg>
                    <svg v-else class="w-7 h-7 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="truncate text-sm font-semibold text-zinc-950 dark:text-zinc-50">{{ fileName }}</p>
                    <p class="mt-0.5 text-sm text-zinc-500 dark:text-zinc-400">{{ fileSize(fileObj) }} &middot; Prêt pour l'analyse</p>
                </div>
                <button @click="emit('remove')" class="rounded-lg p-2 text-zinc-400 transition-colors hover:bg-white hover:text-rose-500 dark:hover:bg-zinc-900 cursor-pointer" title="Retirer">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
            </div>
            <p class="text-center mt-4">
                <label class="cursor-pointer text-sm text-zinc-900 hover:underline dark:text-zinc-100">
                    Choisir un autre fichier
                    <input type="file" class="hidden" accept=".txt,.pdf,.docx" @change="onFileInput" />
                </label>
            </p>
        </div>
    </div>
</template>
