import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
# 중요: OpenAIEmbeddings 대신 HuggingFaceEmbeddings 사용
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

class SchoolChatbot:
    """성동글로벌경영고등학교 AI 챗봇의 두뇌"""
    
    def __init__(self, api_key, docs_path="data/school_docs"):
        self.api_key = api_key
        self.docs_path = docs_path
        
        # 1. 모델 설정 (OpenRouter - Llama 무료 모델)
        self.llm = ChatOpenAI(
            model="meta-llama/llama-3.2-3b-instruct:free",
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.7
        )
        
        # 2. 임베딩 설정 (한국어 성능이 검증된 무료 로컬 모델)
        # 이 부분에서 더 이상 OpenAI API를 호출하지 않으므로 에러가 나지 않습니다.
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
        """PDF 문서를 읽어서 AI가 이해할 수 있는 형태로 변환"""
        if not os.path.exists(self.docs_path):
            os.makedirs(self.docs_path)
            
        loader = PyPDFDirectoryLoader(self.docs_path)
        documents = loader.load()
        
        if not documents:
            raise ValueError(f"⚠️ '{self.docs_path}' 폴더에 PDF 파일이 없습니다.")
        
        # 텍스트 나누기 (안정성을 위해 chunk_size 조절)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
        splits = text_splitter.split_documents(documents)
        
        if not splits:
            raise ValueError("PDF에서 텍스트를 추출하지 못했습니다.")
            
        # [핵심] 수정한 임베딩 모델로 저장소 생성
        return FAISS.from_documents(splits, self.embeddings)
    
    def _create_chain(self):
        template = """당신은 성동글로벌경영고등학교를 소개하는 친절한 AI 도우미입니다. 
아래 제공된 정보를 바탕으로 답변하세요. 모르면 학교(02-2252-1932)로 문의하라고 하세요.

정보:
{context}

질문: {question}

답변:"""
        prompt = ChatPromptTemplate.from_template(template)
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        return chain
    
    def ask(self, question):
        try:
            return self.chain.invoke(question)
        except Exception as e:
            return f"오류가 발생했습니다: {str(e)}"
