<?php

namespace App\Http\Controllers;

use App\Models\Detection;
use App\Models\Humanization;
use App\Services\TextPreprocessor;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\RateLimiter;
use PhpOffice\PhpWord\IOFactory as WordIOFactory;
use Smalot\PdfParser\Parser as PdfParser;

class DetectionController extends Controller
{
    private const AI_SERVICE_URL = 'http://localhost:8000';
    private const CHUNK_THRESHOLD = 2000; // chars: above this, use chunk analysis
    private const HUMANIZE_TEXT_LIMIT = 50000;
    private const HUMANIZE_MODES = ['rapid', 'reasoning', 'pro'];

    private function normalizeIntensity(?string $intensity): string
    {
        return match ($intensity) {
            'easy', 'light' => 'light',
            'aggressive' => 'aggressive',
            default => 'medium',
        };
    }

    private function normalizeProbability(mixed $value): float
    {
        $probability = is_numeric($value) ? (float) $value : 0.0;

        if ($probability >= 0 && $probability <= 1) {
            $probability *= 100;
        }

        return round(max(0, min(100, $probability)), 1);
    }

    private function normalizeSentences(array $sentences, string $prefix = 'sentence'): array
    {
        $normalized = array_values(array_filter(array_map(function ($sentence) {
            if (!is_array($sentence)) {
                return null;
            }

            $text = trim((string) ($sentence['text'] ?? ''));

            if ($text === '') {
                return null;
            }

            return [
                ...$sentence,
                'text' => $text,
                'score' => $this->normalizeProbability($sentence['score'] ?? 0),
            ];
        }, $sentences)));

        return array_map(function ($sentence, $index) use ($prefix) {
            $sentence['id'] = $sentence['id'] ?? "{$prefix}-{$index}";

            return $sentence;
        }, $normalized, array_keys($normalized));
    }

    private function normalizeChunkResults(array $chunks): array
    {
        $normalizedChunks = [];

        foreach (array_values($chunks) as $chunkIndex => $chunk) {
            if (!is_array($chunk)) {
                continue;
            }

            $chunk['ai_probability'] = $this->normalizeProbability($chunk['ai_probability'] ?? 0);

            if (isset($chunk['score_roberta']) && is_numeric($chunk['score_roberta'])) {
                $chunk['score_roberta'] = (float) $chunk['score_roberta'];
            }

            if (isset($chunk['score_ppl']) && is_numeric($chunk['score_ppl'])) {
                $chunk['score_ppl'] = (float) $chunk['score_ppl'];
            }

            if (isset($chunk['sentences']) && is_array($chunk['sentences'])) {
                $chunk['sentences'] = $this->normalizeSentences($chunk['sentences'], "chunk-{$chunkIndex}-sentence");
            }

            $normalizedChunks[] = $chunk;
        }

        return $normalizedChunks;
    }

    private function shouldAutoHumanize(string $mode): bool
    {
        return in_array($mode, self::HUMANIZE_MODES, true);
    }

    private function mapModeToIntensity(string $mode): string
    {
        return match ($mode) {
            'rapid' => 'light',
            'reasoning' => 'medium',
            'pro' => 'aggressive',
            default => 'medium',
        };
    }

    private function humanizationErrorPayload(string $mode, string $message, string $status = 'failed'): array
    {
        return [
            'status' => $status,
            'mode' => $mode,
            'intensity' => $this->mapModeToIntensity($mode),
            'error' => $message,
            'humanized_text' => '',
            'segments' => [],
            'reanalyzed_score' => null,
            'estimated_score_before' => null,
            'estimated_score_after' => null,
        ];
    }

    private function collectHumanizeSegments(array $analysisData): array
    {
        if (!empty($analysisData['sentences']) && is_array($analysisData['sentences'])) {
            return array_values(array_filter(array_map(function ($sentence, $index) {
                if (!is_array($sentence)) {
                    return null;
                }

                $text = trim((string) ($sentence['text'] ?? ''));

                if ($text === '') {
                    return null;
                }

                return [
                    'id' => $sentence['id'] ?? "sentence-{$index}",
                    'text' => $text,
                ];
            }, $analysisData['sentences'], array_keys($analysisData['sentences']))));
        }

        $segments = [];

        foreach (($analysisData['chunks'] ?? []) as $chunkIndex => $chunk) {
            if (!is_array($chunk) || empty($chunk['sentences']) || !is_array($chunk['sentences'])) {
                continue;
            }

            foreach ($chunk['sentences'] as $sentenceIndex => $sentence) {
                if (!is_array($sentence)) {
                    continue;
                }

                $text = trim((string) ($sentence['text'] ?? ''));

                if ($text === '') {
                    continue;
                }

                $segments[] = [
                    'id' => $sentence['id'] ?? "chunk-{$chunkIndex}-sentence-{$sentenceIndex}",
                    'text' => $text,
                ];
            }
        }

        return $segments;
    }

    private function appendHumanization(Request $request, array $analysisData, string $text, string $mode): array
    {
        if (!$this->shouldAutoHumanize($mode)) {
            return $analysisData;
        }

        $analysisData['mode'] = $mode;

        if (mb_strlen($text) > self::HUMANIZE_TEXT_LIMIT) {
            $analysisData['humanization'] = $this->humanizationErrorPayload(
                $mode,
                'L’humanisation instantanée est limitée à 50 000 caractères. Analyse disponible, humanisation à lancer sur un extrait plus court.',
                'skipped',
            );

            return $analysisData;
        }

        $user = $request->user();

        if (!$user || !$user->isSuperAdmin()) {
            $key = 'humanize:' . auth()->id();

            if (RateLimiter::tooManyAttempts($key, 10)) {
                $seconds = RateLimiter::availableIn($key);
                $analysisData['humanization'] = $this->humanizationErrorPayload(
                    $mode,
                    "Limite d'humanisations atteinte. Réessayez dans " . ceil($seconds / 60) . " minutes.",
                    'rate_limited',
                );

                return $analysisData;
            }

            RateLimiter::hit($key, 3600);
        }

        $intensity = $this->mapModeToIntensity($mode);
        $segments = $this->collectHumanizeSegments($analysisData);

        try {
            $payload = [
                'text' => mb_substr($text, 0, self::HUMANIZE_TEXT_LIMIT),
                'intensity' => $intensity,
                'mode' => $mode,
            ];

            if (!empty($segments)) {
                $payload['segments'] = $segments;
            }

            $response = Http::timeout(120)->post(self::AI_SERVICE_URL . '/humanize', $payload);

            if (!$response->successful()) {
                \Log::error('Inline humanization service error', [
                    'status' => $response->status(),
                    'body' => $response->body(),
                    'mode' => $mode,
                ]);

                $analysisData['humanization'] = $this->humanizationErrorPayload(
                    $mode,
                    'Réécriture indisponible pour ce lancement. L’analyse reste affichée.',
                );

                return $analysisData;
            }

            $humanizedText = (string) $response->json('humanized_text', '');

            if ($humanizedText !== '') {
                Humanization::create([
                    'user_id' => auth()->id(),
                    'original_text' => $text,
                    'humanized_text' => $humanizedText,
                    'intensity' => $intensity,
                ]);
            }

            $analysisData['humanization'] = [
                'status' => 'completed',
                'mode' => $mode,
                'intensity' => $intensity,
                'humanized_text' => $humanizedText,
                'segments' => $response->json('segments', []),
                'reanalyzed_score' => null,
                'estimated_score_before' => $response->json('estimated_score_before'),
                'estimated_score_after' => $response->json('estimated_score_after'),
                'retry_count' => $response->json('retry_count'),
                'used_fallback' => $response->json('used_fallback'),
            ];

            return $analysisData;
        } catch (\Exception $e) {
            \Log::error('Inline humanization exception', [
                'mode' => $mode,
                'message' => $e->getMessage(),
            ]);

            $analysisData['humanization'] = $this->humanizationErrorPayload(
                $mode,
                'Réécriture indisponible pour ce lancement. L’analyse reste affichée.',
            );

            return $analysisData;
        }
    }

    /**
     * Guest analysis: limited to 20k chars, no history saved.
     */
    public function guestAnalyze(Request $request)
    {
        $request->validate([
            'text' => 'required|string|min:10|max:20000',
        ]);

        $text = $request->input('text');

        try {
            $response = Http::timeout(120)->post(self::AI_SERVICE_URL . '/predict', [
                'text' => mb_substr($text, 0, 15000),
            ]);

            if ($response->successful()) {
                return response()->json([
                    'result' => $this->normalizeProbability($response->json('ai_probability')),
                    'sentences' => $this->normalizeSentences($response->json('sentences', [])),
                ]);
            }

            return response()->json(['error' => 'Erreur du service IA.'], 502);
        } catch (\Exception $e) {
            return response()->json(['error' => 'Service IA indisponible.'], 503);
        }
    }

    public function analyze(Request $request)
    {
        $request->validate([
            'text' => 'required|string|min:10|max:1500000',
            'mode' => 'sometimes|string|in:detect,rapid,reasoning,pro',
            'task_type' => 'sometimes|string|in:detect,humanize',
            'intensity' => 'sometimes|string|in:easy,light,medium,aggressive',
        ]);

        $text = $request->input('text');
        $mode = $request->input('mode', 'detect');
        $intensity = $this->normalizeIntensity($request->input('intensity'));

        $response = mb_strlen($text) > self::CHUNK_THRESHOLD
            ? $this->analyzeWithChunks($text, null, $mode, 'detect', $intensity)
            : $this->analyzeSingle($text, null, $mode, 'detect', $intensity);

        if (!$this->shouldAutoHumanize($mode) || !$response instanceof \Illuminate\Http\JsonResponse || $response->getStatusCode() >= 400) {
            return $response;
        }

        $data = $response->getData(true);

        return response()->json(
            $this->appendHumanization($request, $data, $data['analyzed_text'] ?? $text, $mode),
            $response->getStatusCode(),
        );
    }

    public function analyzeFile(Request $request)
    {
        $request->validate([
            'file' => 'required|file|max:25600|mimes:txt,pdf,docx',
            'mode' => 'sometimes|string|in:detect,rapid,reasoning,pro',
            'task_type' => 'sometimes|string|in:detect,humanize',
            'intensity' => 'sometimes|string|in:easy,light,medium,aggressive',
        ]);

        $file = $request->file('file');
        $extension = strtolower($file->getClientOriginalExtension());
        $mode = $request->input('mode', 'detect');
        $intensity = $this->normalizeIntensity($request->input('intensity'));

        try {
            $rawText = match ($extension) {
                'txt' => file_get_contents($file->getRealPath()),
                'pdf' => $this->extractPdf($file->getRealPath()),
                'docx' => $this->extractDocx($file->getRealPath()),
                default => null,
            };
        } catch (\Exception $e) {
            \Log::error('File extraction error', ['file' => $file->getClientOriginalName(), 'error' => $e->getMessage()]);
            return response()->json(['error' => 'Impossible de lire le contenu du fichier: ' . $e->getMessage()], 422);
        }

        if (!$rawText || mb_strlen(trim($rawText)) < 10) {
            return response()->json(['error' => 'Le fichier ne contient pas assez de texte (minimum 10 caractères).'], 422);
        }

        // Apply smart preprocessing pipeline
        $processed = TextPreprocessor::process($rawText);
        $cleanText = $processed['text'];
        $chunks = $processed['chunks'];

        if (mb_strlen($cleanText) < 10) {
            return response()->json(['error' => 'Après nettoyage, le fichier ne contient pas assez de texte exploitable.'], 422);
        }

        $fileName = $file->getClientOriginalName();

        if (count($chunks) > 1) {
            $result = $this->callChunkService($chunks, $cleanText, $fileName, $mode, 'detect', $intensity);
        } else {
            $result = $this->callSingleService($cleanText, $fileName, $mode, 'detect', $intensity);
        }

        if ($result instanceof \Illuminate\Http\JsonResponse) {
            $data = $result->getData(true);
            $data['extracted_text'] = $cleanText;
            $data['preprocessing'] = $processed['stats'];

            if ($this->shouldAutoHumanize($mode) && $result->getStatusCode() < 400) {
                $data = $this->appendHumanization($request, $data, $cleanText, $mode);
            }

            return response()->json($data, $result->getStatusCode());
        }

        return $result;
    }

    /**
     * Simple analysis for short texts.
     */
    private function analyzeSingle(
        string $text,
        ?string $fileName = null,
        string $mode = 'detect',
        string $taskType = 'detect',
        string $intensity = 'medium',
    )
    {
        return $this->callSingleService($text, $fileName, $mode, $taskType, $intensity);
    }

    /**
     * Chunk-based analysis for long texts.
     */
    private function analyzeWithChunks(
        string $text,
        ?string $fileName = null,
        string $mode = 'detect',
        string $taskType = 'detect',
        string $intensity = 'medium',
    )
    {
        $processed = TextPreprocessor::process($text);
        $chunks = $processed['chunks'];

        if (count($chunks) <= 1) {
            return $this->callSingleService($processed['text'], $fileName, $mode, $taskType, $intensity);
        }

        return $this->callChunkService($chunks, $processed['text'], $fileName, $mode, $taskType, $intensity);
    }

    private function callSingleService(
        string $text,
        ?string $fileName = null,
        string $mode = 'detect',
        string $taskType = 'detect',
        string $intensity = 'medium',
    )
    {
        try {
            $response = Http::timeout(120)->post(self::AI_SERVICE_URL . '/predict', [
                'text' => mb_substr($text, 0, 15000),
                'mode' => $mode,
                'task_type' => $taskType,
                'intensity' => $intensity,
            ]);

            if ($response->successful()) {
                $probability = $this->normalizeProbability($response->json('ai_probability'));
                $sentences = $this->normalizeSentences($response->json('sentences', []));

                $payload = [
                    'user_id' => auth()->id(),
                    'text_excerpt' => mb_substr($text, 0, 200),
                    'full_text' => $text,
                    'file_name' => $fileName,
                    'ai_probability' => $probability,
                    'chunk_results' => null,
                    'chunk_count' => 0,
                ];

                if (Detection::hasUuidColumn()) {
                    $payload['uuid'] = (string) \Illuminate\Support\Str::uuid();
                }

                Detection::create($payload);

                return response()->json([
                    'result' => $probability,
                    'analyzed_text' => $text,
                    'sentences' => $sentences,
                    'mode' => $mode,
                    'task_type' => $taskType,
                    'intensity' => $intensity,
                ]);
            }

            \Log::error('AI service error', ['status' => $response->status(), 'body' => $response->body()]);
            return response()->json(['error' => 'Le service IA a retourné une erreur (code ' . $response->status() . ').'], 502);
        } catch (\Exception $e) {
            \Log::error('AI service exception', ['message' => $e->getMessage()]);
            return response()->json([
                'error' => 'Le service de détection IA est indisponible: ' . $e->getMessage(),
            ], 503);
        }
    }

    private function callChunkService(
        array $chunks,
        string $fullText,
        ?string $fileName = null,
        string $mode = 'detect',
        string $taskType = 'detect',
        string $intensity = 'medium',
    )
    {
        try {
            // Limit chunks to avoid timeout (max ~20 chunks)
            $chunksToSend = array_slice($chunks, 0, 20);

            $response = Http::timeout(300)->post(self::AI_SERVICE_URL . '/predict-chunks', [
                'chunks' => $chunksToSend,
                'mode' => $mode,
                'task_type' => $taskType,
                'intensity' => $intensity,
            ]);

            if ($response->successful()) {
                $data = $response->json();
                $probability = $this->normalizeProbability($data['ai_probability'] ?? 0);
                $chunkResults = $this->normalizeChunkResults($data['chunks'] ?? []);

                $payload = [
                    'user_id' => auth()->id(),
                    'text_excerpt' => mb_substr($fullText, 0, 200),
                    'full_text' => $fullText,
                    'file_name' => $fileName,
                    'ai_probability' => $probability,
                    'chunk_results' => $chunkResults,
                    'chunk_count' => count($chunkResults),
                ];

                if (Detection::hasUuidColumn()) {
                    $payload['uuid'] = (string) \Illuminate\Support\Str::uuid();
                }

                Detection::create($payload);

                return response()->json([
                    'result' => $probability,
                    'analyzed_text' => $fullText,
                    'chunks' => $chunkResults,
                    'chunk_count' => count($chunkResults),
                    'mode' => $mode,
                    'task_type' => $taskType,
                    'intensity' => $intensity,
                ]);
            }

            \Log::error('AI chunk service error', ['status' => $response->status(), 'body' => $response->body()]);
            return response()->json(['error' => 'Le service IA a retourné une erreur (code ' . $response->status() . ').'], 502);
        } catch (\Exception $e) {
            \Log::error('AI chunk service exception', ['message' => $e->getMessage()]);
            return response()->json([
                'error' => 'Le service de détection IA est indisponible: ' . $e->getMessage(),
            ], 503);
        }
    }

    private function extractPdf(string $path): string
    {
        $parser = new PdfParser();
        $pdf = $parser->parseFile($path);
        return $pdf->getText();
    }

    private function extractDocx(string $path): string
    {
        $phpWord = WordIOFactory::load($path, 'Word2007');
        $text = '';
        foreach ($phpWord->getSections() as $section) {
            foreach ($section->getElements() as $element) {
                if (method_exists($element, 'getText')) {
                    $text .= $element->getText() . "\n";
                }
                // Handle tables
                if ($element instanceof \PhpOffice\PhpWord\Element\Table) {
                    foreach ($element->getRows() as $row) {
                        $cells = [];
                        foreach ($row->getCells() as $cell) {
                            $cellText = '';
                            foreach ($cell->getElements() as $cellElement) {
                                if (method_exists($cellElement, 'getText')) {
                                    $cellText .= $cellElement->getText() . ' ';
                                }
                            }
                            $cells[] = trim($cellText);
                        }
                        $text .= implode(' | ', $cells) . "\n";
                    }
                }
            }
        }
        return $text;
    }
}
