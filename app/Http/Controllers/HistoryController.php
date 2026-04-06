<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Inertia\Inertia;

class HistoryController extends Controller
{
    public function index(Request $request)
    {
        $query = $request->user()
            ->detections()
            ->select('id', 'user_id', 'text_excerpt', 'file_name', 'ai_probability', 'created_at')
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

        return Inertia::render('History', [
            'detections' => $query->paginate(20)->withQueryString(),
            'filters' => [
                'search' => $search,
                'from' => $from,
                'to' => $to,
            ],
        ]);
    }

    public function sidebar(Request $request)
    {
        $recent = $request->user()
            ->detections()
            ->select('id', 'text_excerpt', 'ai_probability', 'created_at')
            ->orderByDesc('created_at')
            ->limit(20)
            ->get();

        return response()->json($recent);
    }

    public function show(Request $request, int $id)
    {
        $detection = $request->user()->detections()->findOrFail($id);

        return response()->json([
            'full_text' => $detection->full_text,
            'ai_probability' => $detection->ai_probability,
            'chunk_results' => $detection->chunk_results,
            'chunk_count' => $detection->chunk_count,
        ]);
    }

    public function destroy(Request $request, int $id)
    {
        $request->user()->detections()->where('id', $id)->delete();

        return back();
    }
}
