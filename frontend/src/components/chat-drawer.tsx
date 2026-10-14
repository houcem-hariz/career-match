"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { getOffer, listOffers } from "@/lib/api";
import { answer, suggestions, type ChatContext } from "@/lib/chat";
import { MessageCircle, Send, X } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  text: string;
}

/** Chat drawer (wireframe 06): the current page stays visible on the left. */
export function ChatDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const pathname = usePathname();
  const [ctx, setCtx] = useState<ChatContext>({ offers: null, card: null });
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  const sourceId = pathname.startsWith("/offers/")
    ? decodeURIComponent(pathname.slice("/offers/".length))
    : null;

  // Reload the context each time the drawer opens, so it follows the page.
  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    Promise.all([listOffers(), sourceId ? getOffer(sourceId) : Promise.resolve(null)])
      .then(([offers, card]) => {
        if (!cancelled) setCtx({ offers, card });
      })
      .catch(() => {
        if (!cancelled) setCtx({ offers: null, card: null });
      });
    return () => {
      cancelled = true;
    };
  }, [open, sourceId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function send(text: string) {
    const question = text.trim();
    if (!question) return;
    setMessages((prev) => [
      ...prev,
      { role: "user", text: question },
      { role: "assistant", text: answer(question, ctx) },
    ]);
    setInput("");
  }

  if (!open) return null;

  return (
    <aside className="fixed right-0 top-0 z-45 flex h-full w-full max-w-sm flex-col border-l border-slate-200 bg-[#f7f7f5] shadow-2xl animate-in slide-in-from-right duration-200">
      <div className="flex items-center justify-between border-b border-slate-200 bg-white px-5 py-4">
        <div className="flex items-center gap-2">
          <MessageCircle className="h-4 w-4 text-purple-600" />
          <h2 className="text-sm font-black text-slate-900">Chat</h2>
          {ctx.card && (
            <span className="max-w-[140px] truncate rounded-full bg-purple-100 px-2 py-0.5 text-[10px] font-bold text-purple-800">
              {ctx.card.title}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          aria-label="Close chat"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto px-5 py-4">
        {messages.length === 0 && (
          <div className="space-y-3">
            <p className="text-xs text-slate-500">
              Ask about your matched offers. Answers come from your session scores, gaps and
              course simulations.
            </p>
            <div className="flex flex-col gap-2">
              {suggestions(ctx).map((question) => (
                <button
                  key={question}
                  type="button"
                  onClick={() => send(question)}
                  className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-left text-xs font-medium text-slate-700 hover:border-purple-300 hover:text-purple-700 transition-colors"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, i) => (
          <div
            key={i}
            className={`whitespace-pre-line rounded-2xl px-3.5 py-2.5 text-xs leading-relaxed ${
              message.role === "user"
                ? "ml-8 border border-slate-200 bg-white text-slate-600"
                : "mr-8 border border-purple-200 bg-white text-slate-900"
            }`}
          >
            {message.text}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="flex items-center gap-2 border-t border-slate-200 bg-white px-4 py-3"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Your message..."
          className="flex-1 rounded-xl border border-slate-200 bg-[#fafaf8] px-3 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/10"
        />
        <button
          type="submit"
          disabled={!input.trim()}
          className="rounded-xl bg-purple-600 p-2 text-white hover:bg-purple-700 disabled:opacity-40"
          aria-label="Send"
        >
          <Send className="h-3.5 w-3.5" />
        </button>
      </form>
    </aside>
  );
}
