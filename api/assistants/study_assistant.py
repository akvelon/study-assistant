"""Study assistant"""
import time
from pydantic import BaseSettings
import openai
from settings import settings
from api.endpoints.search import search_engine
from api.endpoints.user import User
from api.endpoints.schemas import (
    MessageAttachment,
    Message,
    MessagesRequest,
    MessagesResponse,
)
from api.assistants.history.manager import HistoryManager

history_manager = HistoryManager()

openai.api_key = settings.openai_key


def parse_prompt(file: str) -> str:
    """Loads prompts for Chat"""
    with open(file, "r", encoding="utf-8") as promptfile:
        prompt = promptfile.read()
    return prompt


class StudyAssistantSettings(BaseSettings):
    """read file and return as string"""

    prompt = parse_prompt("api/assistants/study_assistant.txt")

    model: str = "gpt-3.5-turbo"
    greeting: str = ""

    temperature: float = 0.8
    max_tokens: int = 400

    prompt: str = prompt

    name: str = "Study Assistant"
    description: str = ""
    category: str = "language"


class StudyAssistant(StudyAssistantSettings):
    """Study assistant class"""

    async def generate_response(
        self,
        request: MessagesRequest,
        user: User,
        school_id: int,
    ) -> MessagesResponse:
        """Generates response for answer"""
        # Places the system prompt at beginning of list
        messages = [{"role": "system", "content": self.prompt}]
        # Appends the rest of the conversation
        for message in request.messages:
            messages.append({"role": message.role, "content": message.content})
        documents = await search_engine.search_text_vectors(request, school_id)
        document = documents[0] if len(documents) else None
        if document:
            messages.append(search_engine.get_system_message(document))

        # Generate response
        gpt_response = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        attachments = []

        # Attach document to user message content
        if document:
            image_src = (
                document.document.image_metadata[0]["src"]
                if document.document.image_metadata
                else None
            )
            attachments.append(
                MessageAttachment(
                    id=document.document.id,
                    title=document.document.title,
                    summary=document.document.summary,
                    url=document.document.url,
                    image=image_src,
                )
            )

        # Convert to Message schema
        response_message = Message(
            id=gpt_response["id"],
            role=gpt_response["choices"][0]["message"]["role"],
            timestamp=time.time(),
            content=gpt_response["choices"][0]["message"]["content"],
            attachments=attachments,
        )

        return history_manager.process_messages(request, response_message, user)


class UsersMessageMissingException(Exception):
    """Missing exception class"""
