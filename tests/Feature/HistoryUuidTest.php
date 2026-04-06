<?php

namespace Tests\Feature;

use App\Models\Detection;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class HistoryUuidTest extends TestCase
{
    use RefreshDatabase;

    public function test_user_can_fetch_own_detection_by_uuid(): void
    {
        $user = User::factory()->create();

        $detection = Detection::create([
            'user_id' => $user->id,
            'text_excerpt' => 'Extrait de test',
            'full_text' => 'Contenu complet du test',
            'ai_probability' => 42.5,
            'chunk_results' => null,
            'chunk_count' => 0,
        ]);

        $response = $this->actingAs($user)->get("/history/{$detection->uuid}");

        $response->assertOk()
            ->assertJson([
                'full_text' => 'Contenu complet du test',
                'ai_probability' => 42.5,
                'chunk_count' => 0,
            ]);
    }
}
