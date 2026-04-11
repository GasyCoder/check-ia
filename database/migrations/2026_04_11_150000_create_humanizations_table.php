<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('humanizations', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->foreignId('detection_id')->nullable()->constrained()->nullOnDelete();
            $table->longText('original_text');
            $table->longText('humanized_text');
            $table->string('intensity', 20)->default('medium');
            $table->float('original_score')->nullable();
            $table->float('humanized_score')->nullable();
            $table->timestamps();

            $table->index('user_id');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('humanizations');
    }
};
