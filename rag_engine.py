from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.prompts import PromptTemplate

class SchoolChatbot:
    """성동글로벌경영고등학교 AI 챗봇"""
    
    def __init__(self, api_key, docs_path="data/school_docs"):
        """
        챗봇 초기화
        
        Args:
            api_key: OpenRouter API 키
            docs_path: PDF 문서가 있는 폴더 경로
        """
        self.api_key = api_key
        self.docs_path = docs_path
        
        # OpenRouter LLM 설정 (무료 Gemini 2.0 Flash 모델)
        self.llm = ChatOpenAI(
            model="google/gemini-2.0-flash-exp:free",
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://sdglobal.sen.hs.kr/",
                "X-Title": "성동글로벌경영고 AI 챗봇"
            },
            temperature=0.7,
            max_tokens=1000
        )
        
        # 임베딩 모델 설정
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1"
        )
        
        # 문서 로드 및 벡터 스토어 생성
        self.vectorstore = self._load_documents()
        
        # QA 체인 생성
        self.qa_chain = self._create_qa_chain()
    
    def _load_documents(self):
        """PDF 문서 로드 및 벡터화"""
        print(f"📂 {self.docs_path}에서 PDF 문서를 로드합니다...")
        
        # PDF 로더
        loader = PyPDFDirectoryLoader(self.docs_path)
        documents = loader.load()
        
        if not documents:
            raise ValueError(
                f"⚠️ {self.docs_path} 폴더에 PDF 파일이 없습니다!\n"
                f"data/school_docs/ 폴더에 학교 소개 PDF를 업로드해주세요."
            )
        
        print(f"✅ {len(documents)}개의 문서 페이지를 로드했습니다.")
        
        # 텍스트 청크 분할
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,        # 각 청크의 크기
            chunk_overlap=200,      # 청크 간 겹치는 부분
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        splits = text_splitter.split_documents(documents)
        
        print(f"✅ 문서를 {len(splits)}개의 청크로 분할했습니다.")
        
        # FAISS 벡터 스토어 생성
        print("🔄 벡터 스토어를 생성하고 있습니다...")
        vectorstore = FAISS.from_documents(splits, self.embeddings)
        
        print("✅ 벡터 스토어 생성 완료!")
        
        return vectorstore
    
    def _create_qa_chain(self):
        """질의응답 체인 생성"""
        # 프롬프트 템플릿
        prompt_template = """당신은 성동글로벌경영고등학교를 소개하는 친절하고 전문적인 AI 도우미입니다.

아래 제공된 학교 자료를 바탕으로 학생, 학부모, 방문자의 질문에 정확하고 친절하게 답변해주세요.

답변 시 다음 규칙을 따라주세요:
1. 친절하고 정중한 말투를 사용하세요
2. 제공된 문서의 정보만을 사용하여 답변하세요
3. 구체적이고 명확하게 설명하세요
4. 문서에 없는 정보는 "제공된 자료에는 해당 정보가 없습니다. 학교에 직접 문의해주시기 바랍니다 (02-2252-1932)"라고 답변하세요
5. 가능하면 예시나 부연 설명을 추가하세요

학교 정보:
- 학교명: 성동글로벌경영고등학교
- 주소: 서울 중구 퇴계로 375 (신당동)
- 전화: 02-2252-1932
- 홈페이지: https://sdglobal.sen.hs.kr/

문서 내용:
{context}

질문: {question}

답변:"""

        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # RetrievalQA 체인 생성
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}  # 상위 3개의 관련 문서 검색
            ),
            return_source_documents=False,
            chain_type_kwargs={"prompt": PROMPT}
        )
        
        return qa_chain
    
    def ask(self, question):
        """
        질문에 답변
        
        Args:
            question: 사용자의 질문
            
        Returns:
            str: AI의 답변
        """
        try:
            response = self.qa_chain.invoke({"query": question})
            return response["result"]
        except Exception as e:
            error_message = (
                f"죄송합니다. 답변 생성 중 오류가 발생했습니다.\n\n"
                f"오류 내용: {str(e)}\n\n"
                f"학교에 직접 문의해주시기 바랍니다.\n"
                f"📞 02-2252-1932"
            )
            return error_message
    
    def refresh_documents(self):
        """
        문서 새로고침 (PDF 업데이트 시 사용)
        
        이 메서드를 호출하면 data/school_docs 폴더의
        PDF를 다시 로드하고 벡터 스토어를 재생성합니다.
        """
        print("🔄 문서를 다시 로드합니다...")
        self.vectorstore = self._load_documents()
        self.qa_chain = self._create_qa_chain()
        print("✅ 문서 새로고침 완료!")
