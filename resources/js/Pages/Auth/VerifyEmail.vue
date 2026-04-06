<script setup>
import { computed, ref } from 'vue';
import { router, usePage } from '@inertiajs/vue3';

const page = usePage();
const sending = ref(false);
const sent = ref(false);

const email = computed(() => page.props.auth?.user?.email ?? '');

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
    <div class="min-h-screen bg-slate-50 px-4 py-10">
        <div class="mx-auto max-w-lg rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <h1 class="text-2xl font-semibold tracking-tight text-slate-950">Vérifiez votre email</h1>
            <p class="mt-3 text-sm leading-7 text-slate-600">
                Un lien de vérification a été envoyé à <span class="font-medium text-slate-900">{{ email || 'votre adresse email' }}</span>.
            </p>

            <div v-if="sent || page.props.flash?.success" class="mt-5 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                Un nouveau lien a été envoyé.
            </div>

            <div class="mt-6 space-y-2 text-sm text-slate-600">
                <p>1. Ouvrez votre boîte mail.</p>
                <p>2. Cliquez sur le lien reçu.</p>
                <p>3. Si besoin, renvoyez le lien ci-dessous.</p>
            </div>

            <div class="mt-6 space-y-3">
                <button
                    type="button"
                    :disabled="sending"
                    class="w-full rounded-lg bg-slate-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                    @click="resend"
                >
                    <span v-if="sending">Envoi en cours...</span>
                    <span v-else>Renvoyer le lien</span>
                </button>

                <button
                    type="button"
                    class="w-full rounded-lg border border-slate-300 px-5 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                    @click="logout"
                >
                    Se déconnecter
                </button>
            </div>
        </div>
    </div>
</template>
