import { useState, useEffect, useRef } from 'react';
import type { KeyboardEvent } from 'react';
import { useAuth } from '@clerk/clerk-react';
import { useParams, useNavigate } from 'react-router-dom';
import '../styles/ChatPage.css';

interface User {
  id: string;
  fullName: string;
  phoneNumber: string;
  publicEmail: string;
}

interface Message {
  id: string;
  content: string;
  senderId: number;
  receiverId: number;
  createdAt: string;
  isRead: boolean;
  // For display purposes (from WebSocket)
  sender?: {
    id: number;
    fullName: string;
  };
  receiver?: {
    id: number;
    fullName: string;
  };
}

const ChatPage = () => {
  const { getToken } = useAuth();
  const { userId } = useParams();
  const navigate = useNavigate();
  const socketRef = useRef<WebSocket | null>(null);
  
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  // Fetch current user data
  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        const token = await getToken();
        const response = await fetch('http://localhost:8000/users/me', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const userData = await response.json();
          setCurrentUser(userData);
        } else {
          // If user doesn't exist, redirect to profile page
          if (response.status === 404) {
            navigate('/');
          }
          throw new Error(`Failed to fetch current user: ${response.status}`);
        }
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Failed to fetch current user');
      }
    };

    fetchCurrentUser();
  }, [getToken, navigate]);

  // Fetch all users
  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true);
      try {
        const token = await getToken();
        const response = await fetch('http://localhost:8000/users', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch users: ${response.status}`);
        }

        const usersData = await response.json();
        // Filter out current user from the list
        const filteredUsers = currentUser 
          ? usersData.filter((user: User) => user.id !== currentUser.id)
          : usersData;
          
        setUsers(filteredUsers);
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Failed to fetch users');
      } finally {
        setLoading(false);
      }
    };

    if (currentUser) {
      fetchUsers();
    }
  }, [getToken, currentUser]);

  // If userId is provided in URL, select that user
  useEffect(() => {
    if (userId && users.length > 0) {
      const user = users.find(u => u.id === userId);
      if (user) {
        setSelectedUser(user);
      }
    }
  }, [userId, users]);

  // Setup WebSocket connection for real-time messaging
  // This will be established when the current user is set
  useEffect(() => {
    if (currentUser) {
      const socket = new WebSocket(`ws://localhost:8000/ws/${currentUser.id}`);
      
      socket.onopen = () => {
        console.log('WebSocket connection established');
      };
      
      socket.onmessage = (event) => {
        const newMessage = JSON.parse(event.data);
        console.log("websocket ", newMessage)
        setMessages(prev => [...prev, newMessage]);
      };
      
      socket.onclose = () => {
        console.log('WebSocket connection closed');
      };
      
      socketRef.current = socket;
      
      return () => {
        socket.close();
      };
    }
  }, [currentUser]);

  // Fetch messages when a user is selected using GraphQL
  useEffect(() => {
    const fetchMessages = async () => {
      if (!selectedUser || !currentUser) return;
      
      setLoading(true);
      try {
        const token = await getToken();
        
        const query = `
          query GetMessages($receiverId: Int!) {
            messages(receiverId: $receiverId) {
              id
              content
              senderId
              receiverId
              createdAt
              isRead
            }
          }
        `;
     
        const response = await fetch('http://localhost:8000/graphql', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            query,
            variables: { receiverId: parseInt(selectedUser.id) }
          })
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch messages: ${response.status}`);
        }
        const result = await response.json();
        if (result.errors) {
          throw new Error(result.errors[0].message);
        }
        
        setMessages(result.data.messages);
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Failed to fetch messages');
      } finally {
        setLoading(false);
      }
    };

    fetchMessages();
  }, [selectedUser, currentUser, getToken]);

  // Handle user selection from the sidebar
  // This will also navigate to the chat page with the selected user
  const handleUserSelect = (user: User) => {
    setSelectedUser(user);
    navigate(`/chat/${user.id}`);
  };

  // Handle sending a message
  // This will use GraphQL mutation to send the message
  // and update the messages state
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    if (!newMessage.trim() || !selectedUser || !currentUser) return;
    
    try {
      const token = await getToken();
      
      const mutation = `
        mutation SendMessage($receiverId: Int!, $content: String!) {
          sendMessage(receiverId: $receiverId, content: $content) {
            id
            content
            senderId
            receiverId
            createdAt
            isRead
          }
        }
      `;
      
      const response = await fetch('http://localhost:8000/graphql', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          query: mutation,
          variables: { 
            receiverId: parseInt(selectedUser.id),
            content: newMessage
          }
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.status}`);
      }

      const result = await response.json();
      if (result.errors) {
        throw new Error(result.errors[0].message);
      }

      setMessages(prev => [...prev, result.data.sendMessage]);
      setIsSubmitting(false);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to send message');
    }
  };

  // Format the message timestamp to a readable format
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Helper function to determine if a message was sent by the current user
  const isCurrentUserMessage = (message: Message) => {
    return message.senderId === parseInt(currentUser?.id || '0');
  };

  // Handle keydown event for sending messages
  // Note: This will prevent new line on Enter key press
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Prevent new line in input
      handleSendMessage(e);
    }
  };

  return (
    <div className="chat-page">
      {error && <div className="error-message">{error}</div>}
      
      <div className="chat-container">
        <div className="users-sidebar">
          <h2>Contacts</h2>
          {loading && users.length === 0 ? (
            <div className="loading">Loading contacts...</div>
          ) : (
            <ul className="users-list">
              {users.map(user => (
                <li 
                  key={user.id} 
                  className={`user-item ${selectedUser?.id === user.id ? 'active' : ''}`}
                  onClick={() => handleUserSelect(user)}
                >
                  <div className="user-avatar">
                    {user.fullName.charAt(0).toUpperCase()}
                  </div>
                  <div className="user-info">
                    <h3>{user.fullName}</h3>
                    <p>{user.publicEmail}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
        
        <div className="chat-area">
          {selectedUser ? (
            <>
              <div className="chat-header">
                <h2>{selectedUser.fullName}</h2>
                <p>{selectedUser.publicEmail}</p>
              </div>
              
              <div className="messages-container">
                {loading ? (
                  <div className="loading">Loading messages...</div>
                ) : messages.length === 0 ? (
                  <div className="no-messages">No messages yet. Start the conversation!</div>
                ) : (
                  <div className="messages-list">
                    {messages.map(message => (
                      <div 
                        key={message.id}
                        className={`message ${isCurrentUserMessage(message) ? 'sent' : 'received'}`}
                      >
                        <div className="message-content">{message.content}</div>
                        <div className="message-time">{formatTime(message.createdAt)}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              <form className="message-form" onSubmit={handleSendMessage}>
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type a message..."
                  disabled={isSubmitting}
                  required
                />
                <button 
                  type="submit" 
                  className="send-button"
                  disabled={isSubmitting || !newMessage.trim()}
                >
                  {isSubmitting ? 'Sending...' : 'Send'}
                </button>
              </form>
            </>
          ) : (
            <div className="no-chat-selected">
              <div className="placeholder-content">
                <h2>Select a contact to start messaging</h2>
                <p>Choose from your contacts list on the left</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatPage; 