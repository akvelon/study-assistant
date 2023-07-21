from api.db.history import history_db, InvalidChatIdException
from api.endpoints.schemas import Chat, Message, MessagesResponse
from api.endpoints.user import User


class HistoryManager:
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
            else:
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

        else:
            # Otherwise guest user, just messages
            return MessagesResponse(
                messages=request.messages,
                quickReplies=[],
            )

    def update_history(self, chat_id: int, user_id: int, messages: list[Message]):
        """Update History table by appending new messages for valid chat id"""
        if (history := history_db.get_history(chat_id)) is None:
            raise InvalidChatIdException

        if history.user_id != user_id:
            raise UnauthorizedUserEditingHistoryException

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
            chat_id = history_db.create_new_history_ids(openai_id, user_id)
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
    pass
