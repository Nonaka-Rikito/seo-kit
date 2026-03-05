"""
Japanese Readability Scorer

Janomeベースの日本語テキスト可読性分析。
英語向けのFlesch-Kincaidスコアの代わりに、日本語固有の指標でスコアリングする。

指標:
- 平均文長（文字数）
- 漢字比率
- ひらがな比率
- カタカナ比率
- 品詞分布（名詞/動詞/形容詞の比率）
- 段落構成
- 専門用語密度
"""

import re
import unicodedata
from typing import Dict, List, Any
from janome.tokenizer import Tokenizer


class ReadabilityScorerJa:
    """日本語コンテンツの可読性を分析する"""

    def __init__(self):
        self.tokenizer = Tokenizer()
        # 日本語Webコンテンツの推奨値
        self.target_avg_sentence_length = (40, 80)  # 文字数
        self.target_kanji_ratio = (0.20, 0.35)  # 20-35%
        self.target_hiragana_ratio = (0.35, 0.55)  # 35-55%
        self.max_paragraph_sentences = 4

    def analyze(self, content: str) -> Dict[str, Any]:
        """日本語テキストの可読性を総合分析する"""
        clean_text = self._clean_content(content)
        if not clean_text:
            return {'error': 'No readable content provided'}

        char_metrics = self._analyze_characters(clean_text)
        sentence_metrics = self._analyze_sentences(clean_text)
        morpheme_metrics = self._analyze_morphemes(clean_text)
        structure_metrics = self._analyze_structure(content)

        overall_score = self._calculate_overall_score(
            char_metrics, sentence_metrics, morpheme_metrics, structure_metrics
        )
        grade = self._get_grade(overall_score)
        recommendations = self._generate_recommendations(
            char_metrics, sentence_metrics, morpheme_metrics, structure_metrics
        )

        return {
            'overall_score': overall_score,
            'grade': grade,
            'character_metrics': char_metrics,
            'sentence_metrics': sentence_metrics,
            'morpheme_metrics': morpheme_metrics,
            'structure_metrics': structure_metrics,
            'recommendations': recommendations,
        }

    def _clean_content(self, content: str) -> str:
        """Markdownヘッダー、リンク、コードブロックを除去"""
        text = re.sub(r'^#+\s+', '', content, flags=re.MULTILINE)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'```[^`]*```', '', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()

    def _analyze_characters(self, text: str) -> Dict[str, Any]:
        """文字種別の比率を分析"""
        total = len(text.replace(' ', '').replace('\n', ''))
        if total == 0:
            return {'error': 'Empty text'}

        kanji = sum(1 for c in text if self._is_kanji(c))
        hiragana = sum(1 for c in text if self._is_hiragana(c))
        katakana = sum(1 for c in text if self._is_katakana(c))
        ascii_chars = sum(1 for c in text if c.isascii() and c.isalpha())

        return {
            'total_chars': total,
            'kanji_count': kanji,
            'kanji_ratio': round(kanji / total, 3),
            'hiragana_count': hiragana,
            'hiragana_ratio': round(hiragana / total, 3),
            'katakana_count': katakana,
            'katakana_ratio': round(katakana / total, 3),
            'ascii_ratio': round(ascii_chars / total, 3),
        }

    def _analyze_sentences(self, text: str) -> Dict[str, Any]:
        """文単位の分析"""
        sentences = re.split(r'[。！？\n]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 2]

        if not sentences:
            return {'total_sentences': 0, 'avg_length': 0}

        lengths = [len(s) for s in sentences]
        return {
            'total_sentences': len(sentences),
            'avg_length': round(sum(lengths) / len(lengths), 1),
            'min_length': min(lengths),
            'max_length': max(lengths),
            'long_sentences': len([l for l in lengths if l > 100]),
            'very_long_sentences': len([l for l in lengths if l > 150]),
        }

    def _analyze_morphemes(self, text: str) -> Dict[str, Any]:
        """形態素解析による品詞分布"""
        tokens = list(self.tokenizer.tokenize(text))
        if not tokens:
            return {'total_tokens': 0}

        pos_counts = {}
        content_words = []
        for token in tokens:
            pos = token.part_of_speech.split(',')[0]
            pos_counts[pos] = pos_counts.get(pos, 0) + 1
            if pos in ('名詞', '動詞', '形容詞', '副詞'):
                content_words.append(token.surface)

        total = len(tokens)
        return {
            'total_tokens': total,
            'noun_ratio': round(pos_counts.get('名詞', 0) / total, 3),
            'verb_ratio': round(pos_counts.get('動詞', 0) / total, 3),
            'adjective_ratio': round(pos_counts.get('形容詞', 0) / total, 3),
            'particle_ratio': round(pos_counts.get('助詞', 0) / total, 3),
            'content_word_count': len(content_words),
            'pos_distribution': {k: v for k, v in sorted(pos_counts.items(), key=lambda x: -x[1])},
        }

    def _analyze_structure(self, content: str) -> Dict[str, Any]:
        """見出し・段落構成の分析"""
        lines = content.split('\n')
        h1_count = sum(1 for l in lines if re.match(r'^#\s+', l))
        h2_count = sum(1 for l in lines if re.match(r'^##\s+', l))
        h3_count = sum(1 for l in lines if re.match(r'^###\s+', l))

        paragraphs = [p for p in content.split('\n\n') if p.strip() and not p.strip().startswith('#')]
        para_lengths = [len(p) for p in paragraphs]

        bullet_lists = len(re.findall(r'^\s*[-*+]\s', content, re.MULTILINE))
        numbered_lists = len(re.findall(r'^\s*\d+\.\s', content, re.MULTILINE))

        return {
            'h1_count': h1_count,
            'h2_count': h2_count,
            'h3_count': h3_count,
            'paragraph_count': len(paragraphs),
            'avg_paragraph_length': round(sum(para_lengths) / len(para_lengths), 1) if para_lengths else 0,
            'has_lists': (bullet_lists + numbered_lists) > 0,
            'list_count': bullet_lists + numbered_lists,
        }

    def _calculate_overall_score(self, char_m, sent_m, morph_m, struct_m) -> float:
        """総合スコアを計算（0-100）"""
        score = 100.0

        # 漢字比率チェック（20点）
        kr = char_m.get('kanji_ratio', 0)
        if kr > 0.40:
            score -= 20  # 漢字が多すぎ（読みにくい）
        elif kr > 0.35:
            score -= 10
        elif kr < 0.15:
            score -= 10  # 漢字が少なすぎ（幼稚な印象）

        # ひらがな比率チェック（15点）
        hr = char_m.get('hiragana_ratio', 0)
        if hr < 0.30:
            score -= 15  # ひらがなが少ない
        elif hr > 0.60:
            score -= 10  # ひらがなが多すぎ

        # 平均文長チェック（20点）
        avg_len = sent_m.get('avg_length', 0)
        if avg_len > 120:
            score -= 20
        elif avg_len > 100:
            score -= 15
        elif avg_len > 80:
            score -= 5
        elif avg_len < 20:
            score -= 10  # 短すぎ

        # 長文ペナルティ（15点）
        very_long = sent_m.get('very_long_sentences', 0)
        if very_long > 0:
            score -= min(15, very_long * 3)

        # 見出し構成（15点）
        if struct_m.get('h2_count', 0) < 3:
            score -= 10
        if not struct_m.get('has_lists', False):
            score -= 5

        # 段落の長さ（15点）
        avg_para = struct_m.get('avg_paragraph_length', 0)
        if avg_para > 300:
            score -= 15
        elif avg_para > 200:
            score -= 10

        return max(0, min(100, score))

    def _get_grade(self, score: float) -> str:
        if score >= 90:
            return "A（優秀）"
        elif score >= 80:
            return "B（良好）"
        elif score >= 70:
            return "C（標準）"
        elif score >= 60:
            return "D（改善必要）"
        else:
            return "F（要大幅改善）"

    def _generate_recommendations(self, char_m, sent_m, morph_m, struct_m) -> List[str]:
        """改善提案を生成"""
        recs = []

        kr = char_m.get('kanji_ratio', 0)
        if kr > 0.35:
            recs.append(f"漢字比率が高めです（{kr:.0%}）。ひらがなへの言い換えを検討してください。")
        elif kr < 0.15:
            recs.append(f"漢字比率が低めです（{kr:.0%}）。適度に漢字を使うと読みやすくなります。")

        avg_len = sent_m.get('avg_length', 0)
        if avg_len > 80:
            recs.append(f"平均文長が長めです（{avg_len:.0f}文字）。40〜80文字を目安に区切りましょう。")

        very_long = sent_m.get('very_long_sentences', 0)
        if very_long > 0:
            recs.append(f"{very_long}文が150文字を超えています。複数の文に分割してください。")

        if struct_m.get('h2_count', 0) < 3:
            recs.append("H2見出しが少ないです。読者がスキャンしやすいよう、見出しを追加してください。")

        if not struct_m.get('has_lists', False):
            recs.append("リスト（箇条書き）がありません。情報を整理するためにリストの活用を検討してください。")

        avg_para = struct_m.get('avg_paragraph_length', 0)
        if avg_para > 200:
            recs.append(f"段落が長めです（平均{avg_para:.0f}文字）。3〜4文で段落を区切りましょう。")

        if not recs:
            recs.append("可読性は優秀です。読みやすいコンテンツになっています。")

        return recs

    @staticmethod
    def _is_kanji(char: str) -> bool:
        try:
            return 'CJK UNIFIED IDEOGRAPH' in unicodedata.name(char, '')
        except ValueError:
            return False

    @staticmethod
    def _is_hiragana(char: str) -> bool:
        return '\u3040' <= char <= '\u309f'

    @staticmethod
    def _is_katakana(char: str) -> bool:
        return '\u30a0' <= char <= '\u30ff'


def score_readability_ja(content: str) -> Dict[str, Any]:
    """日本語コンテンツの可読性をスコアリング"""
    scorer = ReadabilityScorerJa()
    return scorer.analyze(content)
