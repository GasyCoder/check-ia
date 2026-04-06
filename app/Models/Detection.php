<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Str;

#[Fillable(['uuid', 'user_id', 'text_excerpt', 'full_text', 'file_name', 'ai_probability', 'chunk_results', 'chunk_count'])]
class Detection extends Model
{
    protected static ?bool $hasUuidColumn = null;

    protected static function booted(): void
    {
        static::creating(function (Detection $detection) {
            if (static::hasUuidColumn() && !$detection->uuid) {
                $detection->uuid = (string) Str::uuid();
            }
        });
    }

    protected function casts(): array
    {
        return [
            'chunk_results' => 'array',
        ];
    }

    public function ensureUuid(): void
    {
        if (!static::hasUuidColumn() || $this->uuid) {
            return;
        }

        $this->forceFill([
            'uuid' => (string) Str::uuid(),
        ])->saveQuietly();
    }

    public static function hasUuidColumn(): bool
    {
        if (static::$hasUuidColumn === null) {
            static::$hasUuidColumn = Schema::hasColumn('detections', 'uuid');
        }

        return static::$hasUuidColumn;
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
}
