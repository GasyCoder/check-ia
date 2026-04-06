<script setup>
import { ref, computed } from 'vue';
import { router, usePage } from '@inertiajs/vue3';
import axios from 'axios';
import AppLayout from '../Layouts/AppLayout.vue';

const page = usePage();
const props = defineProps({
    user: Object,
    statusOptions: Array,
});

const profileForm = ref({
    name: props.user.name || '',
    first_name: props.user.first_name || '',
    birth_date: props.user.birth_date ? props.user.birth_date.split('T')[0] : '',
    status: props.user.status || '',
    affiliation: props.user.affiliation || '',
});

const passwordForm = ref({
    current_password: '',
    password: '',
    password_confirmation: '',
});

const savingProfile = ref(false);
const savingPassword = ref(false);
const uploadingAvatar = ref(false);
const showSuccess = ref(false);
const avatarPreview = ref(props.user.avatar_url || null);

function saveProfile() {
    savingProfile.value = true;
    router.put('/profile', profileForm.value, {
        preserveScroll: true,
        onFinish: () => { savingProfile.value = false; },
        onSuccess: () => { showSuccess.value = true; setTimeout(() => showSuccess.value = false, 3000); },
    });
}

function savePassword() {
    savingPassword.value = true;
    router.put('/profile/password', passwordForm.value, {
        preserveScroll: true,
        onFinish: () => { savingPassword.value = false; },
        onSuccess: () => {
            passwordForm.value = { current_password: '', password: '', password_confirmation: '' };
            showSuccess.value = true;
            setTimeout(() => showSuccess.value = false, 3000);
        },
    });
}

function onAvatarSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    // Preview
    const reader = new FileReader();
    reader.onload = (ev) => { avatarPreview.value = ev.target.result; };
    reader.readAsDataURL(file);

    // Upload
    uploadingAvatar.value = true;
    const formData = new FormData();
    formData.append('avatar', file);

    router.post('/profile/avatar', formData, {
        preserveScroll: true,
        onFinish: () => { uploadingAvatar.value = false; },
        onSuccess: () => {
            showSuccess.value = true;
            setTimeout(() => showSuccess.value = false, 3000);
        },
    });

    e.target.value = '';
}

function deleteAvatar() {
    router.delete('/profile/avatar', {
        preserveScroll: true,
        onSuccess: () => {
            avatarPreview.value = null;
            showSuccess.value = true;
            setTimeout(() => showSuccess.value = false, 3000);
        },
    });
}

const isVerified = computed(() => !!props.user.email_verified_at);
const memberSince = computed(() => new Date(props.user.created_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric' }));
</script>

<template>
    <AppLayout>
        <div class="max-w-3xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
            <!-- Header -->
            <div class="mb-8">
                <h1 class="text-3xl font-bold text-slate-900 dark:text-white">Mon profil</h1>
                <p class="mt-1 text-slate-500 dark:text-slate-400">Gérez vos informations personnelles</p>
            </div>

            <!-- Success toast -->
            <transition enter-active-class="transition duration-200" enter-from-class="opacity-0 -translate-y-2" enter-to-class="opacity-100" leave-active-class="transition duration-150" leave-from-class="opacity-100" leave-to-class="opacity-0">
                <div v-if="showSuccess || page.props.flash?.success" class="mb-6 p-4 rounded-xl border flex items-center gap-2 bg-emerald-50 dark:bg-emerald-500/10 border-emerald-200 dark:border-emerald-500/25">
                    <svg class="w-5 h-5 text-emerald-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    <p class="text-sm text-emerald-700 dark:text-emerald-400">{{ page.props.flash?.success || 'Enregistré avec succès !' }}</p>
                </div>
            </transition>

            <div class="space-y-6">
                <!-- Profile card -->
                <div class="rounded-2xl border bg-white dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/50 overflow-hidden">
                    <!-- Header with avatar -->
                    <div class="px-6 py-6 border-b border-slate-100 dark:border-slate-700/30 flex items-center gap-5">
                        <!-- Avatar with upload -->
                        <div class="relative group shrink-0">
                            <img v-if="avatarPreview" :src="avatarPreview" :alt="user.name" class="w-20 h-20 rounded-full object-cover ring-4 ring-slate-100 dark:ring-slate-700" />
                            <div v-else class="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-white text-2xl font-bold ring-4 ring-slate-100 dark:ring-slate-700">
                                {{ user.name?.charAt(0).toUpperCase() }}
                            </div>

                            <!-- Upload overlay -->
                            <label class="absolute inset-0 flex items-center justify-center rounded-full cursor-pointer bg-black/0 group-hover:bg-black/40 transition-all">
                                <div class="opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center">
                                    <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6.827 6.175A2.31 2.31 0 015.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 00-1.134-.175 2.31 2.31 0 01-1.64-1.055l-.822-1.316a2.192 2.192 0 00-1.736-1.039 48.774 48.774 0 00-5.232 0 2.192 2.192 0 00-1.736 1.039l-.821 1.316z" /><path stroke-linecap="round" stroke-linejoin="round" d="M16.5 12.75a4.5 4.5 0 11-9 0 4.5 4.5 0 019 0z" /></svg>
                                </div>
                                <input type="file" class="hidden" accept="image/jpeg,image/png,image/webp" @change="onAvatarSelect" />
                            </label>

                            <!-- Loading spinner -->
                            <div v-if="uploadingAvatar" class="absolute inset-0 flex items-center justify-center rounded-full bg-black/50">
                                <svg class="w-6 h-6 text-white animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                            </div>
                        </div>

                        <div class="flex-1">
                            <p class="text-lg font-semibold text-slate-900 dark:text-white">{{ user.name }} {{ user.first_name || '' }}</p>
                            <div class="flex items-center gap-2 mt-0.5">
                                <span class="text-sm text-slate-500 dark:text-slate-400">{{ user.email }}</span>
                                <span v-if="isVerified" class="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
                                    <svg class="w-2.5 h-2.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" /></svg>
                                    Vérifié
                                </span>
                            </div>
                            <p class="text-xs text-slate-400 dark:text-slate-500 mt-1">Membre depuis {{ memberSince }}</p>
                            <div class="flex items-center gap-3 mt-2">
                                <label class="text-xs font-medium cursor-pointer text-blue-600 dark:text-blue-400 hover:underline">
                                    Changer la photo
                                    <input type="file" class="hidden" accept="image/jpeg,image/png,image/webp" @change="onAvatarSelect" />
                                </label>
                                <button v-if="avatarPreview" @click="deleteAvatar" class="text-xs font-medium text-slate-400 hover:text-red-500 transition-colors">Supprimer</button>
                            </div>
                        </div>
                    </div>

                    <!-- Profile form -->
                    <form @submit.prevent="saveProfile" class="p-6 space-y-5">
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
                            <div>
                                <label class="block text-sm font-medium mb-1.5 text-slate-700 dark:text-slate-300">Nom *</label>
                                <input v-model="profileForm.name" type="text" required class="w-full text-sm px-4 py-2.5 rounded-xl border bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-600/50 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition" />
                                <p v-if="page.props.errors?.name" class="text-red-500 text-xs mt-1">{{ page.props.errors.name }}</p>
                            </div>
                            <div>
                                <label class="block text-sm font-medium mb-1.5 text-slate-700 dark:text-slate-300">Prénom <span class="text-slate-400">(optionnel)</span></label>
                                <input v-model="profileForm.first_name" type="text" class="w-full text-sm px-4 py-2.5 rounded-xl border bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-600/50 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition" />
                            </div>
                        </div>

                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
                            <div>
                                <label class="block text-sm font-medium mb-1.5 text-slate-700 dark:text-slate-300">Date de naissance</label>
                                <input v-model="profileForm.birth_date" type="date" class="w-full text-sm px-4 py-2.5 rounded-xl border bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-600/50 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition" />
                            </div>
                            <div>
                                <label class="block text-sm font-medium mb-1.5 text-slate-700 dark:text-slate-300">Statut</label>
                                <select v-model="profileForm.status" class="w-full text-sm px-4 py-2.5 rounded-xl border bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-600/50 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition">
                                    <option value="">Sélectionner...</option>
                                    <option v-for="opt in statusOptions" :key="opt" :value="opt">{{ opt }}</option>
                                </select>
                            </div>
                        </div>

                        <div>
                            <label class="block text-sm font-medium mb-1.5 text-slate-700 dark:text-slate-300">Affiliation</label>
                            <input v-model="profileForm.affiliation" type="text" placeholder="Université, entreprise, organisation..." class="w-full text-sm px-4 py-2.5 rounded-xl border bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-600/50 text-slate-800 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition" />
                        </div>

                        <div class="flex justify-end pt-2">
                            <button type="submit" :disabled="savingProfile" class="px-6 py-2.5 rounded-xl text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 disabled:from-slate-600 disabled:to-slate-600 transition-all shadow-lg shadow-blue-500/20 disabled:shadow-none">
                                {{ savingProfile ? 'Enregistrement...' : 'Enregistrer' }}
                            </button>
                        </div>
                    </form>
                </div>

                <!-- Password card -->
                <div class="rounded-2xl border bg-white dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/50 overflow-hidden">
                    <div class="px-6 py-4 border-b border-slate-100 dark:border-slate-700/30">
                        <h2 class="text-lg font-semibold text-slate-900 dark:text-white">Changer le mot de passe</h2>
                        <p class="text-sm text-slate-500 dark:text-slate-400 mt-0.5">Utilisez un mot de passe fort et unique</p>
                    </div>

                    <form @submit.prevent="savePassword" class="p-6 space-y-5">
                        <div>
                            <label class="block text-sm font-medium mb-1.5 text-slate-700 dark:text-slate-300">Mot de passe actuel</label>
                            <input v-model="passwordForm.current_password" type="password" required class="w-full text-sm px-4 py-2.5 rounded-xl border bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-600/50 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition" />
                            <p v-if="page.props.errors?.current_password" class="text-red-500 text-xs mt-1">{{ page.props.errors.current_password }}</p>
                        </div>

                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
                            <div>
                                <label class="block text-sm font-medium mb-1.5 text-slate-700 dark:text-slate-300">Nouveau mot de passe</label>
                                <input v-model="passwordForm.password" type="password" required class="w-full text-sm px-4 py-2.5 rounded-xl border bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-600/50 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition" />
                                <p v-if="page.props.errors?.password" class="text-red-500 text-xs mt-1">{{ page.props.errors.password }}</p>
                            </div>
                            <div>
                                <label class="block text-sm font-medium mb-1.5 text-slate-700 dark:text-slate-300">Confirmer</label>
                                <input v-model="passwordForm.password_confirmation" type="password" required class="w-full text-sm px-4 py-2.5 rounded-xl border bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-600/50 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition" />
                            </div>
                        </div>

                        <div class="flex justify-end pt-2">
                            <button type="submit" :disabled="savingPassword" class="px-6 py-2.5 rounded-xl text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 disabled:from-slate-600 disabled:to-slate-600 transition-all shadow-lg shadow-blue-500/20 disabled:shadow-none">
                                {{ savingPassword ? 'Modification...' : 'Modifier le mot de passe' }}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </AppLayout>
</template>
