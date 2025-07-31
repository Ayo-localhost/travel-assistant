"use client";

import { useChat } from "ai/react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Plane, Send, MapPin, Loader2 } from "lucide-react";
import type { FormEvent } from "react";

export default function TravelAdvisor() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } =
    useChat();

  const suggestedQuestions = [
    "Plan a 7-day trip to Lagos for first-time visitors",
    "Best budget destinations in Africa for summer",
    "What should I pack for a trip to Lagos?",
    "Recommend romantic getaways in Nigeria",
  ];

  const handleSuggestedQuestion = (question: string) => {
    // Create a proper form event for React 19
    const form = document.createElement("form");
    const input = document.createElement("input");
    input.name = "prompt";
    input.value = question;
    form.appendChild(input);

    const event = new Event("submit", {
      bubbles: true,
      cancelable: true,
    }) as unknown as FormEvent<HTMLFormElement>;
    Object.defineProperty(event, "target", {
      value: form,
      enumerable: true,
    });
    Object.defineProperty(event, "currentTarget", {
      value: form,
      enumerable: true,
    });

    handleSubmit(event);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Plane className="h-8 w-8 text-blue-600" />
            <h1 className="text-4xl font-bold text-gray-800">
              AI Travel Advisor
            </h1>
          </div>
          <p className="text-gray-600 text-lg">
            Your personal travel companion for planning amazing adventures
          </p>
        </div>

        {/* Chat Interface */}
        <Card className="shadow-xl border-0">
          <CardHeader className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-t-lg py-2">
            <CardTitle className="flex items-center gap-2">
              <MapPin className="h-5 w-5" />
              Chat with your Travel Advisor
            </CardTitle>
          </CardHeader>

          <CardContent className="p-0">
            <ScrollArea className="h-[500px] p-6">
              {messages.length === 0 ? (
                <div className="text-center space-y-6">
                  <div className="text-gray-500 mb-6">
                    <Plane className="h-16 w-16 mx-auto mb-4 text-blue-300" />
                    <p className="text-lg">
                      Ready to plan your next adventure?
                    </p>
                    <p className="text-sm">
                      Ask me anything about travel destinations, planning, or
                      tips!
                    </p>
                  </div>

                  <div className="space-y-2">
                    <p className="text-sm font-medium text-gray-700 mb-3">
                      Try asking:
                    </p>
                    {suggestedQuestions.map((question, index) => (
                      <Button
                        key={index}
                        variant="outline"
                        className="w-full text-left justify-start h-auto p-3 text-sm bg-transparent"
                        onClick={() => handleSuggestedQuestion(question)}
                      >
                        {question}
                      </Button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex gap-3 ${
                        message.role === "user"
                          ? "justify-end"
                          : "justify-start"
                      }`}
                    >
                      {message.role === "assistant" && (
                        <Avatar className="h-8 w-8 bg-blue-600">
                          <AvatarFallback className="text-white text-xs">
                            <Plane className="h-4 w-4" />
                          </AvatarFallback>
                        </Avatar>
                      )}

                      <div
                        className={`max-w-[80%] rounded-lg px-4 py-2 ${
                          message.role === "user"
                            ? "bg-blue-600 text-white"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">
                          {message.content}
                        </p>
                      </div>

                      {message.role === "user" && (
                        <Avatar className="h-8 w-8 bg-gray-600">
                          <AvatarFallback className="text-white text-xs">
                            You
                          </AvatarFallback>
                        </Avatar>
                      )}
                    </div>
                  ))}

                  {isLoading && (
                    <div className="flex gap-3 justify-start">
                      <Avatar className="h-8 w-8 bg-blue-600">
                        <AvatarFallback className="text-white text-xs">
                          <Plane className="h-4 w-4" />
                        </AvatarFallback>
                      </Avatar>
                      <div className="bg-gray-100 rounded-lg px-4 py-2">
                        <div className="flex items-center gap-2 text-gray-600">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span className="text-sm">
                            Planning your adventure...
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </ScrollArea>

            {/* Input Form */}
            <div className="border-t bg-gray-50 p-4">
              <form onSubmit={handleSubmit} className="flex gap-2">
                <Input
                  name="prompt"
                  value={input}
                  onChange={handleInputChange}
                  placeholder="Ask about destinations, travel tips, planning advice..."
                  className="flex-1"
                  disabled={isLoading}
                />
                <Button
                  type="submit"
                  disabled={isLoading || !input.trim()}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </form>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center mt-8 text-gray-500 text-sm">
          <p>
            Powered by AI • Get personalized travel advice and recommendations
          </p>
        </div>
      </div>
    </div>
  );
}
