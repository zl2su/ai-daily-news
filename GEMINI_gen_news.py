# AI 뉴스 생성기 #
import requests
import feedparser
import json
import os
import time 

class AINewsWebGenerator:
    def __init__(self):
        self.claude_api_key = os.getenv('CLAUDE_API_KEY')
        
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
        
        for source in self.news_sources:
            try:
                feed = feedparser.parse(source)
                for entry in feed.entries[:5]:  # 각 소스에서 최신 5개씩
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
                
        return all_articles[:5]  # 최대 5개 기사
        
    def get_gemini_summary(self, articles):
        """Google Gemini API로 뉴스 요약"""
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        print(f"📊 Gemini API 키 확인: {'설정됨' if gemini_api_key else '설정 안됨'}")
    
        if not gemini_api_key:
            print("❌ GEMINI_API_KEY가 설정되지 않았습니다!")
            return None
            
        articles_text = ""
        for i, article in enumerate(articles, 1):
            articles_text += f"{i}. {article['title']}\n"
            if article['summary']:
                articles_text += f"   {article['summary'][:100]}...\n"
            articles_text += f"   출처: {article['source']}\n\n"
        
        prompt = f"""
다음 AI 뉴스들을 분석해서 한국어로 요약해주세요:

{articles_text}

다음 형식으로 JSON 응답해주세요:
{{
  "today_summary": "오늘의 AI 뉴스 한줄 요약",
  "key_trends": ["주요 트렌드1", "주요 트렌드2", "주요 트렌드3"],
  "market_insight": "AI 시장 동향 분석 (2-3문장)"
}}

JSON 형식으로만 응답해주세요.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={gemini_api_key}"
    
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
                print(f"📝 API 응답 내용 미리보기: {content[:200]}...")
                
                try:
                    parsed_data = json.loads(content)
                    print("✅ JSON 파싱 성공!")
                    return parsed_data
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
            # 수정된 코드 (문제 해결)
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
            <p>🔄 매일 오전 10시 자동 업데이트 | Made with Claude AI</p>
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
        
        # 2. GEMINI 요약
        print("🤖 GEMINI AI 분석 중...")
        summary_data = self.get_gemini_summary(articles)
        
        if not summary_data:
            summary_data = {
                "today_summary": "오늘의 AI 뉴스를 분석하고 있습니다.",
                "key_trends": ["인공지능", "머신러닝", "딥러닝"],
                "market_insight": "AI 기술이 빠르게 발전하고 있습니다.",
                "tech_highlights": ["새로운 AI 모델", "기술 혁신"]
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

