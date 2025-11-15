"""
Modul skema untuk API Chatbot.
"""

from pydantic import BaseModel, Field

class ChatInputSchema(BaseModel):
    """ Data masukan (input) untuk chatbot. """
    query: str = Field(..., description="Teks pertanyaan dari pengguna.")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Apa itu predictive maintenance?"
            }
        }

class ChatOutputSchema(BaseModel):
    """ Data keluaran (output) dari respons chatbot. """
    response: str = Field(..., description="Teks jawaban dari chatbot.")