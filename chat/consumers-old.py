# following https://channels.readthedocs.io/en/latest/tutorial/part_2.html
# chat/consumers.py
import json
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message, Chat
from .views import get_last_10_messages, get_current_chat
from channels.db import database_sync_to_async

User = get_user_model()
# a channel is a mailbox where messages can be sent to.
# a group is a group of related channels.

#everything has access to self.channel_layer because
#this is extending the websocketconsumer
#the channel name is added when the socket connects below
class ChatConsumer(AsyncWebsocketConsumer):

    @database_sync_to_async
    def get_username(self, username):
      User.objects.get(username=username)

    async def fetch_messages(self, data):
      #data contains data from the front end request and will contain the chatId to load
      #gets messages from the database and turns them into json
      #using helper functions below
      #then uses the send chat message function below to output
      # print(f'DATA {data}')
      # messages = get_last_10_messages(data['chatId'])
      messages = await database_sync_to_async(Chat.objects.get(id=data['chatId']).messages.order_by('-timestamp').all()[:10])
      # print(f'MESSAGES TEST {messages}')
      content = {
        'command':'messages',
        'messages': self.messages_to_json(messages)
      }
      # print(f'CONTENT {content}')
      await self.send_chat_message(content)

    async def new_message(self, data):
      #we are passing through the user to the backend through the from field
      author = data['from']
      user = await self.get_username(author)
      author_user = user
      # print(f'AUTHOR {author_user}')
      message =  await database_sync_to_async(Message.objects.create(
        author=author_user, 
        content=data['message']))
      #current_chat is imported at the top from the views.py
      #it finds the current chat based on the ID sent by the frontend
      #and will add the message to the chat
      current_chat = await database_sync_to_async(Chat.objects.get(id=data['chatId']))
      current_chat.messages.add(message)
      await database_sync_to_async(current_chat.save())
      content = {
        'command':'new_message',
        'message': self.message_to_json(message)
      }
      await self.send_chat_message(content)

    def messages_to_json(self, messages):
      #turns the messages from the db to json
      #convenience methods in convenience methods x.x
      result = []
      for message in messages:
        result.append(self.message_to_json(message))
      return result

    def message_to_json(self, message):
      return {
        #we know these fields from the model
        'id': message.id,
        'author':message.author.username,
        'content':message.content,
        'timestamp': str(message.timestamp)
      }

    commands = {
      'fetch_messages': fetch_messages,
      'new_message': new_message
    }

    async def connect(self):
        # obtains the input room name
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        # constructs the channel group name from the room name
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # accepts the connection from/links with the front end websocket
        # so it can receive data from the user
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        print(data)
        # at the top of the class we added a dictionary which
        # associated different 'commands' with helper functions we have written
        # the code below reads in a command from the user data which is automatically
        # filtered into the receive method by channels and will call either function based
        # on the command input by the front end.
        await self.commands[data['command']](self, data)
    
    async def send_chat_message(self, message):
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )
        
    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        # Send message to WebSocket
        await self.send(text_data=json.dumps(message))