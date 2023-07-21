from pydantic import BaseSettings
import openai
from settings import settings
import time
from api.endpoints.search import search_documents, SearchQuery
from api.endpoints.schemas import (
    MessageAttachment,
    Message,
    MessagesRequest,
    MessagesResponse,
)
from api.assistants.history.manager import HistoryManager
from api.endpoints.user import User

history_manager = HistoryManager()

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
    async def generate_response(
        self, request: MessagesRequest, user: User | None
    ) -> MessagesResponse:
        # Places the system prompt at beginning of list
        messages = [{"role": "system", "content": self.prompt}]
        # Appends the rest of the conversation
        for message in request.messages:
            messages.append({"role": message.role, "content": message.content})

        # Generate response
        gpt_response = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        # Convert to Message schema
        response_message = Message(
            id=gpt_response["id"],
            role=gpt_response["choices"][0]["message"]["role"],
            timestamp=time.time(),
            content=gpt_response["choices"][0]["message"]["content"],
        )

        # search similar documents with user message content
        search_engine = search_documents(SearchQuery(messages=[response_message]))
        found_documents = await search_engine
        attachment = None
        if len(found_documents.documents) > 0:
            document = found_documents.documents[0]
            image_src = (
                document.document.image_metadata[0]["src"]
                if document.document.image_metadata
                else None
            )
            attachment = MessageAttachment(
                id=document.document.id,
                title=document.document.title,
                summary=document.document.summary,
                url=document.document.url,
                image=image_src,
            )
        # Update ChatGPT attachmentens
        if attachment:
            response_message.attachments = [attachment]

        return history_manager.process_messages(request, response_message, user)


class UsersMessageMissingException(Exception):
    pass
