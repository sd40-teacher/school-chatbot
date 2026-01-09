import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
# HuggingFace 임베딩 추가
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

class SchoolChatbot:
    def __init__(self, api_key, docs_path="data/school_docs"):
        self.api_key = api_key
        self.docs_path = docs_path
        
        # 1. 모델 설정 (OpenRouter Gemini) - 기존 유지
        self.llm = ChatOpenAI(
            model="google/gemini-2.0-flash-exp:free",
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.7
        )
        
        # 2. 임베딩 설정 (한국어 특화 모델로 교체)
        # 별도의 API 키가 필요 없으며 성능이 안정적입니다.
        self.embeddings = HuggingFaceEmbeddings(
            model_name="jhgan/ko-sroberta-multitask",
            model_kwargs={'device': 'cpu'}
        )
        
        # 3. 데이터 로드 및 벡터 저장소 생성
        self.vectorstore = self._load_documents()
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        
        # 4. 답변 체인 생성
        self.chain = self._create_chain()

    def _load_documents(self):
        if not os.path.exists(self.docs_path):
            os.makedirs(self.docs_path)
            
        loader = PyPDFDirectoryLoader(self.docs_path)
        documents = loader.load()
        
        if not documents:
            raise ValueError(f"⚠️ '{self.docs_path}'에 읽을 수 있는 PDF가 없습니다.")
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents)
        
        # FAISS 인덱스 생성 시 교체된 임베딩 모델 사용
        return FAISS.from_documents(splits, self.embeddings)

    # ... 이하 _create_chain 및 ask 메서드는 기존과 동일 ...
