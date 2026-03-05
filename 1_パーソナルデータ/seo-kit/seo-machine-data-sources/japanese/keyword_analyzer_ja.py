"""
Japanese Keyword Analyzer

Janomeベースの日本語キーワード密度・共起語分析。
英語の単語区切りではなく、形態素解析でキーワードを正確に検出する。
"""

import re
from typing import Dict, List, Optional, Any
from collections import Counter
from janome.tokenizer import Tokenizer


class KeywordAnalyzerJa:
    """日本語コンテンツのキーワード分析"""

    def __init__(self):
        self.tokenizer = Tokenizer()
        self.stop_pos = {'助詞', '助動詞', '記号', '接続詞'}

    def analyze(
        self,
        content: str,
        primary_keyword: str,
        secondary_keywords: Optional[List[str]] = None,
        target_density: float = 1.5,
    ) -> Dict[str, Any]:
        """キーワード密度・配置・共起語を分析"""
        secondary_keywords = secondary_keywords or []
        clean_text = self._clean_content(content)
        tokens = list(self.tokenizer.tokenize(clean_text))
        total_tokens = len([t for t in tokens if t.part_of_speech.split(',')[0] not in self.stop_pos])
        sections = self._extract_sections(content)

        primary_analysis = self._analyze_keyword(
            clean_text, primary_keyword, total_tokens, sections, target_density
        )

        secondary_analysis = []
        for kw in secondary_keywords:
            analysis = self._analyze_keyword(
                clean_text, kw, total_tokens, sections, target_density * 0.5
            )
            secondary_analysis.append({'keyword': kw, **analysis})

        stuffing_risk = self._detect_keyword_stuffing(clean_text, primary_keyword, primary_analysis['density'])
        cooccurrence = self._find_cooccurrence(clean_text, primary_keyword)
        lsi_keywords = self._find_related_terms(clean_text, primary_keyword)

        return {
            'total_content_words': total_tokens,
            'primary_keyword': {'keyword': primary_keyword, **primary_analysis},
            'secondary_keywords': secondary_analysis,
            'keyword_stuffing': stuffing_risk,
            'cooccurrence_terms': cooccurrence,
            'related_terms': lsi_keywords,
            'recommendations': self._generate_recommendations(
                primary_analysis, secondary_analysis, stuffing_risk, target_density, primary_keyword
            ),
        }

    def _clean_content(self, content: str) -> str:
        text = re.sub(r'^#+\s+', '', content, flags=re.MULTILINE)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'```[^`]*```', '', text)
        return text.strip()

    def _extract_sections(self, content: str) -> List[Dict]:
        sections = []
        lines = content.split('\n')
        current = {'type': 'intro', 'header': '', 'content': ''}

        for line in lines:
            h_match = re.match(r'^(#{1,3})\s+(.+)$', line)
            if h_match:
                if current['content'].strip():
                    sections.append(current.copy())
                level = len(h_match.group(1))
                current = {'type': f'h{level}', 'header': h_match.group(2), 'content': ''}
            else:
                current['content'] += line + '\n'

        if current['content'].strip():
            sections.append(current)
        return sections

    def _analyze_keyword(
        self, text: str, keyword: str, total_tokens: int,
        sections: List[Dict], target_density: float
    ) -> Dict[str, Any]:
        """単一キーワードの出現分析"""
        count = text.count(keyword)
        # 密度はキーワード出現数 / 全内容語数 * 100
        density = (count / total_tokens * 100) if total_tokens > 0 else 0

        critical_placements = self._check_critical_placements(text, sections, keyword)
        section_dist = self._section_distribution(sections, keyword)

        return {
            'count': count,
            'density': round(density, 2),
            'target_density': target_density,
            'density_status': self._density_status(density, target_density),
            'critical_placements': critical_placements,
            'section_distribution': section_dist,
        }

    def _check_critical_placements(self, text: str, sections: List[Dict], keyword: str) -> Dict[str, bool]:
        first_200_chars = text[:200]
        in_first_200 = keyword in first_200_chars

        last_para = text.split('\n\n')[-1] if '\n\n' in text else text[-500:]
        in_conclusion = keyword in last_para

        in_h1 = False
        h2_count = 0
        h2_with_kw = 0
        for sec in sections:
            if sec['type'] == 'h1' and keyword in sec['header']:
                in_h1 = True
            if sec['type'] == 'h2':
                h2_count += 1
                if keyword in sec['header']:
                    h2_with_kw += 1

        return {
            'in_first_200_chars': in_first_200,
            'in_conclusion': in_conclusion,
            'in_h1': in_h1,
            'in_h2': f'{h2_with_kw}/{h2_count}',
        }

    def _section_distribution(self, sections: List[Dict], keyword: str) -> List[Dict]:
        dist = []
        for i, sec in enumerate(sections):
            full_text = sec['header'] + ' ' + sec['content']
            count = full_text.count(keyword)
            dist.append({
                'section': i,
                'type': sec['type'],
                'header': sec['header'][:40],
                'keyword_count': count,
            })
        return dist

    def _density_status(self, actual: float, target: float) -> str:
        if actual < target * 0.5:
            return 'too_low'
        elif actual < target * 0.8:
            return 'slightly_low'
        elif actual <= target * 1.3:
            return 'optimal'
        elif actual <= target * 1.8:
            return 'slightly_high'
        else:
            return 'too_high'

    def _detect_keyword_stuffing(self, text: str, keyword: str, density: float) -> Dict[str, Any]:
        risk = 'none'
        warnings = []

        if density > 3.0:
            risk = 'high'
            warnings.append(f'キーワード密度が{density}%で非常に高い（3%超）')
        elif density > 2.5:
            risk = 'medium'
            warnings.append(f'キーワード密度が{density}%でやや高い（2.5%超）')

        paragraphs = text.split('\n\n')
        for i, para in enumerate(paragraphs):
            count = para.count(keyword)
            if count >= 4:
                risk = 'high' if risk != 'high' else risk
                warnings.append(f'段落{i+1}にキーワードが{count}回出現（集中しすぎ）')

        return {'risk_level': risk, 'warnings': warnings, 'safe': risk in ('none', 'low')}

    def _find_cooccurrence(self, text: str, keyword: str, window: int = 50) -> List[Dict]:
        """キーワード周辺の共起語を抽出"""
        positions = [m.start() for m in re.finditer(re.escape(keyword), text)]
        nearby_words = Counter()

        for pos in positions:
            start = max(0, pos - window)
            end = min(len(text), pos + len(keyword) + window)
            context = text[start:end]
            tokens = self.tokenizer.tokenize(context)
            for token in tokens:
                pos_tag = token.part_of_speech.split(',')[0]
                if pos_tag in ('名詞', '動詞', '形容詞') and token.surface != keyword and len(token.surface) > 1:
                    nearby_words[token.surface] += 1

        return [{'term': word, 'count': count} for word, count in nearby_words.most_common(15)]

    def _find_related_terms(self, text: str, keyword: str) -> List[str]:
        """TF的に重要な関連語を抽出"""
        tokens = self.tokenizer.tokenize(text)
        content_words = Counter()
        kw_parts = set(keyword)

        for token in tokens:
            pos_tag = token.part_of_speech.split(',')[0]
            surface = token.surface
            if pos_tag in ('名詞', '動詞', '形容詞') and len(surface) > 1 and surface != keyword:
                if not all(c in kw_parts for c in surface):
                    content_words[surface] += 1

        return [word for word, _ in content_words.most_common(20)]

    def _generate_recommendations(self, primary, secondary, stuffing, target, keyword) -> List[str]:
        recs = []
        status = primary['density_status']
        if status == 'too_low':
            recs.append(f'メインキーワード「{keyword}」の出現が少ないです（{primary["density"]}%）。自然に追加してください。')
        elif status == 'too_high':
            recs.append(f'メインキーワード「{keyword}」の出現が多すぎます（{primary["density"]}%）。同義語に置き換えてください。')

        cp = primary['critical_placements']
        if not cp['in_first_200_chars']:
            recs.append(f'冒頭200文字以内に「{keyword}」を含めてください。')
        if not cp['in_h1']:
            recs.append(f'H1見出しに「{keyword}」を含めてください。')
        if not cp['in_conclusion']:
            recs.append(f'まとめ部分にも「{keyword}」を含めると効果的です。')

        if not stuffing['safe']:
            recs.append(f'キーワード詰め込みリスク: {stuffing["risk_level"]}')

        for sa in secondary:
            if sa['count'] == 0:
                recs.append(f'サブキーワード「{sa["keyword"]}」が未使用です。追加を検討してください。')

        if not recs:
            recs.append('キーワード配置は適切です。')
        return recs


def analyze_keywords_ja(
    content: str,
    primary_keyword: str,
    secondary_keywords: Optional[List[str]] = None,
    target_density: float = 1.5,
) -> Dict[str, Any]:
    """日本語キーワード分析のコンビニエンス関数"""
    analyzer = KeywordAnalyzerJa()
    return analyzer.analyze(content, primary_keyword, secondary_keywords, target_density)
