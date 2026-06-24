import { useState, type FormEvent } from "react";

import { ChatWindow } from "@/components/assistant/ChatWindow";
import { useApp } from "@/context/AppContext";
import { chatSeed } from "@/data/mockData";
import type { ChatMessage } from "@/types";

const suggestions = [
  "Show unknown visitors after 7 PM",
  "Who checked in late today?",
  "Summarize today's alerts",
  "Any access denials near server room?",
];

function buildReply(query: string) {
  const lower = query.toLowerCase();
  if (lower.includes("unknown visitors")) {
    return "There were 2 unknown visitors after 7 PM. One appeared near the side door and one at the rear entrance.";
  }
  if (lower.includes("late")) {
    return "Three employees checked in late today, mostly within the 08:10 to 08:35 AM range.";
  }
  if (lower.includes("alerts")) {
    return "Today’s alerts include 1 critical unknown-person event, 1 high-severity tailgating warning, and 2 medium/low items.";
  }
  return "I found matching security events in the current tenant. I can break this down by time, camera, or severity if you want.";
}

export function Assistant() {
  const { currentTenant } = useApp();
  const [messages, setMessages] = useState<ChatMessage[]>(chatSeed);
  const [input, setInput] = useState("");

  function send(event: FormEvent) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;

    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", content: trimmed, time: "Just now" },
      { id: crypto.randomUUID(), role: "assistant", content: buildReply(trimmed), time: "Just now" },
    ]);
    setInput("");
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">GenAI assistant</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Chat with tenant logs</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
          Query attendance, visitors, access events, and alerts using natural language for {currentTenant?.name ?? "this tenant"}.
        </p>
      </section>

      <ChatWindow messages={messages} input={input} setInput={setInput} onSend={send} chips={suggestions} />
    </div>
  );
}
