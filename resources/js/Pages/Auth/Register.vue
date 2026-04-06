<script setup>
import { ref } from 'vue';
import { router, usePage } from '@inertiajs/vue3';

const page = usePage();
const form = ref({
    name: '',
    email: '',
    password: '',
    password_confirmation: '',
});
const loading = ref(false);

function submit() {
    loading.value = true;
    router.post('/register', form.value, {
        onFinish: () => (loading.value = false),
    });
}
</script>

<template>
    <div class="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-4">
        <div class="w-full max-w-md">
            <!-- Logo -->
            <div class="text-center mb-8">
                <a href="/" class="inline-flex items-center gap-2.5">
                    <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
                        <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                        </svg>
                    </div>
                </a>
                <h1 class="text-2xl font-bold text-white mt-4">Créer un compte</h1>
                <p class="text-slate-400 text-sm mt-1">Rejoignez la plateforme de détection IA</p>
            </div>

            <!-- Card -->
            <div class="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/50 p-6 shadow-xl">
                <form @submit.prevent="submit" class="space-y-5">
                    <!-- Name -->
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-1.5">Nom complet</label>
                        <input
                            v-model="form.name"
                            type="text"
                            required
                            autocomplete="name"
                            class="w-full bg-slate-900/60 text-white border border-slate-600/50 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition placeholder-slate-500"
                            placeholder="Votre nom"
                        />
                        <p v-if="page.props.errors?.name" class="text-red-400 text-xs mt-1.5">{{ page.props.errors.name }}</p>
                    </div>

                    <!-- Email -->
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-1.5">Email</label>
                        <input
                            v-model="form.email"
                            type="email"
                            required
                            autocomplete="email"
                            class="w-full bg-slate-900/60 text-white border border-slate-600/50 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition placeholder-slate-500"
                            placeholder="votre@email.com"
                        />
                        <p v-if="page.props.errors?.email" class="text-red-400 text-xs mt-1.5">{{ page.props.errors.email }}</p>
                    </div>

                    <!-- Password -->
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-1.5">Mot de passe</label>
                        <input
                            v-model="form.password"
                            type="password"
                            required
                            autocomplete="new-password"
                            class="w-full bg-slate-900/60 text-white border border-slate-600/50 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition placeholder-slate-500"
                            placeholder="Minimum 8 caractères"
                        />
                        <p v-if="page.props.errors?.password" class="text-red-400 text-xs mt-1.5">{{ page.props.errors.password }}</p>
                    </div>

                    <!-- Confirm Password -->
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-1.5">Confirmer le mot de passe</label>
                        <input
                            v-model="form.password_confirmation"
                            type="password"
                            required
                            autocomplete="new-password"
                            class="w-full bg-slate-900/60 text-white border border-slate-600/50 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition placeholder-slate-500"
                            placeholder="Retapez votre mot de passe"
                        />
                    </div>

                    <!-- Submit -->
                    <button
                        type="submit"
                        :disabled="loading"
                        class="w-full bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 disabled:from-slate-700 disabled:to-slate-700 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 shadow-lg shadow-blue-500/20 disabled:shadow-none"
                    >
                        <span v-if="loading" class="flex items-center justify-center gap-2">
                            <svg class="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                            Création...
                        </span>
                        <span v-else>Créer mon compte</span>
                    </button>
                </form>

                <!-- Divider -->
                <div class="relative my-6">
                    <div class="absolute inset-0 flex items-center"><div class="w-full border-t border-slate-700/50"></div></div>
                    <div class="relative flex justify-center"><span class="bg-slate-800/50 px-3 text-xs text-slate-500">ou</span></div>
                </div>

                <!-- Google -->
                <a href="/auth/google" class="flex items-center justify-center gap-3 w-full py-3 px-4 rounded-xl border border-slate-600/50 text-sm font-medium text-slate-300 hover:bg-slate-700/30 hover:border-slate-500 transition-all">
                    <svg class="w-5 h-5" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
                    Continuer avec Google
                </a>
                <p class="mt-2 text-center text-xs text-slate-500">
                    Google évite l’étape de vérification email et ouvre directement l’espace complet.
                </p>

                <!-- Login link -->
                <div class="mt-6 text-center">
                    <p class="text-sm text-slate-400">
                        Déjà un compte ?
                        <a href="/login" class="text-blue-400 hover:text-blue-300 font-medium transition-colors">Se connecter</a>
                    </p>
                </div>
            </div>
        </div>
    </div>
</template>
