import { useRef, useEffect } from "react";
import {
  Button,
  Input,
  Card,
  Avatar,
  Spin,
  Typography,
  Space,
  Flex,
  theme,
  ConfigProvider,
} from "antd";
import {
  SendOutlined,
  EnvironmentOutlined,
  LoadingOutlined,
  RocketOutlined,
  CompassOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { useTravelChat } from "./usetravelchat";

const { Title, Text } = Typography;

export default function TravelAdvisor() {
  const { token } = theme.useToken();
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);

  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    sendMessage,
  } = useTravelChat();

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({
        behavior: "smooth",
        block: "end",
      });
    }
  };

  const suggestedQuestions = [
    "🔥 Events happening in December",
    "🏠 Where to stay in Lagos",
    "🧳 Help me plan my trip",
    "👗 Outfit suggestions",
  ];

  const handleSuggestedQuestion = (question) => {
    sendMessage(question);
  };

  const customTheme = {
    token: {
      colorPrimary: "#1890ff",
      borderRadius: 8,
    },
    components: {
      Card: {
        borderRadiusLG: 16,
      },
      Button: {
        borderRadius: 8,
      },
      Input: {
        borderRadius: 8,
      },
    },
  };

  return (
    <ConfigProvider theme={customTheme}>
      <div
        style={{
          minHeight: "100vh",
          background: `linear-gradient(135deg, ${token.blue1} 0%, ${token.purple1} 100%)`,
          padding: "32px 16px",
        }}
      >
        <div style={{ maxWidth: "1024px", margin: "0 auto" }}>
          {/* Header */}
          <div style={{ textAlign: "center", marginBottom: 32 }}>
            <Space direction="vertical" size="middle" style={{ width: "100%" }}>
              <Flex justify="center" align="center" gap={12}>
                <RocketOutlined
                  style={{
                    fontSize: 40,
                    color: token.colorPrimary,
                    background: `linear-gradient(45deg, ${token.colorPrimary}, ${token.purple6})`,
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                    backgroundClip: "text",
                  }}
                />
                <Title
                  level={1}
                  style={{
                    margin: 0,
                    background: `linear-gradient(45deg, ${token.colorPrimary}, ${token.purple6})`,
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                    backgroundClip: "text",
                  }}
                >
                  Yinka
                </Title>
              </Flex>
            </Space>
          </div>

          {/* Chat Interface */}
          <Card
            style={{
              boxShadow: `0 20px 40px ${token.colorBgElevated}40`,
              border: "none",
              overflow: "hidden",
            }}
            title={
              <Flex align="center" gap={12} justify="space-between">
                <Flex align="center" gap={12}>
                  <CompassOutlined style={{ fontSize: 20 }} />
                  <span>Chat with your Travel Advisor</span>
                </Flex>
                {/* Optional: Add scroll to bottom button */}
                {messages.length > 3 && (
                  <Button
                    type="text"
                    size="small"
                    onClick={scrollToBottom}
                    style={{ color: "white" }}
                  >
                    ↓ Latest
                  </Button>
                )}
              </Flex>
            }
            headStyle={{
              background: `linear-gradient(135deg, ${token.colorPrimary} 0%, ${token.purple6} 100%)`,
              color: "white",
              padding: "16px 24px",
              fontSize: 16,
              fontWeight: 600,
            }}
            bodyStyle={{ padding: 0 }}
          >
            {/* Messages Area with ref */}
            <div
              ref={messagesContainerRef}
              style={{
                height: 500,
                overflowY: "auto",
                padding: 24,
                background: token.colorBgContainer,
                scrollBehavior: "smooth", // Enable smooth scrolling
              }}
            >
              {messages.length === 0 ? (
                <div
                  style={{
                    textAlign: "center",
                    height: "100%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <Space
                    direction="vertical"
                    size="large"
                    style={{ width: "100%" }}
                  >
                    <div>
                      <Text
                        type="secondary"
                        style={{
                          fontSize: 16,
                          maxWidth: 100,
                          margin: "0 auto",
                        }}
                      >
                        Hey there! 🎉 Ready to Detty this December in Lagos? I
                        am Yinka and I can help you plan your trip, find events,
                        comfy places to stay, or outfit inspo. What would you
                        like to explore
                      </Text>
                    </div>
                    <div style={{ maxWidth: 500, margin: "0 auto" }}>
                      <Text
                        strong
                        style={{
                          color: token.colorText,
                          marginBottom: 16,
                          display: "block",
                          fontSize: 16,
                        }}
                      >
                        ✨ Try asking:
                      </Text>
                      <Space
                        direction="vertical"
                        style={{ width: "100%" }}
                        size="middle"
                      >
                        {suggestedQuestions.map((question, index) => (
                          <Button
                            key={index}
                            type="default"
                            size="large"
                            block
                            style={{
                              textAlign: "left",
                              height: "auto",
                              padding: "16px 20px",
                              whiteSpace: "normal",
                              lineHeight: 1.5,
                              border: `1px solid ${token.colorBorder}`,
                              borderRadius: 12,
                              transition: "all 0.3s ease",
                            }}
                            onClick={() => handleSuggestedQuestion(question)}
                          >
                            <EnvironmentOutlined
                              style={{
                                marginRight: 8,
                                color: token.colorPrimary,
                              }}
                            />
                            {question}
                          </Button>
                        ))}
                      </Space>
                    </div>
                  </Space>
                </div>
              ) : (
                <Space
                  direction="vertical"
                  size="large"
                  style={{ width: "100%" }}
                >
                  {messages.map((message, index) => (
                    <div
                      key={`${message.id}-${index}`}
                      style={{
                        display: "flex",
                        gap: 12,
                        justifyContent:
                          message.role === "user" ? "flex-end" : "flex-start",
                        alignItems: "flex-start",
                      }}
                      // Add special styling for the last message
                      className={
                        index === messages.length - 1 ? "last-message" : ""
                      }
                    >
                      {message.role === "assistant" && (
                        <Avatar
                          size={40}
                          style={{
                            backgroundColor: token.colorPrimary,
                            flexShrink: 0,
                            boxShadow: `0 4px 12px ${token.colorPrimary}30`,
                            // Highlight last message
                            ...(index === messages.length - 1 && {
                              boxShadow: `0 6px 16px ${token.colorPrimary}50`,
                              transform: "scale(1.05)",
                            }),
                          }}
                          icon={<RocketOutlined />}
                        />
                      )}
                      <div
                        style={{
                          maxWidth: "75%",
                          padding: "16px 20px",
                          borderRadius: 16,
                          backgroundColor:
                            message.role === "user"
                              ? token.colorPrimary
                              : token.colorBgElevated,
                          color:
                            message.role === "user" ? "white" : token.colorText,
                          boxShadow:
                            message.role === "user"
                              ? `0 4px 12px ${token.colorPrimary}30`
                              : `0 2px 8px ${token.colorBgElevated}60`,
                          position: "relative",
                          // Highlight last message
                          ...(index === messages.length - 1 && {
                            boxShadow:
                              message.role === "user"
                                ? `0 6px 16px ${token.colorPrimary}50`
                                : `0 4px 12px ${token.colorBgElevated}80`,
                            transform: "scale(1.02)",
                            transition: "all 0.3s ease",
                          }),
                        }}
                      >
                        <Text
                          style={{
                            color:
                              message.role === "user"
                                ? "white"
                                : token.colorText,
                            whiteSpace: "pre-wrap",
                            lineHeight: 1.6,
                            fontSize: 15,
                            display: "block",
                          }}
                        >
                          {message.content}
                        </Text>
                        {/* Show "Latest" badge on last message */}
                        {index === messages.length - 1 &&
                          messages.length > 1 && (
                            <div
                              style={{
                                position: "absolute",
                                top: -8,
                                right: -8,
                                backgroundColor: token.colorSuccess,
                                color: "white",
                                fontSize: 10,
                                padding: "2px 6px",
                                borderRadius: 8,
                                fontWeight: "bold",
                              }}
                            >
                              Latest
                            </div>
                          )}
                      </div>
                      {message.role === "user" && (
                        <Avatar
                          size={40}
                          style={{
                            backgroundColor: token.colorTextSecondary,
                            flexShrink: 0,
                            boxShadow: `0 4px 12px ${token.colorTextSecondary}30`,
                            // Highlight last message
                            ...(index === messages.length - 1 && {
                              boxShadow: `0 6px 16px ${token.colorTextSecondary}50`,
                              transform: "scale(1.05)",
                            }),
                          }}
                          icon={<UserOutlined />}
                        />
                      )}
                    </div>
                  ))}

                  {isLoading && (
                    <div
                      style={{
                        display: "flex",
                        gap: 12,
                        justifyContent: "flex-start",
                        alignItems: "flex-start",
                      }}
                    >
                      <Avatar
                        size={40}
                        style={{
                          backgroundColor: token.colorPrimary,
                          flexShrink: 0,
                          boxShadow: `0 4px 12px ${token.colorPrimary}30`,
                        }}
                        icon={<RocketOutlined />}
                      />
                      <div
                        style={{
                          padding: "16px 20px",
                          borderRadius: 16,
                          backgroundColor: token.colorBgElevated,
                          boxShadow: `0 2px 8px ${token.colorBgElevated}60`,
                        }}
                      >
                        <Flex align="center" gap={12}>
                          <Spin
                            indicator={
                              <LoadingOutlined
                                style={{
                                  fontSize: 18,
                                  color: token.colorPrimary,
                                }}
                              />
                            }
                          />
                          <Text
                            style={{
                              color: token.colorTextSecondary,
                              fontSize: 15,
                            }}
                          >
                            Planning your adventure...
                          </Text>
                        </Flex>
                      </div>
                    </div>
                  )}

                  {/* Invisible element to scroll to */}
                  <div ref={messagesEndRef} style={{ height: 1 }} />
                </Space>
              )}
            </div>

            {/* Input Form */}
            <div
              style={{
                borderTop: `1px solid ${token.colorBorderSecondary}`,
                backgroundColor: token.colorBgLayout,
                padding: 20,
              }}
            >
              <form onSubmit={handleSubmit}>
                <Flex gap={12}>
                  <Input
                    name="prompt"
                    value={input}
                    onChange={handleInputChange}
                    placeholder="Ask about destinations, travel tips, planning advice..."
                    disabled={isLoading}
                    size="large"
                    onPressEnter={(e) => {
                      e.preventDefault();
                      if (!isLoading && input.trim()) {
                        handleSubmit(e);
                      }
                    }}
                    style={{
                      flex: 1,
                      borderRadius: 12,
                      fontSize: 16,
                    }}
                    suffix={
                      <EnvironmentOutlined
                        style={{
                          color: token.colorTextTertiary,
                          fontSize: 16,
                        }}
                      />
                    }
                  />
                  <Button
                    type="primary"
                    htmlType="submit"
                    disabled={isLoading || !input.trim()}
                    size="large"
                    loading={isLoading}
                    icon={!isLoading && <SendOutlined />}
                    style={{
                      borderRadius: 12,
                      minWidth: 60,
                      height: 40,
                      background: `linear-gradient(135deg, ${token.colorPrimary} 0%, ${token.purple6} 100%)`,
                      border: "none",
                      boxShadow: `0 4px 12px ${token.colorPrimary}30`,
                    }}
                  />
                </Flex>
              </form>
            </div>
          </Card>

          {/* Footer */}
          <div style={{ textAlign: "center", marginTop: 32 }}>
            <Text
              type="secondary"
              style={{
                fontSize: 14,
                opacity: 0.8,
              }}
            >
              🤖 Powered by AI • Get personalized travel advice and
              recommendations ✈️
            </Text>
          </div>
        </div>
      </div>
    </ConfigProvider>
  );
}
