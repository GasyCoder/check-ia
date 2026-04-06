<script setup>
import { ref } from 'vue';
import { router } from '@inertiajs/vue3';
import AppLayout from '../../Layouts/AppLayout.vue';

const props = defineProps({
    users: Array,
});

const confirmDelete = ref(null);
const search = ref('');

const filteredUsers = ref(props.users);

function filterUsers() {
    const q = search.value.toLowerCase();
    filteredUsers.value = props.users.filter(u =>
        u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
    );
}

function toggleRole(user) {
    router.put(`/admin/users/${user.id}/role`, {
        role: user.role === 'superadmin' ? 'user' : 'superadmin',
    }, { preserveScroll: true });
}

function deleteUser(user) {
    if (confirmDelete.value === user.id) {
        router.delete(`/admin/users/${user.id}`, { preserveScroll: true });
        confirmDelete.value = null;
    } else {
        confirmDelete.value = user.id;
        setTimeout(() => { confirmDelete.value = null; }, 3000);
    }
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' });
}
</script>

<template>
    <AppLayout>
        <div class="max-w-5xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
            <!-- Header -->
            <div class="mb-8">
                <h1 class="text-3xl font-bold text-slate-900 dark:text-white">Administration</h1>
                <p class="mt-1 text-slate-500 dark:text-slate-400">Gérez les utilisateurs de la plateforme</p>
            </div>

            <!-- Stats -->
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
                <div class="rounded-xl border p-5 bg-white dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/50">
                    <p class="text-sm text-slate-500 dark:text-slate-400">Total utilisateurs</p>
                    <p class="text-3xl font-bold mt-1 text-slate-900 dark:text-white">{{ users.length }}</p>
                </div>
                <div class="rounded-xl border p-5 bg-white dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/50">
                    <p class="text-sm text-slate-500 dark:text-slate-400">Super Admins</p>
                    <p class="text-3xl font-bold mt-1 text-violet-600 dark:text-violet-400">{{ users.filter(u => u.role === 'superadmin').length }}</p>
                </div>
                <div class="rounded-xl border p-5 bg-white dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/50">
                    <p class="text-sm text-slate-500 dark:text-slate-400">Utilisateurs</p>
                    <p class="text-3xl font-bold mt-1 text-blue-600 dark:text-blue-400">{{ users.filter(u => u.role === 'user').length }}</p>
                </div>
            </div>

            <!-- Users -->
            <div class="rounded-2xl border overflow-hidden bg-white dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/50">
                <div class="px-6 py-4 border-b flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-slate-200 dark:border-slate-700/50">
                    <h2 class="text-lg font-semibold text-slate-900 dark:text-white">Utilisateurs</h2>
                    <input
                        v-model="search"
                        @input="filterUsers"
                        type="text"
                        placeholder="Rechercher..."
                        class="w-full sm:w-64 text-sm px-3 py-2 rounded-lg border bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-600/50 text-slate-800 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                    />
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full">
                        <thead>
                            <tr class="border-b border-slate-100 dark:border-slate-700/30">
                                <th class="text-left text-xs font-medium uppercase tracking-wider px-6 py-3 text-slate-400">Utilisateur</th>
                                <th class="text-left text-xs font-medium uppercase tracking-wider px-6 py-3 text-slate-400">Rôle</th>
                                <th class="text-left text-xs font-medium uppercase tracking-wider px-6 py-3 text-slate-400">Inscrit le</th>
                                <th class="text-right text-xs font-medium uppercase tracking-wider px-6 py-3 text-slate-400">Actions</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100 dark:divide-slate-700/20">
                            <tr v-for="user in filteredUsers" :key="user.id" class="transition-colors hover:bg-slate-50 dark:hover:bg-slate-700/20">
                                <td class="px-6 py-4">
                                    <div class="flex items-center gap-3">
                                        <div class="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-white text-sm font-bold shrink-0">
                                            {{ user.name.charAt(0).toUpperCase() }}
                                        </div>
                                        <div>
                                            <p class="text-sm font-medium text-slate-900 dark:text-white">{{ user.name }}</p>
                                            <p class="text-xs text-slate-400 dark:text-slate-500">{{ user.email }}</p>
                                        </div>
                                    </div>
                                </td>
                                <td class="px-6 py-4">
                                    <span
                                        class="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-full border"
                                        :class="user.role === 'superadmin'
                                            ? 'bg-violet-50 dark:bg-violet-500/15 text-violet-600 dark:text-violet-400 border-violet-200 dark:border-violet-500/20'
                                            : 'bg-slate-50 dark:bg-slate-500/15 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-500/20'"
                                    >
                                        <span class="w-1.5 h-1.5 rounded-full" :class="user.role === 'superadmin' ? 'bg-violet-500 dark:bg-violet-400' : 'bg-slate-400'"></span>
                                        {{ user.role === 'superadmin' ? 'Super Admin' : 'Utilisateur' }}
                                    </span>
                                </td>
                                <td class="px-6 py-4">
                                    <span class="text-sm text-slate-500 dark:text-slate-400">{{ formatDate(user.created_at) }}</span>
                                </td>
                                <td class="px-6 py-4 text-right">
                                    <div class="flex items-center justify-end gap-2">
                                        <button
                                            @click="toggleRole(user)"
                                            class="text-xs px-3 py-1.5 rounded-lg border transition-colors"
                                            :class="user.role === 'superadmin'
                                                ? 'border-amber-300 dark:border-amber-500/30 text-amber-600 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-500/10'
                                                : 'border-violet-300 dark:border-violet-500/30 text-violet-600 dark:text-violet-400 hover:bg-violet-50 dark:hover:bg-violet-500/10'"
                                        >
                                            {{ user.role === 'superadmin' ? 'Retirer admin' : 'Promouvoir' }}
                                        </button>
                                        <button
                                            @click="deleteUser(user)"
                                            class="text-xs px-3 py-1.5 rounded-lg border transition-colors"
                                            :class="confirmDelete === user.id
                                                ? 'bg-red-500 text-white border-red-500'
                                                : 'border-red-300 dark:border-red-500/30 text-red-500 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10'"
                                        >
                                            {{ confirmDelete === user.id ? 'Confirmer ?' : 'Supprimer' }}
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </AppLayout>
</template>
