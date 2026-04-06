<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('detections', function (Blueprint $table) {
            $table->json('chunk_results')->nullable()->after('ai_probability');
            $table->unsignedInteger('chunk_count')->default(0)->after('chunk_results');
        });
    }

    public function down(): void
    {
        Schema::table('detections', function (Blueprint $table) {
            $table->dropColumn(['chunk_results', 'chunk_count']);
        });
    }
};
