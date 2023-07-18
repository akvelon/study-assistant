from pydantic import BaseSettings
import openai
from settings import settings
import time
from api.endpoints.search import search_documents
from api.endpoints.schemas import MessageAttachment, Message

openai.api_key = settings.openai_key 


class StudyAssistantSettings(BaseSettings):
    # read file and return as string
    def parse_prompt(file: str) -> str:
        with open(file, "r") as f:
            prompt = f.read()
        return prompt

    model: str = "gpt-3.5-turbo"
    greeting: str = ""

    temperature: float = 0.0
    max_tokens: int = 500
    
    prompt: str = parse_prompt("api/assistants/study_assistant.txt")

    name: str = "Study Assistant"
    description: str = ""
    category: str = "language"


class StudyAssistant(StudyAssistantSettings):
    
    async def generate_response(self, input: list) -> Message:
        # places the system prompt at beginning of list
        messages = [{"role": "system", "content": self.prompt}]
        # appends the rest of the conversation
        for message in input:
            messages.append({"role": message.role, "content": message.content})
     
        # generate response 
        gpt_response = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        # extract response message and id
        response_message = gpt_response["choices"][0]["message"]
        id = gpt_response["id"]

        # search similar documents with user message content
        search_engine = search_documents(input)
        found_documents = await search_engine
        document = found_documents.documents[0]
        attachment = MessageAttachment(id=document.document.id, title=document.document.title,
                                       summary=document.document.summary, url=document.document.url,
                                       image=document.document.image_metadata[0]["src"])

        #create and return new message object
        return Message(
            id=id,
            role=response_message["role"],
            timestamp=time.time(),
            content=response_message["content"],
            attachments=[attachment]
            )
