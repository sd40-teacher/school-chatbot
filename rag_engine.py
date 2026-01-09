import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate

# 최신 버전(1.2.x 이상)에서 RetrievalQA를 불러오는 가장 안전한 방법
try:
    from langchain.chains.retrieval_qa.base import RetrievalQA
except ImportError:
    try:
        from langchain_community.chains import RetrievalQA
    except ImportError:
        from langchain.chains import RetrievalQA

class SchoolChatbot:
    """성동글로벌경영고등학교 AI 챗봇 (LangChain 1.2.3 대응 버전)"""
    
    def __init__(self, api_key, docs_path="data/school_docs"):
        self.api_key = api_key
        self.docs_path = docs_path
        
        # 1. OpenRouter LLM 설정
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
        
        # 2. 임베딩 모델 설정
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1"
        )
        
        # 3. 문서 로드 및 벡터 스토어 생성
        self.vectorstore = self._load_documents()
        
        # 4. QA 체인 생성
        self.qa_chain = self._create_qa_chain()
    
    def _load_documents(self):
        """PDF 로드 및 FAISS 벡터 스토어 생성"""
        if not os.path.exists(self.docs_path):
            os.makedirs(self.docs_path)
            
        loader = PyPDFDirectoryLoader(self.docs_path)
        documents = loader.load()
        
        if not documents:
            raise ValueError(f"⚠️ {self.docs_path} 폴더에 PDF 파일이 없습니다!")
        
        # 텍스트 분할
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)
        
        # 벡터 저장소 생성
        return FAISS.from_documents(splits, self.embeddings)
    
    def _create_qa_chain(self):
        """RetrievalQA 체인 생성"""
        prompt_template = """당신은 성동글로벌경영고등학교를 소개하는 친절한 AI 도우미입니다.
제공된 학교 자료를 바탕으로 질문에 답하세요.

문서 내용:
{context}

질문: {question}

답변:"""

        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # 최신 버전 호환 방식으로 체인 구성
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            ),
            chain_type_kwargs={"prompt": PROMPT}
        )
    
    def ask(self, question):
        """사용자 질문에 답변하는 메서드"""
        try:
            # 최신 invoke 방식 사용
            response = self.qa_chain.invoke({"query": question})
            return response["result"]
        except Exception as e:
            return f"오류 발생: {str(e)}\n학교로 문의하세요 (02-2252-1932)"
