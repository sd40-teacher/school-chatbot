import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

class SchoolChatbot:
    """성동글로벌경영고등학교 AI 챗봇 (LangChain 0.3+ 대응 최종본)"""
    
    def __init__(self, api_key, docs_path="data/school_docs"):
        self.api_key = api_key
        self.docs_path = docs_path
        
        # 1. 모델 설정
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
        
        # 3. 데이터 로드 및 벡터 저장소
        self.vectorstore = self._load_documents()
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        
        # 4. 프롬프트 및 체인 설정 (가장 에러 없는 LCEL 방식)
        self.chain = self._create_chain()
    
    def _load_documents(self):
        if not os.path.exists(self.docs_path):
            os.makedirs(self.docs_path)
        loader = PyPDFDirectoryLoader(self.docs_path)
        documents = loader.load()
        if not documents:
            raise ValueError(f"⚠️ {self.docs_path}에 PDF 파일이 없습니다!")
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents)
        return FAISS.from_documents(splits, self.embeddings)
    
    def _create_chain(self):
        # 최신 방식의 프롬프트 구성
        template = """당신은 성동글로벌경영고등학교의 AI 도우미입니다. 
아래의 정보를 바탕으로 친절하게 답변하세요. 모르면 학교(02-2252-1932)로 문의하라고 하세요.

정보:
{context}

질문: {question}

답변:"""
        prompt = ChatPromptTemplate.from_template(template)
        
        # 에러를 유발하는 create_retrieval_chain 대신 LCEL 파이프라인 사용
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
            # invoke 하나로 깔끔하게 실행
            return self.chain.invoke(question)
        except Exception as e:
            return f"오류가 발생했습니다: {str(e)}"
