<?php

namespace App\Http\Controllers;

use App\Models\Detection;
use App\Services\TextPreprocessor;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use PhpOffice\PhpWord\IOFactory as WordIOFactory;
use Smalot\PdfParser\Parser as PdfParser;

class DetectionController extends Controller
{
    private const AI_SERVICE_URL = 'http://localhost:8000';
    private const CHUNK_THRESHOLD = 2000; // chars: above this, use chunk analysis

    private function normalizeProbability(mixed $value): float
    {
        $probability = is_numeric($value) ? (float) $value : 0.0;

        if ($probability >= 0 && $probability <= 1) {
            $probability *= 100;
        }

        return round(max(0, min(100, $probability)), 1);
    }

    private function normalizeSentences(array $sentences): array
    {
        return array_values(array_filter(array_map(function ($sentence) {
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
    }

    private function normalizeChunkResults(array $chunks): array
    {
        return array_values(array_filter(array_map(function ($chunk) {
            if (!is_array($chunk)) {
                return null;
            }

            $chunk['ai_probability'] = $this->normalizeProbability($chunk['ai_probability'] ?? 0);

            if (isset($chunk['score_roberta']) && is_numeric($chunk['score_roberta'])) {
                $chunk['score_roberta'] = (float) $chunk['score_roberta'];
            }

            if (isset($chunk['score_ppl']) && is_numeric($chunk['score_ppl'])) {
                $chunk['score_ppl'] = (float) $chunk['score_ppl'];
            }

            if (isset($chunk['sentences']) && is_array($chunk['sentences'])) {
                $chunk['sentences'] = $this->normalizeSentences($chunk['sentences']);
            }

            return $chunk;
        }, $chunks)));
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
        ]);

        $text = $request->input('text');

        if (mb_strlen($text) > self::CHUNK_THRESHOLD) {
            return $this->analyzeWithChunks($text);
        }

        return $this->analyzeSingle($text);
    }

    public function analyzeFile(Request $request)
    {
        $request->validate([
            'file' => 'required|file|max:25600|mimes:txt,pdf,docx',
        ]);

        $file = $request->file('file');
        $extension = strtolower($file->getClientOriginalExtension());

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
            $result = $this->callChunkService($chunks, $cleanText, $fileName);
        } else {
            $result = $this->callSingleService($cleanText, $fileName);
        }

        if ($result instanceof \Illuminate\Http\JsonResponse) {
            $data = $result->getData(true);
            $data['extracted_text'] = $cleanText;
            $data['preprocessing'] = $processed['stats'];
            return response()->json($data);
        }

        return $result;
    }

    /**
     * Simple analysis for short texts.
     */
    private function analyzeSingle(string $text, ?string $fileName = null)
    {
        return $this->callSingleService($text, $fileName);
    }

    /**
     * Chunk-based analysis for long texts.
     */
    private function analyzeWithChunks(string $text, ?string $fileName = null)
    {
        $processed = TextPreprocessor::process($text);
        $chunks = $processed['chunks'];

        if (count($chunks) <= 1) {
            return $this->callSingleService($processed['text'], $fileName);
        }

        return $this->callChunkService($chunks, $processed['text'], $fileName);
    }

    private function callSingleService(string $text, ?string $fileName = null)
    {
        try {
            $response = Http::timeout(120)->post(self::AI_SERVICE_URL . '/predict', [
                'text' => mb_substr($text, 0, 15000),
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
                    'sentences' => $sentences,
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

    private function callChunkService(array $chunks, string $fullText, ?string $fileName = null)
    {
        try {
            // Limit chunks to avoid timeout (max ~20 chunks)
            $chunksToSend = array_slice($chunks, 0, 20);

            $response = Http::timeout(300)->post(self::AI_SERVICE_URL . '/predict-chunks', [
                'chunks' => $chunksToSend,
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
                    'chunks' => $chunkResults,
                    'chunk_count' => count($chunkResults),
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
