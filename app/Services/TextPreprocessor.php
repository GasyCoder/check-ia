<?php

namespace App\Services;

class TextPreprocessor
{
    /**
     * Full pipeline: extract → clean → filter → chunk.
     *
     * @return array{text: string, chunks: array<array{label: string, text: string}>, stats: array}
     */
    public static function process(string $raw): array
    {
        $cleaned = self::clean($raw);
        $sections = self::splitSections($cleaned);
        $filtered = self::filterNonContent($sections);
        $chunks = self::chunk($filtered);

        $fullText = implode("\n\n", array_column($chunks, 'text'));

        return [
            'text' => $fullText,
            'chunks' => $chunks,
            'stats' => [
                'original_length' => mb_strlen($raw),
                'cleaned_length' => mb_strlen($fullText),
                'sections_removed' => count($sections) - count($filtered),
                'chunk_count' => count($chunks),
            ],
        ];
    }

    /**
     * Clean raw extracted text: remove image artifacts, fix encoding, normalize whitespace.
     */
    public static function clean(string $text): string
    {
        // Remove null bytes and control characters (except newline, tab)
        $text = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/', '', $text);

        // Remove image placeholders / artifacts from PDF extraction
        $text = preg_replace('/\[?image[:\s]*\d*\]?/i', '', $text);
        $text = preg_replace('/<img[^>]*>/i', '', $text);
        $text = preg_replace('/\(cid:\d+\)/', '', $text);
        $text = preg_replace('/\{\\\\pict[^}]*\}/', '', $text);

        // Remove page numbers (standalone numbers on a line)
        $text = preg_replace('/^\s*-?\s*\d{1,4}\s*-?\s*$/m', '', $text);

        // Remove header/footer repetitions (lines that appear many times)
        $lines = explode("\n", $text);
        $lineCounts = array_count_values(array_map('trim', $lines));
        $repeatedLines = [];
        foreach ($lineCounts as $line => $count) {
            if ($count >= 5 && mb_strlen($line) > 2 && mb_strlen($line) < 100) {
                $repeatedLines[] = $line;
            }
        }
        if ($repeatedLines) {
            $lines = array_filter($lines, fn($l) => !in_array(trim($l), $repeatedLines));
            $text = implode("\n", $lines);
        }

        // Remove excessive special characters lines (table borders, decorative)
        $text = preg_replace('/^[─━═│┃┌┐└┘├┤┬┴┼╔╗╚╝╠╣╦╩╬\-_=|+*#~]{3,}$/m', '', $text);

        // Normalize whitespace: collapse multiple spaces, remove excessive newlines
        $text = preg_replace('/[ \t]+/', ' ', $text);
        $text = preg_replace('/\n{4,}/', "\n\n\n", $text);

        // Fix common encoding issues
        $text = str_replace(
            ['â€™', 'â€"', 'â€"', 'â€˜', 'â€œ', 'â€', 'Ã©', 'Ã¨', 'Ãª', 'Ã ', 'Ã¢', 'Ã®', 'Ã´', 'Ã¹', 'Ã»', 'Ã§'],
            ["'", '–', '—', "'", '"', '"', 'é', 'è', 'ê', 'à', 'â', 'î', 'ô', 'ù', 'û', 'ç'],
            $text
        );

        return trim($text);
    }

    /**
     * Split text into logical sections using headings, double newlines, etc.
     *
     * @return array<array{label: string, text: string}>
     */
    public static function splitSections(string $text): array
    {
        // Try to split by common heading patterns (numbered sections, uppercase lines, etc.)
        $parts = preg_split(
            '/\n{2,}(?=(?:(?:chapitre|partie|section|introduction|conclusion|résumé|abstract|annexe)\s|(?:\d+[\.\)]\s)|(?:[IVXLCDM]+[\.\)]\s)|(?:[A-Z][A-Z\s]{5,}$)))/imu',
            $text
        );

        if (!$parts || count($parts) <= 1) {
            // Fallback: split by double newlines (paragraphs)
            $parts = preg_split('/\n{2,}/', $text);
        }

        $sections = [];
        $sectionIndex = 0;

        foreach ($parts as $part) {
            $part = trim($part);
            if (mb_strlen($part) < 10) continue;

            // Try to extract a label from the first line
            $firstLine = strtok($part, "\n");
            $label = self::extractLabel($firstLine, $sectionIndex);
            $sectionIndex++;

            $sections[] = [
                'label' => $label,
                'text' => $part,
            ];
        }

        return $sections;
    }

    /**
     * Filter out non-content sections (cover page, TOC, bibliography, etc.).
     */
    public static function filterNonContent(array $sections): array
    {
        $nonContentPatterns = [
            // Table of contents
            '/^(table\s+des\s+mati[èe]res|sommaire|table\s+of\s+contents)/iu',
            // Bibliography / References
            '/^(bibliograph|r[ée]f[ée]rences|références\s+bibliographiques|works?\s+cited|sources)/iu',
            // Index
            '/^(index\s+(des\s+)?(figures|tableaux|illustrations|abr[ée]viations))/iu',
            // Appendices that are just lists
            '/^(liste\s+des\s+(figures|tableaux|annexes|abr[ée]viations))/iu',
            // Remerciements (acknowledgments) — usually not AI-detectable content
            '/^(remerciements|acknowledgments?|d[ée]dicace)/iu',
            // Cover page patterns
            '/^(universit[ée]|facult[ée]|[ée]cole|minist[èe]re|r[ée]publique)/iu',
        ];

        $dotLinePattern = '/\.{5,}/'; // TOC-style dot leaders

        return array_values(array_filter($sections, function ($section) use ($nonContentPatterns, $dotLinePattern) {
            $text = $section['text'];
            $firstLine = strtok($text, "\n");

            // Check heading against non-content patterns
            foreach ($nonContentPatterns as $pattern) {
                if (preg_match($pattern, trim($firstLine))) {
                    return false;
                }
            }

            // Detect TOC pages (many dot-leader lines: "Chapter 1 ......... 5")
            $dotLines = preg_match_all($dotLinePattern, $text);
            $totalLines = substr_count($text, "\n") + 1;
            if ($totalLines > 3 && $dotLines / $totalLines > 0.3) {
                return false;
            }

            // Skip sections that are mostly numbers/special chars (tables of data)
            $alphaChars = preg_match_all('/[a-zA-ZÀ-ÿ]/u', $text);
            $totalChars = mb_strlen($text);
            if ($totalChars > 50 && $alphaChars / $totalChars < 0.3) {
                return false;
            }

            return true;
        }));
    }

    /**
     * Chunk sections into analysis-friendly sizes (800-2000 chars each).
     * Merges small sections, splits large ones.
     *
     * @return array<array{label: string, text: string}>
     */
    public static function chunk(array $sections, int $minSize = 500, int $maxSize = 3000): array
    {
        $chunks = [];
        $buffer = '';
        $bufferLabel = '';

        foreach ($sections as $section) {
            $text = $section['text'];
            $label = $section['label'];

            // If section is too large, split it into sub-chunks
            if (mb_strlen($text) > $maxSize) {
                // Flush buffer first
                if ($buffer) {
                    $chunks[] = ['label' => $bufferLabel, 'text' => trim($buffer)];
                    $buffer = '';
                    $bufferLabel = '';
                }

                $subChunks = self::splitByParagraphs($text, $maxSize, $minSize);
                foreach ($subChunks as $i => $sub) {
                    $chunks[] = [
                        'label' => $label . ($i > 0 ? ' (suite ' . ($i + 1) . ')' : ''),
                        'text' => $sub,
                    ];
                }
                continue;
            }

            // If section is small, accumulate into buffer
            if (mb_strlen($text) < $minSize) {
                if ($buffer) {
                    $buffer .= "\n\n" . $text;
                } else {
                    $buffer = $text;
                    $bufferLabel = $label;
                }

                // Flush if buffer is now large enough
                if (mb_strlen($buffer) >= $minSize) {
                    $chunks[] = ['label' => $bufferLabel, 'text' => trim($buffer)];
                    $buffer = '';
                    $bufferLabel = '';
                }
                continue;
            }

            // Flush buffer if any
            if ($buffer) {
                $combined = $buffer . "\n\n" . $text;
                if (mb_strlen($combined) <= $maxSize) {
                    $chunks[] = ['label' => $bufferLabel, 'text' => trim($combined)];
                    $buffer = '';
                    $bufferLabel = '';
                    continue;
                }
                $chunks[] = ['label' => $bufferLabel, 'text' => trim($buffer)];
                $buffer = '';
                $bufferLabel = '';
            }

            $chunks[] = ['label' => $label, 'text' => $text];
        }

        // Flush remaining buffer
        if ($buffer && mb_strlen(trim($buffer)) >= 50) {
            $chunks[] = ['label' => $bufferLabel, 'text' => trim($buffer)];
        }

        return $chunks;
    }

    /**
     * Split a large text block by paragraphs into chunks of ~maxSize.
     */
    private static function splitByParagraphs(string $text, int $maxSize, int $minSize): array
    {
        $paragraphs = preg_split('/\n{2,}/', $text);
        $chunks = [];
        $current = '';

        foreach ($paragraphs as $para) {
            $para = trim($para);
            if (!$para) continue;

            if ($current && mb_strlen($current . "\n\n" . $para) > $maxSize) {
                if (mb_strlen($current) >= $minSize) {
                    $chunks[] = $current;
                    $current = $para;
                } else {
                    $current .= "\n\n" . $para;
                }
            } else {
                $current = $current ? ($current . "\n\n" . $para) : $para;
            }
        }

        if ($current && mb_strlen(trim($current)) >= 50) {
            $chunks[] = $current;
        }

        return $chunks;
    }

    private static function extractLabel(string $firstLine, int $index): string
    {
        $firstLine = trim($firstLine);

        // Check for common heading patterns
        $patterns = [
            '/^(chapitre|partie|section)\s+[\dIVXLCDM]+/iu',
            '/^(introduction|conclusion|résumé|abstract|annexe)/iu',
            '/^\d+[\.\)]\s+(.+)/u',
            '/^[IVXLCDM]+[\.\)]\s+(.+)/u',
        ];

        foreach ($patterns as $pattern) {
            if (preg_match($pattern, $firstLine, $m)) {
                return mb_substr($m[0], 0, 60);
            }
        }

        // If first line is short and looks like a title
        if (mb_strlen($firstLine) < 80 && mb_strlen($firstLine) > 3) {
            return mb_substr($firstLine, 0, 60);
        }

        return 'Section ' . ($index + 1);
    }
}
