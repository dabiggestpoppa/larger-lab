"""Full RCE pipeline test — both topics, save to desktop."""
import asyncio
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from core.research.cognition import MultiSourceFetcher
from core.research.cognition.llm_reasoning import LLMReasoning

TOPICS = [
    'transfer entropy financial markets systemic risk contagion',
    'geopolitical risk emerging markets capital flows financial crisis',
]

PAPERS_PER_SOURCE = 5
YEAR_FROM = 2016

async def main():
    fetcher = MultiSourceFetcher()
    llm = LLMReasoning()
    
    for topic in TOPICS:
        print(f'\n=== {topic} ===')
        papers = await fetcher.fetch_papers(topic, per_source=PAPERS_PER_SOURCE, year_from=YEAR_FROM)
        print(f'Papers: {len(papers)}')
        
        paper_dicts = []
        for p in papers:
            text = p.abstract or p.title
            if p.concepts:
                concept_text = ', '.join(c.name for c in p.concepts[:5])
                text = f'{text}. Key concepts: {concept_text}'
            paper_dicts.append({'text': text, 'title': p.title, 'id': p.id, 'source': p.source})
        
        results = await llm.run_full_pipeline(topic, paper_dicts)
        
        report = results['r4'].get('research_report', {})
        title = report.get('title', 'Research Report')
        full_report = report.get('full_report', '')
        word_count = report.get('word_count', 0)
        confidence = results['r4'].get('confidence', 0)
        
        print(f'Title: {title}')
        print(f'Words: {word_count}, Confidence: {confidence:.3f}')
        
        safe_name = topic.replace(' ', '_').replace('/', '_')[:40]
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        md_path = os.path.join(desktop, f'RCE_{safe_name}.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f'# {title}\n\n')
            f.write(f'**Topic:** {topic}\n')
            f.write(f'**Papers analyzed:** {len(papers)}\n')
            f.write(f'**Sources:** OpenAlex + arXiv + S2\n')
            f.write(f'**Word count:** {word_count}\n')
            f.write(f'**Confidence:** {confidence:.3f}\n\n')
            f.write(full_report)
        print(f'Saved: {md_path}')

asyncio.run(main())
