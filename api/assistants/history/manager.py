"""Creates an interface all assistant can access to interact with the database
for chat history."""

import openai

from settings import settings
from api.db.history import history_db, InvalidChatIdException
from api.endpoints.schemas import Chat, Message, MessagesResponse, History


class HistoryManager:
    """Manages conversations for assistants."""

    def __init__(self):
        pass

    def process_messages(self, request, response_message, user) -> MessagesResponse:
        """Extract information from request and response, and store in database."""

        request.messages.append(response_message)

        # Only update history for authenticated users
        if user:
            # Check if chat id is present
            if request.chat and request.chat.id:
                return self.update_history(request.chat.id, user.id, request.messages)

            # Otherwise fallback to OpenAI id and user id
            openai_id = None

            # Create new history if first message
            if len(request.messages) == 1:
                openai_id = response_message.id
            else:
                # Continue history from existing messages
                # and get history id from first ChatGPT response
                openai_id = request.messages[1].id

            return self.update_history_by_ids(openai_id, user.id, request.messages)

        # Otherwise guest user, just messages
        return MessagesResponse(
            messages=request.messages,
            quickReplies=[],
        )

    def get_history(self, chat_id: int, user_id: int) -> History | None:
        """Get history by chat id"""
        history = history_db.get_history(chat_id)
        if history is None:
            raise InvalidChatIdException
        if history.user_id != user_id:
            raise UnauthorizedUserEditingHistoryException
        return history

    def update_history(self, chat_id: int, user_id: int, messages: list[Message]):
        """Update History table by appending new messages for valid chat id"""
        history = self.get_history(chat_id, user_id)
        history_db.update_messages(chat_id, messages)

        return MessagesResponse(
            chat=Chat(id=history.chat.id, summary=history.chat.summary),
            messages=messages,
            quickReplies=[],
        )

    def update_history_by_ids(
        self, openai_id: str, user_id: int, messages: list[Message]
    ) -> MessagesResponse:
        """Update History table by appending new messages, otherwise start a
        new conversation."""
        history = history_db.get_history_by_ids(openai_id, user_id)

        chat_id = None
        if history is None:
            # Prime the conversation with a prompt
            promt = {
                "role": "system",
                "content": """Summarize chat message. Here are some examples. 
                EXAMPLE 1: 
                User: "When does UW open general admissions?"
                Summary: "UW general admissions"
                EXAMPLE 2:
                User: "Can I cancel my housing agreement early?"
                Summary: "Cancel housing agreement"
                EXAMPLE 3:
                User: "How do I apply for scholarships?"
                Summary: "Apply for scholarships"
                """,
            }
            first_message = {
                "role": "user",
                "content": messages[0].content,
            }
            # Add prompt and first message to payload
            payload = [promt, first_message]
            # Generate summary
            summary = (
                openai.ChatCompletion.create(
                    model=settings.chatgpt_model,
                    messages=payload,
                )
                .choices[0]
                .message.content
            )

            chat_id = history_db.create_new_history_ids(openai_id, user_id, summary)
        else:
            if history.user_id != user_id:
                raise UnauthorizedUserEditingHistoryException()
            chat_id = history.chat.id

        history_db.update_messages_by_ids(openai_id, user_id, messages)

        history = history_db.get_history(chat_id)

        return MessagesResponse(
            chat=Chat(id=chat_id, summary=history.chat.summary),
            messages=messages,
            quickReplies=[],
        )


class UnauthorizedUserEditingHistoryException(Exception):
    """Raised when user tries to edit history that does not belong to them."""
