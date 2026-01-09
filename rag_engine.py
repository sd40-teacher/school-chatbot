import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

class SchoolChatbot:
    """성동글로벌경영고등학교 AI 챗봇 (최신 LangChain 1.2.3 대응)"""
    
    def __init__(self, api_key, docs_path="data/school_docs"):
        self.api_key = api_key
        self.docs_path = docs_path
        
        # 1. LLM 설정 (OpenRouter)
        self.llm = ChatOpenAI(
            model="google/gemini-2.0-flash-exp:free",
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://sdglobal.sen.hs.kr/",
                "X-Title": "성동글로벌경영고 AI 챗봇"
            },
            temperature=0.7
        )
        
        # 2. 임베딩 설정
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1"
        )
        
        # 3. 문서 로드 및 체인 생성
        self.vectorstore = self._load_documents()
        self.qa_chain = self._create_qa_chain()
    
    def _load_documents(self):
        if not os.path.exists(self.docs_path):
            os.makedirs(self.docs_path)
            
        loader = PyPDFDirectoryLoader(self.docs_path)
        documents = loader.load()
        
        if not documents:
            raise ValueError(f"⚠️ {self.docs_path} 폴더에 PDF 파일이 없습니다!")
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents)
        return FAISS.from_documents(splits, self.embeddings)
    
    def _create_qa_chain(self):
        # 최신 방식의 프롬프트 구성 (system/human 구분)
        system_prompt = (
            "당신은 성동글로벌경영고등학교 도우미입니다. "
            "아래 제공된 문맥(context)만을 사용하여 답변하세요. "
            "모르면 학교(02-2252-1932)로 문의하라고 하세요.\n\n"
            "{context}"
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        
        # 최신 방식의 Retrieval Chain 생성
        question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
        return create_retrieval_chain(self.vectorstore.as_retriever(), question_answer_chain)
    
    def ask(self, question):
        try:
            # 최신 방식의 호출 (input 키 사용)
            response = self.qa_chain.invoke({"input": question})
            return response["answer"]
        except Exception as e:
            return f"오류 발생: {str(e)}"
