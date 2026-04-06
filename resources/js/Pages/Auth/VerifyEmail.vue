<script setup>
import { ref } from 'vue';
import { router, usePage } from '@inertiajs/vue3';

const page = usePage();
const sending = ref(false);
const sent = ref(false);

function resend() {
    sending.value = true;
    router.post('/email/resend', {}, {
        onFinish: () => {
            sending.value = false;
            sent.value = true;
        },
    });
}

function logout() {
    router.post('/logout');
}
</script>

<template>
    <div class="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-4">
        <div class="w-full max-w-md text-center">
            <div class="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
                <svg class="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
                </svg>
            </div>

            <h1 class="text-2xl font-bold text-white mb-2">Vérifiez votre email</h1>
            <p class="text-slate-400 text-sm mb-6">
                Un lien de vérification a été envoyé à votre adresse email.
                Cliquez sur le lien pour activer votre compte.
            </p>

            <div class="bg-slate-800/50 rounded-2xl border border-slate-700/50 p-6 space-y-4">
                <div v-if="sent || page.props.flash?.success" class="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/25">
                    <p class="text-emerald-400 text-sm">Un nouveau lien a été envoyé !</p>
                </div>

                <button
                    @click="resend"
                    :disabled="sending"
                    class="w-full bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 disabled:from-slate-700 disabled:to-slate-700 text-white font-semibold py-3 px-6 rounded-xl transition-all"
                >
                    <span v-if="sending">Envoi en cours...</span>
                    <span v-else>Renvoyer le lien de vérification</span>
                </button>

                <button @click="logout" class="w-full text-sm text-slate-400 hover:text-slate-300 py-2 transition-colors">
                    Se déconnecter
                </button>
            </div>
        </div>
    </div>
</template>
