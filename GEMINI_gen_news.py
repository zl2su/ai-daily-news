# AI 뉴스 생성기 - Gemini 버전 #
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
            'https://www.theverge.com/ai-artificial-intelligence/rss/index.xml'
        ]
    
    def collect_news(self):
        """최신 AI 뉴스 수집"""
        all_articles = []

        # 더 많은 AI 뉴스 소스 추가
        extended_sources = [
            'https://feeds.feedburner.com/venturebeat/SZYF',
            'https://techcrunch.com/category/artificial-intelligence/feed/',
            'https://www.artificialintelligence-news.com/feed/',
            'https://www.theverge.com/ai-artificial-intelligence/rss/index.xml',
            'https://rss.cnn.com/rss/edition.rss',  # CNN 전체 (AI 뉴스 포함)
            'https://feeds.reuters.com/reuters/technologyNews',  # 로이터 기술
            'https://www.wired.com/feed/category/gear/artificial-intelligence/latest/rss',  # Wired AI
            'https://techxplore.com/rss-feed/technology-news/',  # TechXplore
            'https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml',  # Science Daily AI
            'https://news.mit.edu/rss/topic/artificial-intelligence2'  # MIT AI 뉴스
        ]
            
        for source in self.news_sources:
            try:
                print(f"📡 {source}에서 뉴스 수집 중...")
                feed = feedparser.parse(source)
                
                # 각 소스에서 최신 10개씩
                for entry in feed.entries[:10]:  
                    article = {
                        'title': entry.title,
                        'summary': entry.summary if hasattr(entry, 'summary') else entry.description if hasattr(entry, 'description') else '',
                        'link': entry.link,
                        'published': entry.published if hasattr(entry, 'published') else '',
                        'source': feed.feed.title if hasattr(feed.feed, 'title') else source
                    }
                    all_articles.append(article)
            except Exception as e:
                print(f"Error fetching from {source}: {e}")
                
        # 날짜순으로 정렬(최신순)
        def get_date_for_sorting(article):
            try:
                if article.get('published'):
                    from dateutil import parser
                    return parser.parse(article['published'])
            except:
                pass
            return None
        
        # 날짜가 있는 기사들을 최신순으로 정렬
        articles_with_date = [a for a in all_articles if get_date_for_sorting(a)]
        articles_with_date.sort(key=get_date_for_sorting, reverse=True)
        
        # 날짜가 없는 기사들 추가
        articles_without_date = [a for a in all_articles if not get_date_for_sorting(a)]
        
        final_articles = articles_with_date + articles_without_date
        
        print(f"📊 총 {len(final_articles)}개의 AI 뉴스를 수집했습니다")
        return all_articles[:20]  # 최대 20개 기사
    
    def get_gemini_summary(self, articles):
        """Google Gemini API로 뉴스 요약"""
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
다음 AI 뉴스들을 분석하여 JSON으로만 응답하세요. 다른 설명이나 텍스트는 포함하지 마세요.

뉴스 목록:
{articles_text}

응답 형식 (JSON만):
{{
  "today_summary": "한줄 요약",
  "key_trends": ["트렌드1", "트렌드2", "트렌드3"],
  "market_insight": "시장 분석"
}}

위 JSON 형식으로만 응답하세요. 다른 텍스트는 절대 포함하지 마세요.
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
                            return {
                                "today_summary": "JSON 파싱 실패로 인한 기본값",
                                "key_trends": ["파싱", "실패"],
                                "market_insight": "API 응답을 JSON으로 파싱할 수 없습니다."
                            }
                            
                    except Exception as e:
                        print(f"❌ JSON 파싱 실패: {e}")
                        print(f"🔍 원본 응답: {content}")
                        return {
                            "today_summary": "AI 뉴스 요약 처리 중 오류 발생",
                            "key_trends": ["데이터 처리 중"],
                            "market_insight": "시장 분석 준비 중입니다."
                        }
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
    
    def generate_html(self, articles, summary_data):
        """HTML 웹페이지 생성"""
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
            
            <div class="summary-card">
                <h3>🔥 주요 트렌드</h3>
                <div class="trends-list">
                    {''.join([f'<span class="trend-tag">{trend}</span>' for trend in summary_data.get('key_trends', ['분석 중'])])}
                </div>
            </div>
            
            <div class="summary-card">
                <h3>💡 시장 인사이트</h3>
                <p>{summary_data.get('market_insight', '시장 분석 준비 중입니다.')}</p>
            </div>
        </div>
        
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
        
        # 2. Gemini 요약
        print("🤖 Gemini AI 분석 중...")
        summary_data = self.get_gemini_summary(articles)
        
        if not summary_data:
            summary_data = {
                "today_summary": "오늘의 AI 뉴스를 분석하고 있습니다.",
                "key_trends": ["인공지능", "머신러닝", "딥러닝"],
                "market_insight": "AI 기술이 빠르게 발전하고 있습니다."
            }
        
        # 3. HTML 생성
        print("🎨 웹페이지 생성 중...")
        html_content = self.generate_html(articles, summary_data)
        
        # 4. 파일 저장
        self.save_to_file(html_content)
        
        print("✅ 웹페이지 생성 완료!")
        print("📱 브라우저에서 index.html 파일을 열어보세요!")

if __name__ == "__main__":
    generator = AINewsWebGenerator()
    generator.run()
