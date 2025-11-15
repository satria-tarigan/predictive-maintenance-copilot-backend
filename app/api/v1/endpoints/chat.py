"""
Modul endpoint untuk API Chatbot (LangChain).
"""

from fastapi import APIRouter, HTTPException
from app.schemas.chat import ChatInputSchema, ChatOutputSchema
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

router = APIRouter()

if not os.getenv("OPENAI_API_KEY"):
    print("PERINGATAN: OPENAI_API_KEY tidak ditemukan di file .env")

@router.post(
    "/",
    response_model=ChatOutputSchema,
    summary="Interaksi dengan Chatbot",
    description="Mengirimkan pertanyaan ke Agent AI (LangChain) dan menerima respons.",
)
async def handle_chat(data: ChatInputSchema) -> ChatOutputSchema:
    """
    Fungsi utama untuk memproses input pengguna dan menghasilkan respons chatbot.
    """
    
    try:
        llm = ChatOpenAI(model="gpt-4o-mini") 

        prompt = ChatPromptTemplate.from_messages([
            ("system", "Anda adalah asisten AI yang membantu memantau kondisi mesin."),
            ("user", "{query}")
        ])

        chain = prompt | llm

        response = await chain.ainvoke({"query": data.query})

        return ChatOutputSchema(response=response.content)

    except Exception as e:
        print(f"Error pada endpoint chat: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Terjadi kesalahan saat berkomunikasi dengan layanan AI."
        )