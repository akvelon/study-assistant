# Endpoints

## /messages (Auth optional)

If no auth bearer, then messages are treated as guest mode, not
saved to database.

If auth bearer is supplied, unless an existing **messages** list used from
**/history** endpoint, a new conversation starts and saved as new history.

To start a new conversation, send request as in the schema. Then append any
new user messages to the **/messages** post return.

## /history (Auth required)

Return corresponding user's list of entire message history. The history then 
can be used to resume existing conversation. To do so, take the **messages**
and append the new user's message to it and begin using **/messages** endpoint
as usual.
