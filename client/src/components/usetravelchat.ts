"use client";

import { useState, useEffect } from "react";
import { api } from "../api";
import { v4 as uuidv4 } from "uuid";

const SESSION_STORAGE_KEY = "travel_chat_session_id";

export function useTravelChat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  // Initialize session on component mount
  useEffect(() => {
    const initializeSession = () => {
      try {
        // Check if session exists in localStorage
        const existingSessionId = localStorage.getItem(SESSION_STORAGE_KEY);

        if (existingSessionId) {
          // Use existing session
          console.log("Using existing session:", existingSessionId);
          setSessionId(existingSessionId);
        } else {
          // Create new session and store it
          const newSessionId = uuidv4();
          localStorage.setItem(SESSION_STORAGE_KEY, newSessionId);
          console.log("Created new session:", newSessionId);
          setSessionId(newSessionId);
        }
      } catch (error) {
        console.error("Error accessing localStorage:", error);
        // Fallback if localStorage is not available
        console.warn("localStorage not available, using temporary session");
        setSessionId(uuidv4());
      }
    };

    initializeSession();
  }, []);

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const sendMessage = async (message) => {
    // Don't send message if session is not initialized yet
    if (!sessionId) {
      console.warn("Session not initialized yet");
      return;
    }

    // Add user message
    setMessages((prevMessages) => [
      ...prevMessages,
      { id: uuidv4(), role: "user", content: message },
    ]);

    setIsLoading(true);

    try {
      const response = await api.post("/chat", {
        message,
        session_id: sessionId,
      });

      console.log("Response from server:", response.data);
      console.log("Using session ID:", sessionId);

      if (!response.data?.intent) {
        setMessages((prevMessages) => [
          ...prevMessages,
          {
            id: uuidv4(),
            role: "assistant",
            content: `🤔 Hmm, I'm still learning how to help with that!
            
Here are some things you can ask me:
• 🔥 Events happening in Lagos
• 🏠 Where to stay
• 🧳 Help me plan my trip in Lekki
• 👗 Outfit suggestions

What would you like to explore next?`,
          },
        ]);
      } else {
        const assistantMessage = response.data.response;
        // Add assistant message using functional update
        setMessages((prevMessages) => [
          ...prevMessages,
          { id: uuidv4(), role: "assistant", content: assistantMessage },
        ]);
      }
    } catch (error) {
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          id: uuidv4(),
          role: "assistant",
          content: "❌ Something went wrong.",
        },
      ]);
      console.error(error);
    } finally {
      setIsLoading(false);
      setInput("");
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && sessionId) {
      sendMessage(input.trim());
    }
  };

  // Function to clear session (useful for testing or reset functionality)
  const clearSession = () => {
    try {
      localStorage.removeItem(SESSION_STORAGE_KEY);
      const newSessionId = uuidv4();
      localStorage.setItem(SESSION_STORAGE_KEY, newSessionId);
      setSessionId(newSessionId);
      setMessages([]);
      console.log("Session cleared and reset:", newSessionId);
    } catch (error) {
      console.error(error);
      console.warn("Could not clear session from localStorage");
    }
  };

  return {
    input,
    messages,
    isLoading,
    sessionId,
    handleInputChange,
    handleSubmit,
    sendMessage,
    clearSession, // Export this in case you want to add a reset button
  };
}
