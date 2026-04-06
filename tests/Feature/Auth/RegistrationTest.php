<?php

namespace Tests\Feature\Auth;

use App\Models\User;
use Illuminate\Auth\Notifications\VerifyEmail;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Notification;
use Tests\TestCase;

class RegistrationTest extends TestCase
{
    use RefreshDatabase;

    public function test_registration_sends_verification_email_and_redirects_to_notice(): void
    {
        Notification::fake();

        $response = $this->post('/register', [
            'name' => 'Ada Lovelace',
            'email' => 'ada@example.com',
            'password' => 'password123',
            'password_confirmation' => 'password123',
        ]);

        $user = User::where('email', 'ada@example.com')->first();

        $this->assertNotNull($user);
        $this->assertNull($user->email_verified_at);
        $this->assertAuthenticatedAs($user);
        $response->assertRedirect(route('verification.notice'));
        Notification::assertSentTo($user, VerifyEmail::class);
    }
}
