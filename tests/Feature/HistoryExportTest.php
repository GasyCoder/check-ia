<?php

namespace Tests\Feature;

use App\Models\Detection;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class HistoryExportTest extends TestCase
{
    use RefreshDatabase;

    public function test_user_can_export_filtered_history_in_all_supported_formats(): void
    {
        $user = User::factory()->create();
        $otherUser = User::factory()->create();

        $matchingDetection = Detection::create([
            'user_id' => $user->id,
            'text_excerpt' => 'Rapport energie test',
            'full_text' => 'Contenu complet energie',
            'file_name' => 'energie.txt',
            'ai_probability' => 44.8,
            'chunk_results' => null,
            'chunk_count' => 0,
        ]);

        Detection::create([
            'user_id' => $user->id,
            'text_excerpt' => 'Analyse agriculture',
            'full_text' => 'Contenu complet agriculture',
            'file_name' => 'agri.txt',
            'ai_probability' => 12.5,
            'chunk_results' => null,
            'chunk_count' => 0,
        ]);

        Detection::create([
            'user_id' => $otherUser->id,
            'text_excerpt' => 'Rapport energie externe',
            'full_text' => 'Contenu externe',
            'file_name' => 'external.txt',
            'ai_probability' => 91.2,
            'chunk_results' => null,
            'chunk_count' => 0,
        ]);

        foreach (['json', 'csv', 'txt'] as $format) {
            $response = $this->actingAs($user)->get("/history/export/{$format}?search=energie");

            $response->assertOk();
            $this->assertStringContainsString(".{$format}", $response->headers->get('content-disposition'));

            $content = $response->streamedContent();

            $this->assertStringContainsString((string) $matchingDetection->uuid, $content);
            $this->assertStringContainsString('Rapport energie test', $content);
            $this->assertStringNotContainsString('Analyse agriculture', $content);
            $this->assertStringNotContainsString('Rapport energie externe', $content);
        }
    }
}
