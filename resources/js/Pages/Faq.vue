<script setup>
import AppLayout from '../Layouts/AppLayout.vue';
</script>

<template>
    <AppLayout>
        <div class="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
            <div class="mb-10">
                <h1 class="text-2xl font-semibold text-slate-900 dark:text-white">Comment fonctionne l'analyse</h1>
                <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">Trois méthodes combinées pour une détection fiable.</p>
            </div>

            <!-- Methods -->
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-px rounded-xl border border-slate-200 dark:border-slate-700/60 overflow-hidden mb-10">
                <div class="p-6 bg-white dark:bg-slate-900/50">
                    <p class="text-xs font-medium uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-3">Méthode 1</p>
                    <h3 class="text-base font-semibold text-slate-800 dark:text-white">Modèle RoBERTa</h3>
                    <p class="text-sm text-slate-500 dark:text-slate-400 mt-2 leading-relaxed">Réseau de neurones entraîné sur des textes humains et générés par GPT. Classifie le texte via Hugging Face en local.</p>
                    <div class="mt-4 flex gap-2">
                        <span class="text-[11px] px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400">Hugging Face</span>
                        <span class="text-[11px] px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400">Deep Learning</span>
                    </div>
                </div>
                <div class="p-6 bg-white dark:bg-slate-900/50 border-x border-slate-200 dark:border-slate-700/60 sm:border-y-0 border-y">
                    <p class="text-xs font-medium uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-3">Méthode 2</p>
                    <h3 class="text-base font-semibold text-slate-800 dark:text-white">Perplexité (GPT-2)</h3>
                    <p class="text-sm text-slate-500 dark:text-slate-400 mt-2 leading-relaxed">Mesure la prévisibilité du texte. L'IA produit du texte très prévisible (faible perplexité), l'humain est plus varié.</p>
                    <div class="mt-4 flex gap-2">
                        <span class="text-[11px] px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400">GPT-2</span>
                        <span class="text-[11px] px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400">Statistique</span>
                    </div>
                </div>
                <div class="p-6 bg-white dark:bg-slate-900/50">
                    <p class="text-xs font-medium uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-3">Méthode 3</p>
                    <h3 class="text-base font-semibold text-slate-800 dark:text-white">Burstiness</h3>
                    <p class="text-sm text-slate-500 dark:text-slate-400 mt-2 leading-relaxed">Étudie la variation de complexité entre les phrases. L'IA écrit uniformément, l'humain alterne phrases courtes et longues.</p>
                    <div class="mt-4 flex gap-2">
                        <span class="text-[11px] px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400">Linguistique</span>
                    </div>
                </div>
            </div>

            <!-- Score formula -->
            <div class="rounded-xl border border-slate-200 dark:border-slate-700/60 bg-white dark:bg-slate-900/50 p-5 mb-10">
                <p class="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    <span class="font-medium text-slate-700 dark:text-slate-300">Score final</span> =
                    RoBERTa <span class="text-slate-400">(55%)</span> +
                    Perplexité <span class="text-slate-400">(27%)</span> +
                    Burstiness <span class="text-slate-400">(18%)</span>.
                    Des corrections sont appliquées pour les textes académiques contenant des citations, et lorsque les trois méthodes convergent.
                </p>
            </div>

            <!-- FAQ -->
            <h2 class="text-lg font-semibold text-slate-900 dark:text-white mb-4">Questions fréquentes</h2>
            <div class="rounded-xl border border-slate-200 dark:border-slate-700/60 bg-white dark:bg-slate-900/50 overflow-hidden divide-y divide-slate-100 dark:divide-slate-800/60">
                <details class="group">
                    <summary class="px-6 py-4 cursor-pointer select-none flex items-center justify-between text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                        Le détecteur peut-il faire des erreurs ?
                        <svg class="w-4 h-4 text-slate-400 shrink-0 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" /></svg>
                    </summary>
                    <div class="px-6 pb-5 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Oui. Un texte humain très formel ou structuré peut obtenir un score plus élevé. Nous combinons trois métriques et détectons les citations académiques pour réduire les faux positifs, mais aucun détecteur n'est parfait à 100%.</div>
                </details>
                <details class="group">
                    <summary class="px-6 py-4 cursor-pointer select-none flex items-center justify-between text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                        Le français est-il supporté ?
                        <svg class="w-4 h-4 text-slate-400 shrink-0 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" /></svg>
                    </summary>
                    <div class="px-6 pb-5 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Oui. Les textes français sont automatiquement traduits en anglais (Helsinki-NLP/opus-mt-fr-en) pour l'analyse RoBERTa. La perplexité et la burstiness fonctionnent dans toutes les langues sans traduction.</div>
                </details>
                <details class="group">
                    <summary class="px-6 py-4 cursor-pointer select-none flex items-center justify-between text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                        Comment sont traités les longs documents ?
                        <svg class="w-4 h-4 text-slate-400 shrink-0 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" /></svg>
                    </summary>
                    <div class="px-6 pb-5 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">Les documents sont découpés en sections. Les pages non pertinentes (couverture, sommaire, bibliographie) sont filtrées automatiquement. Chaque section est analysée individuellement, puis un score global pondéré est calculé.</div>
                </details>
                <details class="group">
                    <summary class="px-6 py-4 cursor-pointer select-none flex items-center justify-between text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                        Quels formats de fichiers sont acceptés ?
                        <svg class="w-4 h-4 text-slate-400 shrink-0 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" /></svg>
                    </summary>
                    <div class="px-6 pb-5 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">PDF, DOCX et TXT, jusqu'à 25 Mo. Le texte collé directement supporte jusqu'à 1 500 000 caractères (~500 pages).</div>
                </details>
                <details class="group">
                    <summary class="px-6 py-4 cursor-pointer select-none flex items-center justify-between text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                        Mes données sont-elles sécurisées ?
                        <svg class="w-4 h-4 text-slate-400 shrink-0 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" /></svg>
                    </summary>
                    <div class="px-6 pb-5 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">L'analyse est exécutée entièrement en local sur notre serveur. Aucun texte n'est envoyé à des services tiers. Vos analyses sont dans votre historique personnel, consultables et supprimables à tout moment.</div>
                </details>
            </div>
        </div>
    </AppLayout>
</template>
