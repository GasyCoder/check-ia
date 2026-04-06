<?php

use App\Http\Controllers\AdminController;
use App\Http\Controllers\AuthController;
use App\Http\Controllers\DetectionController;
use App\Http\Controllers\HistoryController;
use App\Http\Controllers\ProfileController;
use App\Http\Controllers\VerificationController;
use Illuminate\Support\Facades\Route;
use Inertia\Inertia;

// ─── Public ───
Route::get('/', function () {
    if (auth()->check()) {
        return redirect('/app');
    }
    return Inertia::render('Landing');
})->name('landing');

// Guest analysis (limited to 20k chars, no auth)
Route::post('/guest/analyze-text', [DetectionController::class, 'guestAnalyze'])
    ->middleware('throttle:10,1');

// ─── Auth (guest only) ───
Route::middleware('guest')->group(function () {
    Route::get('/login', [AuthController::class, 'showLogin'])->name('login');
    Route::post('/login', [AuthController::class, 'login']);
    Route::get('/register', [AuthController::class, 'showRegister'])->name('register');
    Route::post('/register', [AuthController::class, 'register']);

    // Google OAuth
    Route::get('/auth/google', [AuthController::class, 'redirectToGoogle'])->name('google.redirect');
    Route::get('/auth/google/callback', [AuthController::class, 'handleGoogleCallback']);
});

// ─── Auth (not necessarily verified) ───
Route::middleware('auth')->group(function () {
    Route::post('/logout', [AuthController::class, 'logout'])->name('logout');

    // Email verification
    Route::get('/email/verify', [VerificationController::class, 'notice'])->name('verification.notice');
    Route::get('/email/verify/{id}/{hash}', [VerificationController::class, 'verify'])
        ->middleware('signed')->name('verification.verify');
    Route::post('/email/resend', [VerificationController::class, 'resend'])
        ->middleware('throttle:6,1')->name('verification.send');
});

// ─── Verified routes (main app) ───
Route::middleware(['auth', 'verified'])->group(function () {
    Route::get('/app', function () {
        return Inertia::render('Welcome');
    })->name('home');

    Route::post('/analyze-text', [DetectionController::class, 'analyze']);
    Route::post('/analyze-file', [DetectionController::class, 'analyzeFile']);

    Route::get('/faq', function () {
        return Inertia::render('Faq');
    })->name('faq');

    Route::get('/history', [HistoryController::class, 'index'])->name('history');
    Route::get('/history/sidebar', [HistoryController::class, 'sidebar'])->name('history.sidebar');
    Route::get('/history/{id}', [HistoryController::class, 'show'])->name('history.show');
    Route::delete('/history/{id}', [HistoryController::class, 'destroy'])->name('history.destroy');

    Route::get('/profile', [ProfileController::class, 'show'])->name('profile');
    Route::put('/profile', [ProfileController::class, 'update'])->name('profile.update');
    Route::post('/profile/avatar', [ProfileController::class, 'updateAvatar'])->name('profile.avatar');
    Route::delete('/profile/avatar', [ProfileController::class, 'deleteAvatar'])->name('profile.avatar.delete');
    Route::put('/profile/password', [ProfileController::class, 'updatePassword'])->name('profile.password');

    // Admin
    Route::middleware('can:admin')->prefix('admin')->group(function () {
        Route::get('/', [AdminController::class, 'dashboard'])->name('admin');
        Route::put('/users/{user}/role', [AdminController::class, 'updateRole']);
        Route::delete('/users/{user}', [AdminController::class, 'destroyUser']);
    });
});
