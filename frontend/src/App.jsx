import { useState, useEffect, useRef } from "react";
import Sidebar from "./components/Sidebar";
import "./App.css";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const chatEndRef = useRef(null);
  const SESSION = "kid-session-01";

  // Auto scroll as messages update
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Send message to backend
  const handleSend = async (text) => {
    const userText = text || input;
    if (!userText.trim()) return;

    setMessages((prev) => [...prev, { role: "user", text: userText }]);
    setInput("");
    setTyping(true);

    const res = await fetch("http://127.0.0.1:5000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session: SESSION, message: userText }),
    });

    const data = await res.json();
    setTyping(false);

    // Handle response types
    if (data.type === "story") {
      setMessages((prev) => [...prev, { role: "assistant", text: data.story }]);
    } else if (data.type === "refined") {
      setMessages((prev) => [...prev, { role: "assistant", text: data.story }]);
    } else if (data.type === "chat") {
      setMessages((prev) => [...prev, { role: "assistant", text: data.reply }]);
    } else {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Oops! Something went wrong." },
      ]);
    }
  };

  return (
    <div className="app-bg">
      {/* LEFT SIDEBAR */}
      <Sidebar onSelectStory={(txt) => handleSend(txt)} />

      {/* RIGHT SIDE CHAT */}
      <div className="chat-container">
        <div className="chat-box">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`bubble ${msg.role === "user" ? "user" : "assistant"}`}
            >
              {msg.text}
            </div>
          ))}

          {typing && <div className="typing">Assistant is typing...</div>}
          <div ref={chatEndRef} />
        </div>

        {/* INPUT ROW */}
        <div className="input-row">
          <input
            className="chat-input"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
          />
          <button className="send-btn" onClick={() => handleSend()}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}