<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

#[Fillable(['user_id', 'text_excerpt', 'full_text', 'file_name', 'ai_probability', 'chunk_results', 'chunk_count'])]
class Detection extends Model
{
    protected function casts(): array
    {
        return [
            'chunk_results' => 'array',
        ];
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
}
