import { Send } from "lucide-react";
import type { FormEvent } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { formatTime } from "@/utils/format";
import type { ChatMessage } from "@/types";

type ChatWindowProps = {
  messages: ChatMessage[];
  input: string;
  setInput: (value: string) => void;
  onSend: (event: FormEvent) => void;
  chips: string[];
};

export function ChatWindow({ messages, input, setInput, onSend, chips }: ChatWindowProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-[1.25fr_0.75fr]">
      <Card className="grid gap-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-semibold">GenAI Log Assistant</h3>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Ask questions in plain language to query logs and summarize events.
            </p>
          </div>
          <Badge tone="info">Tenant-scoped</Badge>
        </div>

        <div className="grid max-h-[520px] gap-3 overflow-y-auto pr-2">
          {messages.map((message) => (
            <div
              key={message.id}
              className={
                message.role === "user"
                  ? "ml-auto max-w-[80%] rounded-[1.5rem] bg-brand-500 px-4 py-3 text-white shadow-soft"
                  : "max-w-[84%] rounded-[1.5rem] border border-white/10 bg-slate-950/30 px-4 py-3"
              }
            >
              <p className="text-sm leading-6">{message.content}</p>
              <span className="mt-2 block text-xs opacity-75">{formatTime(message.time)}</span>
            </div>
          ))}
        </div>

        <form onSubmit={onSend} className="flex gap-3">
          <Input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask VisionPass AI something like: Show unknown visitors after 7 PM"
          />
          <Button type="submit" rightIcon={<Send className="h-4 w-4" />}>
            Ask
          </Button>
        </form>
      </Card>

      <Card className="grid content-start gap-4">
        <div>
          <h3 className="text-base font-semibold">Suggested queries</h3>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Tap a chip to seed the chat.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {chips.map((chip) => (
            <Badge key={chip} tone="neutral" className="cursor-pointer">
              {chip}
            </Badge>
          ))}
        </div>
        <div className="rounded-2xl border border-white/10 bg-slate-950/30 p-4 text-sm leading-6 text-slate-600 dark:text-slate-300">
          The assistant can summarize alerts, find late arrivals, explain unusual camera activity, and cross-reference
          identity confidence against access events.
        </div>
      </Card>
    </div>
  );
}
