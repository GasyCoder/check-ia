<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

#[Fillable(['user_id', 'detection_id', 'original_text', 'humanized_text', 'intensity', 'original_score', 'humanized_score'])]
class Humanization extends Model
{
    protected function casts(): array
    {
        return [
            'original_score' => 'float',
            'humanized_score' => 'float',
        ];
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function detection(): BelongsTo
    {
        return $this->belongsTo(Detection::class);
    }
}
