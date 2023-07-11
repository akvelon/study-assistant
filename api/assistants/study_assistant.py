from pydantic import BaseSettings, BaseModel
from settings import settings
import time
import openai

openai.api_key = settings.openai_key 

class AssistantMessage(BaseModel):
    id: str
    role: str
    timestamp: int
    content: str
    attachments: list = []

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
    
    def generate_response(self, input: list) -> AssistantMessage:
        # places the system prompt at beginning of list
        messages = [{"role": "system", "content": self.prompt}]
        # appends the rest of the conversation
        for message in input:
            messages.append({"role": message.role, "content": message.content})
     
        # generate response 
        gpt_response = openai.ChatCompletion.create(
            model = self.model,
            messages = messages,  
            max_tokens = self.max_tokens,
            temperature = self.temperature
        )
        # extract response message and id
        response_message = gpt_response["choices"][0]["message"]
        id = gpt_response["id"]
       # create and return new message object
        return AssistantMessage (
            id = id,
            role = response_message["role"],
            timestamp = time.time(),
            content = response_message["content"]
        )

  