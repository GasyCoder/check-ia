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
        class="rounded-2xl border transition-all duration-300 bg-white dark:bg-slate-900/50 overflow-hidden"
        :class="dragOver ? 'border-blue-500 shadow-xl shadow-blue-500/10 ring-2 ring-blue-500/20' : 'border-slate-200 dark:border-slate-700/60 shadow-sm'"
        @dragover.prevent="dragOver = true"
        @dragleave.prevent="dragOver = false"
        @drop.prevent="onDrop"
    >
        <!-- No file -->
        <div v-if="!fileObj" class="p-6 sm:p-8">
            <label class="flex flex-col items-center justify-center py-16 sm:py-20 border-2 border-dashed rounded-2xl cursor-pointer transition-all group"
                :class="dragOver ? 'border-blue-500 bg-blue-50 dark:bg-blue-500/10' : 'border-slate-200 dark:border-slate-700 hover:border-blue-400 dark:hover:border-blue-500 hover:bg-blue-50/30 dark:hover:bg-blue-500/5'"
            >
                <div class="w-16 h-16 rounded-2xl flex items-center justify-center mb-4 transition-colors" :class="dragOver ? 'bg-blue-100 dark:bg-blue-500/20' : 'bg-slate-100 dark:bg-slate-800 group-hover:bg-blue-100 dark:group-hover:bg-blue-500/20'">
                    <svg class="w-8 h-8 transition-colors" :class="dragOver ? 'text-blue-500' : 'text-slate-400 group-hover:text-blue-500'" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" /></svg>
                </div>
                <p class="text-base font-semibold transition-colors" :class="dragOver ? 'text-blue-600 dark:text-blue-400' : 'text-slate-700 dark:text-slate-300 group-hover:text-blue-600 dark:group-hover:text-blue-400'">Glissez-déposez votre fichier ici</p>
                <p class="text-sm mt-2 text-slate-500 dark:text-slate-400">ou <span class="text-blue-600 dark:text-blue-400 font-medium underline underline-offset-2 decoration-blue-500/30">parcourir vos fichiers</span></p>
                <div class="flex items-center gap-4 mt-6">
                    <span class="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400">
                        <svg class="w-3.5 h-3.5 text-red-500" viewBox="0 0 24 24" fill="currentColor"><path d="M7 18h10V6H7v12zm2-10h2v2h1V8h1v4h-1v-1h-1v1H9V8zm5 0h2v6h-2V8z" /></svg>PDF
                    </span>
                    <span class="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400">
                        <svg class="w-3.5 h-3.5 text-blue-500" viewBox="0 0 24 24" fill="currentColor"><path d="M6 2h8l6 6v12c0 1.1-.9 2-2 2H6c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2zm7 1.5V9h5.5L13 3.5zM8 13h2v5H8v-5zm3-2h2v7h-2v-7zm3 4h2v3h-2v-3z" /></svg>DOCX
                    </span>
                    <span class="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400">
                        <svg class="w-3.5 h-3.5 text-slate-500" viewBox="0 0 24 24" fill="currentColor"><path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6z" /></svg>TXT
                    </span>
                </div>
                <p class="text-[11px] mt-3 text-slate-400 dark:text-slate-500">Taille maximale : 25 Mo</p>
                <input type="file" class="hidden" accept=".txt,.pdf,.docx" @change="onFileInput" />
            </label>
        </div>
        <!-- File selected -->
        <div v-else class="p-6 sm:p-8">
            <div class="flex items-center gap-5 p-5 rounded-xl border bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/50">
                <div class="w-14 h-14 rounded-xl flex items-center justify-center shrink-0" :class="fileIcon(fileName) === 'pdf' ? 'bg-red-50 dark:bg-red-500/10' : fileIcon(fileName) === 'docx' ? 'bg-blue-50 dark:bg-blue-500/10' : 'bg-slate-100 dark:bg-slate-700/50'">
                    <svg v-if="fileIcon(fileName) === 'pdf'" class="w-7 h-7 text-red-500" viewBox="0 0 24 24" fill="currentColor"><path d="M7 18h10V6H7v12zm2-10h2v2h1V8h1v4h-1v-1h-1v1H9V8zm5 0h2v6h-2V8z" /></svg>
                    <svg v-else-if="fileIcon(fileName) === 'docx'" class="w-7 h-7 text-blue-500" viewBox="0 0 24 24" fill="currentColor"><path d="M6 2h8l6 6v12c0 1.1-.9 2-2 2H6c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2zm7 1.5V9h5.5L13 3.5zM8 13h2v5H8v-5zm3-2h2v7h-2v-7zm3 4h2v3h-2v-3z" /></svg>
                    <svg v-else class="w-7 h-7 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-base font-semibold truncate text-slate-800 dark:text-white">{{ fileName }}</p>
                    <p class="text-sm text-slate-500 dark:text-slate-400 mt-0.5">{{ fileSize(fileObj) }} &middot; Prêt pour l'analyse</p>
                </div>
                <button @click="emit('remove')" class="p-2 rounded-lg transition-colors text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10" title="Retirer">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
            </div>
            <p class="text-center mt-4">
                <label class="text-sm cursor-pointer text-blue-600 dark:text-blue-400 hover:underline">
                    Choisir un autre fichier
                    <input type="file" class="hidden" accept=".txt,.pdf,.docx" @change="onFileInput" />
                </label>
            </p>
        </div>
    </div>
</template>
