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

    public function index(Request $request)
    {
        $referenceColumn = $this->referenceColumn();

        $query = $request->user()
            ->detections()
            ->select(array_values(array_unique([
                'id',
                $referenceColumn,
                'user_id',
                'text_excerpt',
                'file_name',
                'ai_probability',
                'created_at',
            ])))
            ->orderByDesc('created_at');

        if ($search = $request->input('search')) {
            $query->where('text_excerpt', 'like', "%{$search}%");
        }

        if ($from = $request->input('from')) {
            $query->whereDate('created_at', '>=', $from);
        }

        if ($to = $request->input('to')) {
            $query->whereDate('created_at', '<=', $to);
        }

        $detections = $query->paginate(20)->withQueryString();
        $detections->getCollection()->transform(function ($detection) {
            $detection->ensureUuid();
            $detection->public_id = Detection::hasUuidColumn() ? $detection->uuid : (string) $detection->id;
            return $detection;
        });

        return Inertia::render('History', [
            'detections' => $detections,
            'filters' => [
                'search' => $search,
                'from' => $from,
                'to' => $to,
            ],
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
