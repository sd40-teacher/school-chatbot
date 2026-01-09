import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate

# 최신 버전에서 RetrievalQA를 쓰기 위한 올바른 경로
from langchain.chains import RetrievalQA

class SchoolChatbot:
    """성동글로벌경영고등학교 AI 챗봇"""
    
    def __init__(self, api_key, docs_path="data/school_docs"):
        self.api_key = api_key
        self.docs_path = docs_path
        
        # OpenRouter LLM 설정
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
        
        self.vectorstore = self._load_documents()
        self.qa_chain = self._create_qa_chain()
    
    def _load_documents(self):
        loader = PyPDFDirectoryLoader(self.docs_path)
        documents = loader.load()
        
        if not documents:
            raise ValueError(f"⚠️ {self.docs_path} 폴더에 PDF 파일이 없습니다!")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        splits = text_splitter.split_documents(documents)
        vectorstore = FAISS.from_documents(splits, self.embeddings)
        return vectorstore
    
    def _create_qa_chain(self):
        prompt_template = """당신은 성동글로벌경영고등학교를 소개하는 친절하고 전문적인 AI 도우미입니다.
아래 제공된 학교 자료를 바탕으로 질문에 정확하게 답변해주세요.

문서 내용:
{context}

질문: {question}

답변:"""

        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # 최신 버전에서도 이 방식으로 호출해야 에러가 나지 않습니다.
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            ),
            return_source_documents=False,
            chain_type_kwargs={"prompt": PROMPT}
        )
        
        return qa_chain
    
    def ask(self, question):
        try:
            # invoke 시 입력 키값을 "query"로 전달합니다.
            response = self.qa_chain.invoke({"query": question})
            return response["result"]
        except Exception as e:
            return f"오류 발생: {str(e)}"
