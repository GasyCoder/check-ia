<?php

namespace App\Http\Controllers;

use App\Models\Detection;
use Illuminate\Http\Request;
use Inertia\Inertia;

class HistoryController extends Controller
{
    private function referenceColumn(): string
    {
        return Detection::hasUuidColumn() ? 'uuid' : 'id';
    }

    private function currentFilters(Request $request): array
    {
        return [
            'search' => trim((string) $request->input('search', '')) ?: null,
            'from' => $request->input('from') ?: null,
            'to' => $request->input('to') ?: null,
        ];
    }

    private function filteredQuery(Request $request, array $columns): array
    {
        $referenceColumn = $this->referenceColumn();
        $filters = $this->currentFilters($request);

        $query = $request->user()
            ->detections()
            ->select(array_values(array_unique(array_merge([
                'id',
                $referenceColumn,
            ], $columns))))
            ->orderByDesc('created_at');

        $this->applyFilters($query, $filters);

        return [$query, $filters];
    }

    private function applyFilters($query, array $filters): void
    {
        if ($filters['search']) {
            $query->where('text_excerpt', 'like', "%{$filters['search']}%");
        }

        if ($filters['from']) {
            $query->whereDate('created_at', '>=', $filters['from']);
        }

        if ($filters['to']) {
            $query->whereDate('created_at', '<=', $filters['to']);
        }
    }

    private function exportRow(Detection $detection): array
    {
        $detection->ensureUuid();

        return [
            'id' => Detection::hasUuidColumn() ? $detection->uuid : (string) $detection->id,
            'date' => $detection->created_at?->toIso8601String(),
            'score_ia' => round((float) $detection->ai_probability, 1),
            'fichier' => $detection->file_name,
            'extrait' => $detection->text_excerpt,
            'texte' => $detection->full_text,
            'chunks' => (int) ($detection->chunk_count ?? 0),
        ];
    }

    public function index(Request $request)
    {
        [$query, $filters] = $this->filteredQuery($request, [
            'user_id',
            'text_excerpt',
            'file_name',
            'ai_probability',
            'created_at',
        ]);

        $detections = $query->paginate(20)->withQueryString();
        $detections->getCollection()->transform(function ($detection) {
            $detection->ensureUuid();
            $detection->public_id = Detection::hasUuidColumn() ? $detection->uuid : (string) $detection->id;
            return $detection;
        });

        return Inertia::render('History', [
            'detections' => $detections,
            'filters' => $filters,
        ]);
    }

    public function sidebar(Request $request)
    {
        $referenceColumn = $this->referenceColumn();

        $recent = $request->user()
            ->detections()
            ->select(array_values(array_unique([
                'id',
                $referenceColumn,
                'text_excerpt',
                'ai_probability',
                'created_at',
            ])))
            ->orderByDesc('created_at')
            ->limit(20)
            ->get();

        $recent->each(function ($detection) {
            $detection->ensureUuid();
            $detection->public_id = Detection::hasUuidColumn() ? $detection->uuid : (string) $detection->id;
        });

        return response()->json($recent);
    }

    public function export(Request $request, string $format)
    {
        abort_unless(in_array($format, ['json', 'csv', 'txt'], true), 404);

        [$query, $filters] = $this->filteredQuery($request, [
            'user_id',
            'text_excerpt',
            'full_text',
            'file_name',
            'ai_probability',
            'chunk_count',
            'created_at',
        ]);

        $rows = $query->get()->map(fn (Detection $detection) => $this->exportRow($detection))->values();
        $fileName = 'historique-' . now()->format('Y-m-d-His') . '.' . $format;

        if ($format === 'json') {
            return response()->streamDownload(function () use ($rows, $filters) {
                echo json_encode([
                    'exported_at' => now()->toIso8601String(),
                    'filters' => $filters,
                    'count' => $rows->count(),
                    'items' => $rows->all(),
                ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
            }, $fileName, [
                'Content-Type' => 'application/json; charset=UTF-8',
            ]);
        }

        if ($format === 'csv') {
            return response()->streamDownload(function () use ($rows) {
                $handle = fopen('php://output', 'w');
                fwrite($handle, "\xEF\xBB\xBF");
                fputcsv($handle, ['ID', 'Date', 'Score IA', 'Fichier', 'Extrait', 'Texte', 'Chunks']);

                foreach ($rows as $row) {
                    fputcsv($handle, [
                        $row['id'],
                        $row['date'],
                        $row['score_ia'],
                        $row['fichier'],
                        $row['extrait'],
                        $row['texte'],
                        $row['chunks'],
                    ]);
                }

                fclose($handle);
            }, $fileName, [
                'Content-Type' => 'text/csv; charset=UTF-8',
            ]);
        }

        return response()->streamDownload(function () use ($rows, $filters) {
            echo "Export historique ReinIA\n";
            echo 'Date export: ' . now()->toDateTimeString() . "\n";
            echo 'Filtres: ' . json_encode($filters, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n";
            echo 'Nombre: ' . $rows->count() . "\n\n";

            foreach ($rows as $index => $row) {
                echo 'Analyse #' . ($index + 1) . "\n";
                echo 'ID: ' . $row['id'] . "\n";
                echo 'Date: ' . $row['date'] . "\n";
                echo 'Score IA: ' . $row['score_ia'] . "%\n";
                echo 'Fichier: ' . ($row['fichier'] ?: '-') . "\n";
                echo 'Chunks: ' . $row['chunks'] . "\n";
                echo 'Extrait: ' . ($row['extrait'] ?: '-') . "\n";
                echo "Texte:\n" . ($row['texte'] ?: '-') . "\n";
                echo "\n----------------------------------------\n\n";
            }
        }, $fileName, [
            'Content-Type' => 'text/plain; charset=UTF-8',
        ]);
    }

    public function show(Request $request, string $ref)
    {
        $detection = $request->user()->detections()->where($this->referenceColumn(), $ref)->firstOrFail();

        return response()->json([
            'full_text' => $detection->full_text,
            'ai_probability' => $detection->ai_probability,
            'chunk_results' => $detection->chunk_results,
            'chunk_count' => $detection->chunk_count,
        ]);
    }

    public function destroy(Request $request, string $ref)
    {
        $request->user()->detections()->where($this->referenceColumn(), $ref)->delete();

        return back();
    }
}
