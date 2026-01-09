# 🏫 성동글로벌경영고등학교 AI 챗봇

학교 소개 자료 기반 AI 챗봇 시스템입니다.

## 📌 프로젝트 소개

**성글고 AI 도우미**는 학교 소개 PDF 자료를 학습하여 학생, 학부모, 방문자의 질문에 자동으로 답변하는 AI 챗봇입니다.

### 주요 기능
- ✅ 학교 소개 자료 자동 검색 및 답변
- ✅ 자연어 질의응답 (RAG 기반)
- ✅ 무료 OpenRouter API 사용 (Gemini 2.0 Flash)
- ✅ 웹 브라우저에서 바로 사용 가능
- ✅ 학교 홈페이지 임베드 가능

## 🏫 학교 정보

**성동글로벌경영고등학교**
- 📍 주소: [04566] 서울 중구 퇴계로 375 (신당동)
- 📞 전화: 02-2252-1932
- 🌐 홈페이지: https://sdglobal.sen.hs.kr/

## 📁 프로젝트 구조

```
school-chatbot/
├── data/
│   └── school_docs/          # PDF 파일 저장 폴더
│       ├── README.md         # PDF 업로드 안내
│       └── [학교소개.pdf]    # 여기에 PDF 업로드!
│
├── .streamlit/
│   └── secrets.toml          # API 키 설정 (중요!)
│
├── app.py                    # Streamlit 메인 앱
├── rag_engine.py             # RAG 챗봇 엔진
├── requirements.txt          # 필요한 패키지 목록
└── README.md                 # 이 파일
```

## 🚀 빠른 시작 가이드

### 1단계: GitHub 저장소 생성
```
1. GitHub 로그인
2. "New repository" 클릭
3. 이름: school-chatbot
4. Public 선택
5. Create repository
```

### 2단계: 파일 업로드
```
1. 이 폴더의 모든 파일을 ZIP으로 압축
2. GitHub 저장소에서 "uploading an existing file" 클릭
3. 모든 파일 드래그 앤 드롭
4. Commit changes
```

### 3단계: PDF 파일 추가
```
1. data/school_docs/ 폴더로 이동
2. "Upload files" 클릭
3. 학교소개.pdf 등 PDF 파일 업로드
4. Commit changes
```

### 4단계: Streamlit Cloud 배포
```
1. https://streamlit.io/cloud 접속
2. GitHub 계정으로 로그인
3. "New app" 클릭
4. Repository: school-chatbot 선택
5. Main file: app.py
6. Advanced settings → Secrets 설정:
   OPENROUTER_API_KEY = "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"
7. Deploy!
```

### 5단계: 완료!
```
배포 완료 후 URL 복사:
https://school-chatbot-xxxxx.streamlit.app/

이 링크를 학교 홈페이지에 연결하세요!
```

## 🔄 매년 자료 업데이트 방법

### 2026년, 2027년... 매년 업데이트:

```
1. GitHub 저장소 접속
2. data/school_docs/ 폴더로 이동
3. 기존 PDF 파일 클릭 → "Delete file"
4. "Upload files" 클릭
5. 새로운 PDF 파일 업로드
6. Commit changes
7. Streamlit이 자동 재배포 (2-3분)
8. 완료!
```

**소요 시간: 5분**

## 💡 사용 예시

### 질문 예시:
- "학교 교육과정은 어떻게 되나요?"
- "ERP 수업에 대해 알려주세요"
- "입학 전형은 어떻게 진행되나요?"
- "졸업 후 진로는 어떻게 되나요?"
- "학교 위치와 연락처 알려주세요"

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **Backend**: LangChain + FAISS
- **LLM**: Google Gemini 2.0 Flash (via OpenRouter)
- **Embedding**: text-embedding-3-small
- **Hosting**: Streamlit Cloud (무료)

## 📊 비용

- **OpenRouter API**: 무료 (google/gemini-2.0-flash-exp:free)
- **Streamlit Cloud**: 무료
- **GitHub**: 무료
- **총 비용**: **0원** 🎉

## 🔒 보안

### API 키 관리:
- ⚠️ `.streamlit/secrets.toml` 파일은 GitHub에 업로드하지 마세요!
- ✅ Streamlit Cloud의 Secrets에서 설정하세요
- ✅ API 키는 절대 공개하지 마세요

### secrets.toml 파일이 실수로 올라갔다면:
```
1. OpenRouter에서 즉시 API 키 삭제
2. 새 API 키 발급
3. Streamlit Cloud Secrets 업데이트
```

## 🐛 문제 해결

### "API 키 오류" 발생 시:
```
→ Streamlit Cloud → App settings → Secrets 확인
→ OPENROUTER_API_KEY가 정확한지 확인
```

### "PDF 로드 실패" 발생 시:
```
→ data/school_docs/ 폴더에 PDF 파일이 있는지 확인
→ PDF 파일이 손상되지 않았는지 확인
→ 파일명에 특수문자가 없는지 확인
```

### "답변이 이상해요" 발생 시:
```
→ PDF 내용이 명확한지 확인
→ 질문을 더 구체적으로 수정
→ PDF 자료를 더 상세하게 작성
```

## 📞 문의

**성동글로벌경영고등학교**
- 전화: 02-2252-1932
- 홈페이지: https://sdglobal.sen.hs.kr/

## 📄 라이선스

이 프로젝트는 성동글로벌경영고등학교의 교육 목적으로 제작되었습니다.

---

**제작일**: 2025년 1월
**제작**: 성동글로벌경영고등학교
**기술 지원**: Claude AI + OpenRouter + Streamlit
