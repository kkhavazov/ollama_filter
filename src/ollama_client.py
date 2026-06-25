from pydantic import BaseModel, Field
from typing import Optional
from ollama import Client
from config import ollama_address, MODEL

class CustomerRequest(BaseModel):
    is_customer_request: bool = Field(description="True if this is an external customer inquiry, request, or issue. False if it is internal spam, newsletters, or automated business updates.")
    customer_name: Optional[str] = Field(None, description="The name of the customer if identifiable.")
    urgency: str = Field(description="Urgency level: High, Medium, Low")
    summary: Optional[str] = Field(None, description="A brief 1-sentence summary of what the customer wants.")

def filter_email_with_llm(email_data):
    prompt = f"Subject: {email_data['subject']}\nBody: {email_data['body']}"
    
    client = Client(host = ollama_address)
    response = client.chat(
        model=MODEL,  
        messages=[
            {"role": "system", "content": "You are an AI assistant sorting internal corporate mail. Identify if the incoming email is a customer request."},
            {"role": "user", "content": prompt}
        ],
        format=CustomerRequest.model_json_schema(),
        options={"temperature": 0} 
    )
    
    return CustomerRequest.model_validate_json(response.message.content)