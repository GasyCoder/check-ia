<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Storage;
use Illuminate\Validation\Rules\Password;
use Inertia\Inertia;

class ProfileController extends Controller
{
    public function show(Request $request)
    {
        $user = $request->user();

        return Inertia::render('Profile', [
            'user' => [
                ...$user->only('id', 'name', 'first_name', 'email', 'birth_date', 'status', 'affiliation', 'role', 'email_verified_at', 'created_at'),
                'avatar_url' => $user->avatar ? Storage::url($user->avatar) : null,
            ],
            'statusOptions' => ['Enseignant', 'Doctorant', 'Etudiant', 'Rédacteur', 'Chercheur', 'Journaliste', 'Autre'],
        ]);
    }

    public function update(Request $request)
    {
        $request->validate([
            'name' => 'required|string|max:255',
            'first_name' => 'nullable|string|max:255',
            'birth_date' => 'nullable|date|before:today',
            'status' => 'nullable|string|max:255',
            'affiliation' => 'nullable|string|max:255',
        ]);

        $request->user()->update($request->only('name', 'first_name', 'birth_date', 'status', 'affiliation'));

        return back()->with('success', 'Profil mis à jour avec succès.');
    }

    public function updateAvatar(Request $request)
    {
        $request->validate([
            'avatar' => 'required|image|mimes:jpg,jpeg,png,webp|max:2048',
        ]);

        $user = $request->user();

        // Delete old avatar
        if ($user->avatar) {
            Storage::disk('public')->delete($user->avatar);
        }

        $path = $request->file('avatar')->store('avatars', 'public');
        $user->update(['avatar' => $path]);

        return back()->with('success', 'Photo de profil mise à jour.');
    }

    public function deleteAvatar(Request $request)
    {
        $user = $request->user();

        if ($user->avatar) {
            Storage::disk('public')->delete($user->avatar);
            $user->update(['avatar' => null]);
        }

        return back()->with('success', 'Photo de profil supprimée.');
    }

    public function updatePassword(Request $request)
    {
        $request->validate([
            'current_password' => 'required',
            'password' => ['required', 'confirmed', Password::min(8)],
        ]);

        if (!Hash::check($request->current_password, $request->user()->password)) {
            return back()->withErrors(['current_password' => 'Le mot de passe actuel est incorrect.']);
        }

        $request->user()->update(['password' => $request->password]);

        return back()->with('success', 'Mot de passe modifié avec succès.');
    }
}
