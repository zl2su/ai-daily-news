# AI 뉴스 생성기 - 임원용 보고서 확장 버전 #
import requests
import feedparser
import json
import os
import time 

class AINewsWebGenerator:
    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        # AI 뉴스 RSS 피드들
        self.news_sources = [
            'https://feeds.feedburner.com/venturebeat/SZYF',
            'https://techcrunch.com/category/artificial-intelligence/feed/',
            'https://www.artificialintelligence-news.com/feed/',
            'https://www.theverge.com/ai-artificial-intelligence/rss/index.xml',
            'https://rss.cnn.com/rss/edition.rss',
            'https://feeds.reuters.com/reuters/technologyNews',
            'https://www.wired.com/feed/category/gear/artificial-intelligence/latest/rss',
            'https://techxplore.com/rss-feed/technology-news/',
            'https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml'
        ]
    
    def collect_news(self):
        """최신 뉴스 수집 (24시간 우선, 부족하면 48시간)"""
        from datetime import datetime, timedelta
        
        all_articles = []
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)
        
        print(f"🕐 우선 {yesterday.strftime('%Y-%m-%d %H:%M')} 이후 뉴스를 수집합니다")
        
        recent_articles = []
        older_articles = []
        no_date_articles = []
        
        for source in self.news_sources:
            try:
                print(f"📡 {source}에서 뉴스 수집 중...")
                feed = feedparser.parse(source)
                
                for entry in feed.entries[:20]:
                    article_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            article_date = datetime(*entry.published_parsed[:6])
                        except:
                            pass
                    elif hasattr(entry, 'published') and entry.published:
                        try:
                            from dateutil import parser
                            article_date = parser.parse(entry.published)
                            if article_date.tzinfo:
                                article_date = article_date.replace(tzinfo=None)
                        except:
                            pass
                    
                    article = {
                        'title': entry.title,
                        'summary': entry.summary if hasattr(entry, 'summary') else entry.description if hasattr(entry, 'description') else '',
                        'link': entry.link,
                        'published': entry.published if hasattr(entry, 'published') else '',
                        'source': feed.feed.title if hasattr(feed.feed, 'title') else source,
                        'date_obj': article_date
                    }
                    
                    if article_date:
                        if article_date >= yesterday:
                            recent_articles.append(article)
                            print(f"✅ 최신 뉴스 (24h): {article['title'][:50]}...")
                        elif article_date >= two_days_ago:
                            older_articles.append(article)
                            print(f"🔄 이전 뉴스 (48h): {article['title'][:50]}...")
                    else:
                        no_date_articles.append(article)
                        print(f"📅 날짜 미상: {article['title'][:50]}...")
                            
            except Exception as e:
                print(f"❌ Error fetching from {source}: {e}")
        
        recent_articles.sort(key=lambda x: x['date_obj'], reverse=True)
        older_articles.sort(key=lambda x: x['date_obj'], reverse=True)
        
        if len(recent_articles) >= 10:
            final_articles = recent_articles[:15]
            print(f"📊 24시간 이내 뉴스 충분: {len(final_articles)}개 사용")
        else:
            needed_count = 15 - len(recent_articles)
            final_articles = recent_articles + older_articles[:needed_count]
            print(f"📊 24시간 뉴스 부족 → 48시간 이내 뉴스 추가: 총 {len(final_articles)}개")
            
            if len(final_articles) < 10:
                still_needed = 10 - len(final_articles)
                final_articles.extend(no_date_articles[:still_needed])
                print(f"📊 여전히 부족 → 날짜 미상 뉴스 추가: 총 {len(final_articles)}개")
        
        seen_titles = set()
        unique_articles = []
        for article in final_articles:
            title_key = article['title'].lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_articles.append(article)
        
        print(f"🎯 최종 선택: {len(unique_articles)}개 뉴스")
        
        return unique_articles[:15]
    
    def analyze_keywords_optimal(self, articles):
        """최적화된 키워드 추출 (빈도 3회 + 특별 키워드)"""
        from collections import Counter
        import re
        
        # 모든 뉴스 텍스트 합치기
        all_text = ""
        for article in articles:
            title = article.get('title', '').lower()
            summary = article.get('summary', '').lower()
            all_text += f" {title} {summary}"
        
        # 기술/응용 분야 중심 핵심 키워드
        core_keywords = [
            'autonomous', 'medical', 'healthcare', 'education', 
            'coding', 'robotics', 'vision', 'voice', 'multimodal'
        ]
        
        # 자동 단어 추출
        # 대문자로 시작하는 단어들 (회사명, 제품명)
        capitalized_words = re.findall(r'\b[A-Z][a-z]{2,15}\b', all_text.title())
        
        # 일반 단어들 (3글자 이상)
        regular_words = re.findall(r'\b[a-z]{3,15}\b', all_text)
        
        # 진짜 기본적인 불용어만 (문제 단어들 대폭 추가)
        stop_words = {
            'the', 'and', 'for', 'are', 'with', 'this', 'that', 'from',
            'will', 'can', 'said', 'more', 'about', 'than', 'also', 'have',
            'when', 'where', 'what', 'how', 'why', 'who', 'which',
            'been', 'they', 'their', 'would', 'could', 'should', 'much',
            # 웹 관련 + 분리된 단어들 + 문제 단어들 (모두 소문자)
            'href', 'https', 'www', 'http', 'html', 'com', 'you',
            'chat', 'gpt', 'machine', 'learning', 'deep', 'artificial',
            'new', 'search', 'agent', 'news', 'research', 'its', 'openai'
        }
        
        # 특별 키워드 (새로운 AI 도구/회사들)
        special_keywords = {
            'sora', 'devin', 'claude', 'gemini', 'midjourney', 'cursor', 
            'perplexity', 'runway', 'stability', 'cohere', 'replicate',
            'huggingface', 'github', 'copilot', 'tesla', 'waymo'
        }
        
        auto_keywords = []
        
        # 대문자 단어들 (회사명, 제품명 가능성 높음) - 불용어 필터링 추가
        for word in set(capitalized_words):
            if word.lower() not in stop_words and len(word) >= 3:
                auto_keywords.append(word)
        
        # 일반 단어들 중 빈도 높은 것들 - 불용어 필터링 강화
        word_freq = Counter([word for word in regular_words 
                            if word not in stop_words and len(word) >= 3])
        
        # 빈도 5회 이상으로 올림 (특별 키워드는 3회도 허용)
        for word, freq in word_freq.items():
            if freq >= 5 or (freq >= 3 and word.lower() in special_keywords):
                auto_keywords.append(word.title())
        
        # 전체 키워드 통합
        all_keywords = core_keywords + auto_keywords
        
        # 복합 키워드 우선 처리 (띄어쓰기 문제 해결)
        compound_keywords = {
            'chatgpt': ['chat gpt', 'chatgpt'],
            'machine learning': ['machine learning'],
            'deep learning': ['deep learning'], 
            'artificial intelligence': ['artificial intelligence'],
            'claude ai': ['claude ai', 'claude 3', 'claude 3.5'],
            'gemini pro': ['gemini pro', 'gemini advanced'],
            'github copilot': ['github copilot'],
            'openai gpt': ['openai gpt', 'gpt-4', 'gpt-5']
        }
        
        keyword_counts = Counter()
        
        # 1. 복합 키워드 먼저 계산
        for display_name, patterns in compound_keywords.items():
            total_count = 0
            for pattern in patterns:
                total_count += all_text.count(pattern.lower())
            if total_count > 0:
                keyword_counts[display_name.title()] = total_count
                # 복합 키워드 부분들을 텍스트에서 제거 (중복 방지)
                for pattern in patterns:
                    all_text = all_text.replace(pattern.lower(), '')
        
        # 2. 일반 키워드 계산 (복합 키워드 제거 후)
        for keyword in all_keywords:
            count = all_text.count(keyword.lower())
            if count > 0:
                # 표시명 정리
                if keyword.lower() in ['ai', 'gpt', 'llm', 'api', 'ceo', 'cto']:
                    display_name = keyword.upper()
                elif keyword.lower() in special_keywords:
                    display_name = keyword.title()
                else:
                    display_name = keyword.title()
                
                keyword_counts[display_name] = count
        
        # 상위 10개 반환
        top_keywords = dict(keyword_counts.most_common(10))
        
        print(f"🔍 최적화된 키워드 분석: {len(top_keywords)}개 발견")
        print(f"  📋 핵심 키워드: {len([k for k in core_keywords if k in all_text])}개")
        print(f"  🔍 자동 발견: {len(top_keywords) - len([k for k in core_keywords if k in all_text])}개")
        
        # 상위 5개 키워드 미리보기
        for i, (keyword, count) in enumerate(list(top_keywords.items())[:5]):
            print(f"    {i+1}. {keyword}: {count}회")
        
        return top_keywords
    
    def load_yesterday_keywords(self):
        """어제 키워드 데이터 불러오기"""
        try:
            with open('yesterday_keywords.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"📋 어제 키워드 불러옴: {len(data)}개")
                return data
        except FileNotFoundError:
            print("📋 어제 키워드 파일 없음 (첫 실행)")
            return {}
        except Exception as e:
            print(f"❌ 어제 키워드 불러오기 실패: {e}")
            return {}
    
    def save_today_keywords(self, keyword_data):
        """오늘 키워드 데이터 저장"""
        try:
            with open('yesterday_keywords.json', 'w', encoding='utf-8') as f:
                json.dump(keyword_data, f, ensure_ascii=False, indent=2)
                print(f"💾 오늘 키워드 저장 완료: {len(keyword_data)}개")
        except Exception as e:
            print(f"❌ 키워드 저장 실패: {e}")
    
    def analyze_keyword_trends(self, today_keywords, yesterday_keywords):
        """키워드 트렌드 분석 (NEW, HOT, RISING)"""
        trends = {}
        
        # 첫 실행인 경우 (어제 키워드 없음)
        if not yesterday_keywords:
            print("📋 첫 실행입니다. 모든 키워드를 기본으로 표시합니다.")
            for keyword, count in today_keywords.items():
                trends[keyword] = {
                    'count': count,
                    'tag': '',  # 첫 실행에는 태그 없음
                    'change': '0'
                }
            return trends
        
        for keyword, today_count in today_keywords.items():
            yesterday_count = yesterday_keywords.get(keyword, 0)
            
            if yesterday_count == 0:
                # 어제 없던 키워드
                trends[keyword] = {
                    'count': today_count,
                    'tag': '🆕 NEW',
                    'change': f'+{today_count}'
                }
            elif today_count >= yesterday_count * 2:
                # 빈도가 2배 이상 증가
                trends[keyword] = {
                    'count': today_count,
                    'tag': '🔥 HOT',
                    'change': f'+{today_count - yesterday_count}'
                }
            elif today_count > yesterday_count:
                # 점진적 상승
                trends[keyword] = {
                    'count': today_count,
                    'tag': '📈 RISING',
                    'change': f'+{today_count - yesterday_count}'
                }
            else:
                # 변화 없거나 하락
                trends[keyword] = {
                    'count': today_count,
                    'tag': '',
                    'change': f'{today_count - yesterday_count}' if today_count != yesterday_count else '0'
                }
        
        print(f"📊 트렌드 분석 완료:")
        new_count = len([k for k, v in trends.items() if v['tag'] == '🆕 NEW'])
        hot_count = len([k for k, v in trends.items() if v['tag'] == '🔥 HOT'])
        rising_count = len([k for k, v in trends.items() if v['tag'] == '📈 RISING'])
        
        print(f"  🆕 NEW: {new_count}개")
        print(f"  🔥 HOT: {hot_count}개")
        print(f"  📈 RISING: {rising_count}개")
        
        return trends
    
    def generate_keyword_chart_html(self, keyword_trends):
        """키워드 빈도 차트 HTML 생성 (트렌드 태그 포함)"""
        if not keyword_trends:
            return """
            <div class="keyword-chart">
                <h3>📊 키워드 트렌드</h3>
                <p>분석할 키워드가 충분하지 않습니다.</p>
            </div>
            """
        
        max_count = max([data['count'] for data in keyword_trends.values()]) if keyword_trends else 1
        
        chart_html = """
        <div class="keyword-chart">
            <h3>📊 오늘의 AI 키워드 트렌드</h3>
            <div class="chart-container">
        """
        
        # 키워드를 빈도순으로 정렬
        sorted_keywords = sorted(keyword_trends.items(), key=lambda x: x[1]['count'], reverse=True)
        
        # 각 키워드별 바 차트
        for keyword, data in sorted_keywords:
            count = data['count']
            tag = data['tag']
            change = data['change']
            percentage = (count / max_count) * 100
            
            chart_html += f"""
            <div class="keyword-bar">
                <div class="keyword-label">
                    {keyword}
                    {f'<span class="trend-tag">{tag}</span>' if tag else ''}
                </div>
                <div class="bar-container">
                    <div class="bar" style="width: {percentage}%"></div>
                    <span class="count">{count}</span>
                    {f'<span class="change">({change})</span>' if change != '0' else ''}
                </div>
            </div>
            """
        
        chart_html += """
            </div>
        </div>
        """
        
        return chart_html
    
    def get_gemini_summary(self, articles):
        """Google Gemini API로 뉴스 요약 (일반용 + 임원용)"""
        print(f"📊 Gemini API 키 확인: {'설정됨' if self.gemini_api_key else '설정 안됨'}")
    
        if not self.gemini_api_key:
            print("❌ GEMINI_API_KEY가 설정되지 않았습니다!")
            return None
            
        articles_text = ""
        for i, article in enumerate(articles, 1):
            articles_text += f"{i}. {article['title']}\n"
            if article['summary']:
                articles_text += f"   {article['summary'][:100]}...\n"
            articles_text += f"   출처: {article['source']}\n\n"
        
        prompt = f"""
다음 AI 뉴스들을 분석하여 JSON으로만 응답하세요. 모든 내용은 제공된 뉴스에서만 추출하고, 일반적이거나 추상적인 내용은 포함하지 마세요.

뉴스 목록:
{articles_text}

응답 규칙:
1. 실제 뉴스에서 언급된 구체적인 내용만 사용
2. 기업명, 제품명, 수치, 구체적 사건만 포함
3. 일반론이나 뻔한 내용 금지
4. 각 항목에 해당 뉴스 출처 표시

응답 형식 (JSON만):
{{
  "today_summary": "오늘 뉴스의 핵심 내용 (2-3문장, 구체적 사실 기반)",
  "key_trends": ["뉴스에서 실제 언급된 트렌드만 3개"],
  "business_impact": {{
    "opportunities": [
      "실제 뉴스에서 언급된 구체적 비즈니스 기회 (기업명/제품명 포함)",
      "수치나 구체적 사례가 있는 기회만"
    ],
    "risks": [
      "뉴스에서 실제 보도된 위험 사건이나 이슈만",
      "구체적 기업이나 사건 기반 위험요소만"
    ],
    "competitive_moves": [
      "뉴스에서 언급된 실제 기업의 구체적 행동",
      "기업명과 구체적 행동 내용 포함"
    ]
  }},
  "focus_areas": [
    "뉴스에서 실제 언급된 주목할 만한 기술이나 영역",
    "구체적 기술 이름이나 시장 영역"
  ],
  "technology_watch": [
    "뉴스에서 실제 언급된 기술명만",
    "구체적 기술 이름이나 제품명"
  ]
}}

중요: 뉴스에 없는 내용은 절대 추가하지 마세요. 구체적 사실만 포함하세요.
        """
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={self.gemini_api_key}"
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        try:
            print("🔄 Gemini API 호출 시작...")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            print(f"📡 API 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ API 호출 성공!")
                result = response.json()
                
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    print(f"📝 API 응답 내용 전체: {content}")
                    
                    try:
                        # JSON 부분만 추출 시도
                        start = content.find('{')
                        end = content.rfind('}') + 1
                        
                        if start != -1 and end > start:
                            json_part = content[start:end]
                            print(f"🔍 추출된 JSON: {json_part}")
                            parsed_data = json.loads(json_part)
                            print("✅ JSON 파싱 성공!")
                            return parsed_data
                        else:
                            print("❌ JSON 형식을 찾을 수 없습니다")
                            return self.get_default_summary_data()
                            
                    except Exception as e:
                        print(f"❌ JSON 파싱 실패: {e}")
                        print(f"🔍 원본 응답: {content}")
                        return self.get_default_summary_data()
                else:
                    print("❌ API 응답에 content가 없습니다")
                    print(f"🔍 전체 응답: {result}")
                    return None
            else:
                print(f"❌ API 호출 실패: {response.status_code}")
                print(f"🔍 응답 내용: {response.text}")
                return None

        except Exception as e:
            print(f"❌ Gemini API 오류: {e}")
            return None
    
    def get_default_summary_data(self):
        """기본 요약 데이터 (API 실패시 사용)"""
        return {
            "today_summary": "AI 뉴스 분석을 위해 데이터를 처리 중입니다.",
            "key_trends": ["분석 진행 중"],
            "business_impact": {
                "opportunities": ["데이터 분석 완료 후 업데이트 예정"],
                "risks": ["분석 진행 중"],
                "competitive_moves": ["기업 동향 분석 중"]
            },
            "focus_areas": ["분석 중"],
            "technology_watch": ["분석 중"]
        }
    
    def generate_executive_section_html(self, summary_data):
        """임원용 섹션 HTML 생성"""
        business_impact = summary_data.get('business_impact', {})
        opportunities = business_impact.get('opportunities', [])
        risks = business_impact.get('risks', [])
        competitive_moves = business_impact.get('competitive_moves', [])
        focus_areas = summary_data.get('focus_areas', [])
        technology_watch = summary_data.get('technology_watch', [])
        
        executive_html = f"""
        <div class="executive-section">
            <div class="executive-header">
                <h2>📊 보고</h2>
            </div>
            
            <div class="impact-grid">
                <div class="impact-card opportunities">
                    <h3>🚀 비즈니스 기회</h3>
                    <ul>
                        {''.join([f'<li>{opp}</li>' for opp in opportunities])}
                    </ul>
                </div>
                
                <div class="impact-card risks">
                    <h3>⚠️ 위험 요소</h3>
                    <ul>
                        {''.join([f'<li>{risk}</li>' for risk in risks])}
                    </ul>
                </div>
                
                <div class="impact-card competitive">
                    <h3>🏢 경쟁사 동향</h3>
                    <ul>
                        {''.join([f'<li>{move}</li>' for move in competitive_moves])}
                    </ul>
                </div>
            </div>
            
            <div class="focus-areas">
                <div class="focus-card">
                    <h3>📈 주목 영역</h3>
                    <div class="focus-tags">
                        {''.join([f'<span class="focus-tag investment">{focus}</span>' for focus in focus_areas])}
                    </div>
                </div>
                
                <div class="focus-card">
                    <h3>🔬 기술 모니터링</h3>
                    <div class="focus-tags">
                        {''.join([f'<span class="focus-tag technology">{tech}</span>' for tech in technology_watch])}
                    </div>
                </div>
            </div>
        </div>
        """
        
        return executive_html
    
    def generate_executive_styles(self):
        """임원용 섹션 CSS 스타일"""
        return """
        .executive-section {
            background: #f8f9fa;
            padding: 30px;
            margin-bottom: 20px;
            border-left: 5px solid #dc3545;
        }
        
        .executive-header h2 {
            color: #dc3545;
            font-size: 1.8rem;
            margin-bottom: 20px;
            font-weight: 700;
        }
        
        .executive-summary-card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 25px;
            border-left: 4px solid #dc3545;
            box-shadow: 0 5px 15px rgba(220, 53, 69, 0.1);
        }
        
        .executive-summary-card h3 {
            color: #dc3545;
            margin-bottom: 15px;
            font-size: 1.2rem;
        }
        
        .executive-summary-text {
            font-size: 1.1rem;
            line-height: 1.6;
            color: #2c3e50;
            font-weight: 500;
        }
        
        .impact-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .impact-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }
        
        .impact-card.opportunities {
            border-left: 4px solid #28a745;
        }
        
        .impact-card.risks {
            border-left: 4px solid #ffc107;
        }
        
        .impact-card.competitive {
            border-left: 4px solid #6f42c1;
        }
        
        .impact-card h3 {
            margin-bottom: 15px;
            font-size: 1.1rem;
        }
        
        .opportunities h3 {
            color: #28a745;
        }
        
        .risks h3 {
            color: #ffc107;
        }
        
        .competitive h3 {
            color: #6f42c1;
        }
        
        .impact-card ul {
            list-style: none;
            padding: 0;
        }
        
        .impact-card li {
            padding: 8px 0;
            border-bottom: 1px solid #f1f3f4;
            color: #495057;
            font-size: 0.95rem;
        }
        
        .impact-card li:last-child {
            border-bottom: none;
        }
        
        .recommendations-section {
            margin-bottom: 30px;
        }
        
        .recommendations-section h3 {
            color: #dc3545;
            margin-bottom: 20px;
            font-size: 1.3rem;
        }
        
        .recommendations-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }
        
        .recommendation-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.08);
            position: relative;
        }
        
        .recommendation-card.high {
            border-left: 4px solid #dc3545;
        }
        
        .recommendation-card.medium {
            border-left: 4px solid #ffc107;
        }
        
        .recommendation-card.low {
            border-left: 4px solid #6c757d;
        }
        
        .rec-priority {
            position: absolute;
            top: 10px;
            right: 15px;
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .recommendation-card.high .rec-priority {
            background: #dc3545;
            color: white;
        }
        
        .recommendation-card.medium .rec-priority {
            background: #ffc107;
            color: black;
        }
        
        .recommendation-card.low .rec-priority {
            background: #6c757d;
            color: white;
        }
        
        .rec-action {
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 10px;
            padding-right: 60px;
            font-size: 1rem;
        }
        
        .rec-timeline {
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        .focus-areas {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }
        
        .focus-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }
        
        .focus-card h3 {
            color: #dc3545;
            margin-bottom: 15px;
            font-size: 1.1rem;
        }
        
        .focus-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .focus-tag {
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        .focus-tag.investment {
            background: #e8f5e8;
            color: #2e7d32;
            border: 1px solid #4caf50;
        }
        
        .focus-tag.technology {
            background: #e3f2fd;
            color: #1976d2;
            border: 1px solid #2196f3;
        }
        
        @media (max-width: 768px) {
            .executive-section {
                padding: 20px;
            }
            
            .impact-grid {
                grid-template-columns: 1fr;
            }
            
            .recommendations-grid {
                grid-template-columns: 1fr;
            }
            
            .focus-areas {
                grid-template-columns: 1fr;
            }
        }
        """
    
    def generate_html(self, articles, summary_data, keyword_trends=None):
        """HTML 웹페이지 생성 (임원용 섹션 포함)"""
        current_time = time.strftime('%Y년 %m월 %d일 %H시 %M분')
        
        html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 뉴스 데일리 | {time.strftime('%Y-%m-%d')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header p {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        
        .update-time {{
            background: #f8f9fa;
            padding: 15px;
            text-align: center;
            border-bottom: 1px solid #e9ecef;
            font-size: 0.9rem;
            color: #6c757d;
        }}
        
        .summary-section {{
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .summary-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }}
        
        .summary-card h3 {{
            color: #4facfe;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }}
        
        .trends-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 10px;
        }}
        
        .trend-tag {{
            background: #e3f2fd;
            color: #1976d2;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
        }}
        
        .keyword-chart {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }}
        
        .keyword-chart h3 {{
            color: #4facfe;
            margin-bottom: 20px;
            font-size: 1.3rem;
        }}
        
        .chart-container {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        
        .keyword-bar {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .keyword-label {{
            min-width: 180px;
            font-weight: 500;
            color: #2c3e50;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .trend-tag {{
            font-size: 0.7rem;
            padding: 2px 6px;
            border-radius: 8px;
            background: #f0f8ff;
            border: 1px solid #4facfe;
            color: #4facfe;
            font-weight: 600;
        }}
        
        .bar-container {{
            flex: 1;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .bar {{
            height: 25px;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            border-radius: 12px;
            min-width: 20px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .bar:hover {{
            transform: scaleY(1.1);
            box-shadow: 0 3px 10px rgba(79, 172, 254, 0.3);
        }}
        
        .bar::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shine 2s infinite;
        }}
        
        @keyframes shine {{
            0% {{ left: -100%; }}
            100% {{ left: 100%; }}
        }}
        
        .count {{
            font-weight: 600;
            color: #4facfe;
            min-width: 30px;
            text-align: center;
            font-size: 0.9rem;
        }}
        
        .change {{
            font-size: 0.8rem;
            color: #666;
            min-width: 40px;
            text-align: right;
        }}
        
        {self.generate_executive_styles()}
        
        .news-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            padding: 30px;
        }}
        
        .news-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            border: 1px solid #e9ecef;
            transition: all 0.3s ease;
            position: relative;
        }}
        
        .news-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }}
        
        .news-card h3 {{
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.2rem;
            line-height: 1.4;
        }}
        
        .news-card p {{
            color: #7f8c8d;
            margin-bottom: 15px;
            font-size: 0.95rem;
        }}
        
        .news-meta {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .news-source {{
            background: #e8f5e8;
            color: #2e7d32;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        
        .news-date {{
            color: #95a5a6;
            font-size: 0.8rem;
        }}
        
        .read-more {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s ease;
            display: inline-block;
        }}
        
        .read-more:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(79, 172, 254, 0.4);
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        
        .refresh-btn {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #4facfe;
            color: white;
            border: none;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            font-size: 1.5rem;
            cursor: pointer;
            box-shadow: 0 5px 15px rgba(79, 172, 254, 0.4);
            transition: all 0.3s ease;
        }}
        
        .refresh-btn:hover {{
            transform: scale(1.1);
        }}
        
        @media (max-width: 768px) {{
            .news-grid {{
                grid-template-columns: 1fr;
                padding: 20px;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
            
            .summary-section {{
                padding: 20px;
            }}
            
            .keyword-label {{
                min-width: 140px;
                font-size: 0.8rem;
            }}
            
            .bar {{
                height: 20px;
            }}
            
            .trend-tag {{
                font-size: 0.6rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI 뉴스 데일리</h1>
            <p>오늘의 인공지능 뉴스를 한눈에</p>
        </div>
        
        <div class="update-time">
            마지막 업데이트: {current_time}
        </div>
        
        <div class="summary-section">
            <div class="summary-card">
                <h3>📈 오늘의 한줄 요약</h3>
                <p>{summary_data.get('today_summary', '요약 준비 중입니다.')}</p>
            </div>
            
            {self.generate_keyword_chart_html(keyword_trends) if keyword_trends else ''}
            
            <div class="summary-card">
                <h3>🔥 주요 트렌드</h3>
                <div class="trends-list">
                    {''.join([f'<span class="trend-tag">{trend}</span>' for trend in summary_data.get('key_trends', ['분석 중'])])}
                </div>
            </div>
        </div>
        
        {self.generate_executive_section_html(summary_data)}
        
        <div class="news-grid">
        """
        
        # 뉴스 카드들 추가
        for article in articles:
            # 발행일 포맷팅
            published_date = ""
            if article.get('published'):
                published_date = article['published'][:16]  # 앞의 16글자만 사용
            html_content += f"""
            <div class="news-card">
                <div class="news-meta">
                    <span class="news-source">{article.get('source', 'AI News')}</span>
                    <span class="news-date">{published_date}</span>
                </div>
                <h3>{article['title']}</h3>
                <p>{article['summary'][:200]}...</p>
                <a href="{article['link']}" target="_blank" class="read-more">자세히 읽기</a>
            </div>
            """
        
        html_content += """
        </div>
        
        <div class="footer">
            <p>🔄 매일 오전 10시 자동 업데이트 | Made with Gemini AI</p>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="location.reload()">🔄</button>
    
    <script>
        // 자동 새로고침 (30분마다)
        setTimeout(function() {
            location.reload();
        }, 30 * 60 * 1000);
    </script>
</body>
</html>
        """
        
        return html_content
    
    def save_to_file(self, html_content):
        """HTML 파일로 저장"""
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("index.html 파일 생성 완료!")
    
    def run(self):
        """메인 실행 함수"""
        print("🚀 AI 뉴스 웹페이지 생성 시작...")
        
        # 1. 뉴스 수집
        print("📰 뉴스 수집 중...")
        articles = self.collect_news()
        
        if not articles:
            print("❌ 수집된 뉴스가 없습니다.")
            return
        
        print(f"✅ {len(articles)}개 뉴스 수집 완료")
        
        # 2. 최적화된 키워드 빈도 분석
        print("🔍 키워드 트렌드 분석 중...")
        today_keywords = self.analyze_keywords_optimal(articles)
        
        # 3. 어제 키워드 불러오고 트렌드 분석
        yesterday_keywords = self.load_yesterday_keywords()
        keyword_trends = self.analyze_keyword_trends(today_keywords, yesterday_keywords)
        
        # 4. 오늘 키워드 저장 (내일을 위해)
        self.save_today_keywords(today_keywords)
        
        # 5. Gemini 요약 (일반용 + 임원용)
        print("🤖 Gemini AI 분석 중...")
        summary_data = self.get_gemini_summary(articles)
        
        if not summary_data:
            summary_data = self.get_default_summary_data()
        
        # 6. HTML 생성 (임원용 섹션 포함)
        print("🎨 웹페이지 생성 중...")
        html_content = self.generate_html(articles, summary_data, keyword_trends)
        
        # 7. 파일 저장
        self.save_to_file(html_content)
        
        print("✅ 웹페이지 생성 완료!")
        print("📱 브라우저에서 index.html 파일을 열어보세요!")

if __name__ == "__main__":
    generator = AINewsWebGenerator()
    generator.run()
