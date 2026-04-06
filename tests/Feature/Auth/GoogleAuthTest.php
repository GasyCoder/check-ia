<?php

namespace Tests\Feature\Auth;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Laravel\Socialite\Facades\Socialite;
use Laravel\Socialite\Two\User as SocialiteUser;
use Mockery;
use Tests\TestCase;

class GoogleAuthTest extends TestCase
{
    use RefreshDatabase;

    public function test_google_callback_verifies_an_existing_unverified_user(): void
    {
        $user = User::create([
            'name' => 'Gasy Coder',
            'email' => 'gasycoder@gmail.com',
            'password' => 'password123',
            'role' => 'user',
        ]);

        $googleUser = Mockery::mock(SocialiteUser::class);
        $googleUser->shouldReceive('getId')->andReturn('google-123');
        $googleUser->shouldReceive('getEmail')->andReturn('gasycoder@gmail.com');
        $googleUser->shouldReceive('getName')->andReturn('Gasy Coder');
        $googleUser->shouldReceive('getAvatar')->andReturn('https://example.com/avatar.jpg');

        Socialite::shouldReceive('driver->user')->andReturn($googleUser);

        $response = $this->get('/auth/google/callback');

        $response->assertRedirect('/app');
        $this->assertAuthenticatedAs($user->fresh());
        $this->assertNotNull($user->fresh()->email_verified_at);
        $this->assertSame('google-123', $user->fresh()->google_id);
    }
}
