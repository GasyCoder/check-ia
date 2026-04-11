<?php

namespace App\Http\Controllers;

use App\Models\Humanization;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\RateLimiter;
use Illuminate\Support\Str;
use PhpOffice\PhpWord\IOFactory as WordIOFactory;
use PhpOffice\PhpWord\PhpWord;

class HumanizeController extends Controller
{
    private const AI_SERVICE_URL = 'http://localhost:8000';
    private const SHARE_TTL_MINUTES = 60;

    private function normalizeIntensity(string $intensity): string
    {
        return match ($intensity) {
            'easy' => 'light',
            'light' => 'light',
            'aggressive' => 'aggressive',
            default => 'medium',
        };
    }

    /**
     * Humanize text via the Python AI service.
     *
     * Rate limited to 10 requests per hour per user.
     */
    public function humanize(Request $request)
    {
        $request->validate([
            'text' => 'required|string|min:10|max:50000',
            'intensity' => 'sometimes|string|in:easy,light,medium,aggressive',
            'mode' => 'sometimes|string|max:50',
            'task_type' => 'sometimes|string|in:humanize',
            'segments' => 'sometimes|array',
            'segments.*.text' => 'required_with:segments|string|min:1',
        ]);

        $user = $request->user();

        // Rate limiting: 10 humanizations per hour per user, except superadmins.
        if (!$user || !$user->isSuperAdmin()) {
            $key = 'humanize:' . auth()->id();
            if (RateLimiter::tooManyAttempts($key, 10)) {
                $seconds = RateLimiter::availableIn($key);
                return response()->json([
                    'error' => "Limite d'humanisations atteinte. Réessayez dans " . ceil($seconds / 60) . " minutes.",
                ], 429);
            }

            RateLimiter::hit($key, 3600);
        }

        $text = $request->input('text');
        $requestedIntensity = $request->input('intensity', 'medium');
        $intensity = $this->normalizeIntensity($requestedIntensity);
        $mode = $request->input('mode', 'manual-humanize');
        $taskType = $request->input('task_type', 'humanize');
        $segments = collect($request->input('segments', []))
            ->map(function ($segment) {
                return [
                    'id' => is_array($segment) ? ($segment['id'] ?? null) : null,
                    'text' => trim((string) (is_array($segment) ? ($segment['text'] ?? '') : '')),
                ];
            })
            ->filter(fn ($segment) => $segment['text'] !== '')
            ->values()
            ->all();

        try {
            $payload = [
                'text' => mb_substr($text, 0, 50000),
                'intensity' => $intensity,
                'mode' => $mode,
                'task_type' => $taskType,
            ];

            if (!empty($segments)) {
                $payload['segments'] = $segments;
            }

            $response = Http::timeout(120)->post(self::AI_SERVICE_URL . '/humanize', $payload);

            if ($response->successful()) {
                $humanizedText = $response->json('humanized_text', '');

                // Save to history
                Humanization::create([
                    'user_id' => auth()->id(),
                    'original_text' => $text,
                    'humanized_text' => $humanizedText,
                    'intensity' => $intensity,
                ]);

                return response()->json([
                    'humanized_text' => $humanizedText,
                    'original_length' => $response->json('original_length'),
                    'humanized_length' => $response->json('humanized_length'),
                    'intensity' => $intensity,
                    'mode' => $mode,
                    'task_type' => $taskType,
                    'segments' => $response->json('segments', []),
                ]);
            }

            \Log::error('Humanize service error', [
                'status' => $response->status(),
                'body' => $response->body(),
            ]);

            return response()->json([
                'error' => 'Le service d\'humanisation a retourné une erreur (code ' . $response->status() . ').',
            ], 502);
        } catch (\Exception $e) {
            \Log::error('Humanize service exception', ['message' => $e->getMessage()]);
            return response()->json([
                'error' => 'Le service d\'humanisation est indisponible: ' . $e->getMessage(),
            ], 503);
        }
    }

    public function createShareLink(Request $request)
    {
        $request->validate([
            'text' => 'required|string|min:10|max:50000',
            'intensity' => 'sometimes|string|in:easy,light,medium,aggressive',
        ]);

        $token = (string) Str::uuid();

        Cache::put(
            "shared-humanization:{$token}",
            [
                'text' => $request->input('text'),
                'intensity' => $request->input('intensity', 'medium'),
                'created_at' => now()->toIso8601String(),
            ],
            now()->addMinutes(self::SHARE_TTL_MINUTES),
        );

        return response()->json([
            'share_url' => url("/shared/humanization/{$token}"),
            'expires_in_minutes' => self::SHARE_TTL_MINUTES,
        ]);
    }

    public function showShared(string $token)
    {
        $payload = Cache::get("shared-humanization:{$token}");

        if (!$payload || empty($payload['text'])) {
            abort(404);
        }

        $safeText = nl2br(e((string) $payload['text']));
        $safeIntensity = e((string) ($payload['intensity'] ?? 'medium'));
        $safeCreatedAt = e((string) ($payload['created_at'] ?? now()->toIso8601String()));

        return response(<<<HTML
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Reinia Pro - Texte humanisé partagé</title>
  <style>
    body { margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: #09090b; color: #f4f4f5; }
    .shell { max-width: 960px; margin: 0 auto; padding: 48px 20px 72px; }
    .badge { display: inline-flex; align-items: center; gap: 8px; border: 1px solid rgba(74, 222, 128, 0.22); background: rgba(34, 197, 94, 0.12); color: #86efac; border-radius: 999px; padding: 8px 14px; font-size: 12px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; }
    .card { margin-top: 20px; border: 1px solid rgba(74, 222, 128, 0.18); background: rgba(24, 24, 27, 0.88); border-radius: 28px; padding: 28px; box-shadow: 0 18px 80px rgba(0, 0, 0, 0.34); }
    h1 { margin: 16px 0 10px; font-size: clamp(30px, 5vw, 44px); line-height: 1.05; }
    p.meta { margin: 0; color: #a1a1aa; font-size: 14px; }
    article { margin-top: 20px; font-size: 17px; line-height: 1.9; color: #fafafa; }
  </style>
</head>
<body>
  <main class="shell">
    <span class="badge">Reinia Pro · {$safeIntensity}</span>
    <h1>Texte humanisé partagé</h1>
    <p class="meta">Lien temporaire généré le {$safeCreatedAt}</p>
    <section class="card">
      <article>{$safeText}</article>
    </section>
  </main>
</body>
</html>
HTML
        )->header('Content-Type', 'text/html; charset=UTF-8');
    }

    public function export(Request $request)
    {
        $request->validate([
            'text' => 'required|string|min:10|max:50000',
            'format' => 'required|string|in:txt,docx',
        ]);

        $text = trim((string) $request->input('text'));
        $format = $request->input('format');
        $baseName = 'reinia-humanise-' . now()->format('Ymd-His');

        if ($format === 'txt') {
            return response()->streamDownload(function () use ($text) {
                echo $text;
            }, "{$baseName}.txt", [
                'Content-Type' => 'text/plain; charset=UTF-8',
            ]);
        }

        $phpWord = new PhpWord();
        $section = $phpWord->addSection([
            'marginTop' => 1200,
            'marginRight' => 1200,
            'marginBottom' => 1200,
            'marginLeft' => 1200,
        ]);

        foreach (preg_split("/\\R/u", $text) as $paragraph) {
            $section->addText($paragraph === '' ? ' ' : $paragraph, [
                'name' => 'Arial',
                'size' => 11,
            ]);
        }

        $tmpPath = tempnam(sys_get_temp_dir(), 'reinia_docx_');
        $docxPath = $tmpPath . '.docx';
        @rename($tmpPath, $docxPath);

        $writer = WordIOFactory::createWriter($phpWord, 'Word2007');
        $writer->save($docxPath);

        return response()->download($docxPath, "{$baseName}.docx")->deleteFileAfterSend(true);
    }
}
