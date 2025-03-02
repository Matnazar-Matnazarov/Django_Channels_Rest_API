from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from django.utils import timezone
import json

class ChatConsumer(AsyncJsonWebsocketConsumer):
    # Store all active connections
    active_connections = {}

    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close(code=4001)
            return
        
        self.user_id = self.scope["user"].id
        self.room_group_name = 'chat'
        
        # Add connection to active_connections
        if self.user_id in ChatConsumer.active_connections:
            ChatConsumer.active_connections[self.user_id].append(self.channel_name)
        else:
            ChatConsumer.active_connections[self.user_id] = [self.channel_name]
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        
        # Send current user info
        user_data = await self.get_user_data(self.scope["user"])
        await self.send_json({
            'type': 'user.connected',
            'user': user_data
        })
        
        # Broadcast to others that new user connected
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_list_update',
                'action': 'add',
                'user': user_data
            }
        )
        
        # Send all users list with their statuses
        await self.send_all_users()
    
    @database_sync_to_async
    def get_user_data(self, user):
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_online': self.is_user_online(user.id),
            'last_seen': str(user.last_login) if user.last_login else None
        }
    
    def is_user_online(self, user_id):
        return user_id in ChatConsumer.active_connections and len(ChatConsumer.active_connections[user_id]) > 0
    
    @database_sync_to_async
    def get_all_users(self):
        User = get_user_model()
        users = []
        for user in User.objects.all():
            users.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_online': self.is_user_online(user.id),
                'last_seen': str(user.last_login) if user.last_login else None
            })
        return users
    
    async def send_all_users(self):
        users = await self.get_all_users()
        await self.send_json({
            'type': 'user.list',
            'users': users
        })
        
        # Also broadcast to all connected clients
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_user_list',
                'users': users
            }
        )
    
    async def broadcast_user_list(self, event):
        await self.send_json({
            'type': 'user.list',
            'users': event['users']
        })
    
    async def disconnect(self, close_code):
        if hasattr(self, 'user_id'):
            # Remove this connection
            if self.user_id in ChatConsumer.active_connections:
                ChatConsumer.active_connections[self.user_id].remove(self.channel_name)
                if not ChatConsumer.active_connections[self.user_id]:
                    del ChatConsumer.active_connections[self.user_id]
                    # Update last seen time only when all connections are closed
                    await self.update_last_seen(self.scope["user"])
            
            # Get updated user data
            user_data = await self.get_user_data(self.scope["user"])
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_list_update',
                    'action': 'update',
                    'user': user_data
                }
            )
            
            # Send updated users list to all clients
            await self.send_all_users()
            
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    @database_sync_to_async
    def update_last_seen(self, user):
        user.last_login = timezone.now()
        user.save()

    async def user_list_update(self, event):
        await self.send_json({
            'type': 'user.update',
            'action': event['action'],
            'user': event['user']
        })

    async def receive_json(self, content):
        message_type = content.get('type')
        if message_type == 'chat.message':
            # Broadcast the message to the group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': content.get('message'),
                    'user': self.scope["user"].username
                }
            )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send_json({
            'type': 'chat.message',
            'message': event['message'],
            'user': event['user']
        })
