import { useState } from "react";
import { api } from "../api";
import { v4 as uuidv4 } from "uuid";

export function useTravelChat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(uuidv4());

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const sendMessage = async (message) => {
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

      if (!response.data?.intent) {
        setMessages((prevMessages) => [
          ...prevMessages,
          {
            id: uuidv4(),
            role: "assistant",
            content: `🤔 Hmm, I’m still learning how to help with that!

              Here are some things you can ask me:
              • 🔥 Events happening in Lagos
              • 🏠 Where to stay
              • 🧳 Help me plan my trip
              • 👗 Outfit suggestions
              • ❓ Ask me anything about travel

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
    if (input.trim()) {
      sendMessage(input.trim());
    }
  };

  return {
    input,
    messages,
    isLoading,
    handleInputChange,
    handleSubmit,
    sendMessage,
  };
}
