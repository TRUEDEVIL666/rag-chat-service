import React from 'react';
import ChatInterface from '../../components/chat/ChatInterface';

const UserChat = () => {
  return (
    <ChatInterface basePath="/user/chat" homePath="/user/home" />
  );
};

export default UserChat;
