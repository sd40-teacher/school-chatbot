import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

class SchoolChatbot:
    """성동글로벌경영고등학교 AI 챗봇의 두뇌"""
    
    def __init__(self, api_key, docs_path="data/school_docs"):
        self.api_key = api_key
        self.docs_path = docs_path
        
        # 1. 모델 설정 (OpenRouter Gemini)
        self.llm = ChatOpenAI(
            model="google/gemini-2.0-flash-exp:free",
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.7
        )
        
        # 2. 임베딩 설정
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1"
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
        
        # [디버깅] 파일을 몇 페이지나 읽었는지 확인
        print(f"📄 로드된 총 페이지 수: {len(documents)}")
        
        if not documents:
            raise ValueError(
                f"⚠️ '{self.docs_path}' 폴더에 PDF 파일이 없거나 읽을 수 없습니다. "
                "파일명을 영문(예: school_info.pdf)으로 바꿔서 다시 시도해보세요."
            )
        
        # 텍스트 나누기
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents)
        
        print(f"✂️ 분할된 데이터 조각(Chunk) 수: {len(splits)}")
        
        return FAISS.from_documents(splits, self.embeddings)
    
    def _create_chain(self):
        """질문을 받았을 때 답을 생성하는 흐름 설계"""
        template = """당신은 성동글로벌경영고등학교를 소개하는 친절한 AI 도우미입니다. 
아래 제공된 정보를 바탕으로 답변하세요. 모르면 학교(02-2252-1932)로 문의하라고 하세요.

정보:
{context}

질문: {question}

답변:"""
        prompt = ChatPromptTemplate.from_template(template)
        
        # 가공 함수
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        # LCEL 파이프라인 구성
        chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        return chain
    
    def ask(self, question):
        """사용자가 질문하면 답변을 반환"""
        try:
            return self.chain.invoke(question)
        except Exception as e:
            return f"오류가 발생했습니다: {str(e)}"
