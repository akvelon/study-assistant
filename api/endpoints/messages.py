from fastapi import APIRouter, Response
from pydantic import BaseModel
from settings import settings
import time
import openai

messages_router = APIRouter(prefix='/messages', tags=[""])

class Message(BaseModel):
    id: str
    role: str
    timestamp: int
    content: str
    attachments: list = []

class MessagesRequest(BaseModel):
    messages: list[Message] = []

class MessagesResponse(BaseModel):
    messages: list[Message] = []
    quickReplies: list[str] = []

class StudyAssistant():
    gpt_model: str 

    def __init__(self):
        openai.api_key = settings.openai_key

        self.gpt_model = "gpt-3.5-turbo"
        
    def generateResponse(self, input: list[Message]) -> Message:
        # create a new list with just the "role" and "content" values
        messages = [{"role": message.role, "content": message.content} for message in input]
        # generate response and extract the message
        gpt_response = openai.ChatCompletion.create(
            model = self.gpt_model,
            messages = messages,  
        )
        response_message = gpt_response["choices"][0]["message"]
        id = gpt_response["id"]
       
        return Message (
            id = id,
            role = response_message["role"],
            timestamp = time.time(),
            content = response_message["content"]
        )
        
assistant = StudyAssistant()

@messages_router.post('/')
async def messages(request: MessagesRequest) -> MessagesResponse:
    messages = request.messages
    # pass messages to study assistant class
    assistant_response = assistant.generateResponse(messages)
    # add the response to the end of the messages list
    messages.append(assistant_response)
    
    return MessagesResponse(messages=messages, quickReplies=[])
