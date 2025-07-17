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
