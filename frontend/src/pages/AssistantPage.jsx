import { useEffect, useRef, useState } from "react";

import { PageHeader } from "@/app/layouts/PanelLayout";
import { TOOL_LABELS, chatApi } from "@/features/chat/api/chatApi";
import { useApiQuery } from "@/shared/hooks/useApiQuery";
import { num } from "@/shared/lib/format";
import { EmptyState, ErrorState } from "@/shared/ui/Feedback";

// Only the last few turns are sent back: every turn is re-billed on each
// request, so an unbounded history quietly multiplies the cost of a long
// conversation. The server caps this too — this is the polite half.
const HISTORY_TURNS = 8;

const SUGGESTIONS = [
  "بهره‌وری یونیت‌ها چقدره؟",
  "کدام پزشک بیشترین سود را برای کلینیک ساخته؟",
  "چقدر درمان تأییدشده هنوز انجام نشده؟",
  "کدام بیماران را باید برای فراخوان تماس بگیریم؟",
];

function ToolChips({ tools }) {
  const seen = [...new Set(tools ?? [])].filter((t) => t !== "clinic_context");
  if (!seen.length) return null;
  return (
    <div className="mt-2.5 flex flex-wrap items-center gap-1.5 border-t border-ink-100 pt-2.5">
      <span className="text-[10px] font-bold text-ink-400">بر پایه:</span>
      {seen.map((t) => (
        <span key={t} className="rounded-md bg-brand-50 px-1.5 py-0.5 text-[10px] font-bold text-brand-700">
          {TOOL_LABELS[t] ?? t}
        </span>
      ))}
    </div>
  );
}

function Bubble({ turn }) {
  const mine = turn.role === "user";
  return (
    <div className={`flex ${mine ? "justify-start" : "justify-end"}`}>
      <div
        className={`max-w-[46rem] rounded-2xl px-4 py-3 text-sm leading-7 ${
          mine
            ? "bg-brand-700 text-white"
            : turn.failed
              ? "border border-rose-200 bg-rose-50 text-rose-800"
              : "border border-ink-200 bg-white text-ink-800 shadow-card"
        }`}
      >
        <div className="whitespace-pre-wrap">{turn.content}</div>
        {!mine && <ToolChips tools={turn.tools} />}
      </div>
    </div>
  );
}

export function AssistantPage() {
  const status = useApiQuery((s) => chatApi.status(s));
  const [turns, setTurns] = useState([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns, busy]);

  const send = async (text) => {
    const message = (text ?? draft).trim();
    if (!message || busy) return;

    // The history sent is the conversation *before* this message; appending
    // first and then slicing would send the question twice.
    const history = turns
      .filter((t) => !t.failed)
      .slice(-HISTORY_TURNS)
      .map(({ role, content }) => ({ role, content }));

    setTurns((t) => [...t, { role: "user", content: message }]);
    setDraft("");
    setBusy(true);
    try {
      const r = await chatApi.ask(message, history);
      setTurns((t) => [...t, { role: "assistant", content: r.reply, tools: r.tools_used }]);
    } catch (e) {
      setTurns((t) => [
        ...t,
        { role: "assistant", content: e.message || "پاسخی دریافت نشد.", failed: true },
      ]);
    } finally {
      setBusy(false);
    }
  };

  if (status.data && !status.data.enabled) {
    return (
      <>
        <PageHeader title="دستیار هوشمند" />
        <ErrorState message="دستیار هوشمند پیکربندی نشده است. کلید AVALAI_API_KEY را در فایل .env تنظیم کنید." />
      </>
    );
  }

  return (
    <>
      {/* The upstream model id is deliberately not shown: it tells a clinic
          manager nothing actionable, and naming the provider and model in the
          UI is free reconnaissance for anyone probing the panel. */}
      <PageHeader
        title="دستیار هوشمند"
        subtitle="پرسش درباره عملکرد کلینیک — پاسخ‌ها از همان گزارش‌های داشبورد می‌آیند"
      />

      <div className="flex h-[calc(100dvh-14rem)] flex-col rounded-2xl border border-ink-200/80 bg-ink-50/60">
        <div className="flex-1 space-y-4 overflow-y-auto p-5">
          {!turns.length && (
            <div className="pt-6">
              <EmptyState
                title="بپرسید تا از روی داده‌های کلینیک پاسخ بدهم."
                hint="اعدادی که می‌گویم از همان محاسبه‌های داشبورد می‌آیند."
              />
              <div className="mx-auto mt-5 flex max-w-2xl flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="rounded-xl border border-ink-200 bg-white px-3 py-2 text-xs font-medium
                      text-ink-700 shadow-card transition-colors hover:border-brand-300 hover:text-brand-700"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {turns.map((t, i) => <Bubble key={i} turn={t} />)}

          {busy && (
            <div className="flex justify-end">
              <div className="flex items-center gap-2 rounded-2xl border border-ink-200 bg-white px-4 py-3 shadow-card">
                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-brand-200 border-t-brand-600" />
                <span className="text-xs text-ink-500">در حال بررسی گزارش‌ها…</span>
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <form
          onSubmit={(e) => { e.preventDefault(); send(); }}
          className="flex items-end gap-2 border-t border-ink-200 bg-white p-3"
        >
          <textarea
            rows={1}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            // Enter sends, Shift+Enter breaks the line — the convention every
            // chat UI uses, and the one a manager will try first.
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
            }}
            placeholder="مثلاً: درآمد مرداد چقدر بود؟"
            className="max-h-40 min-h-[2.75rem] flex-1 resize-y rounded-xl border border-ink-200 px-3.5 py-2.5
              text-sm leading-7 text-ink-800 transition-colors placeholder:text-ink-400
              focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
          />
          <button
            type="submit"
            disabled={busy || !draft.trim()}
            className="h-11 shrink-0 rounded-xl bg-brand-700 px-5 text-sm font-bold text-white
              transition-colors hover:bg-brand-800 disabled:bg-ink-300"
          >
            ارسال
          </button>
        </form>
      </div>

      <p className="mt-3 text-xs leading-6 text-ink-400">
        دستیار عدد نمی‌سازد: هر رقم از همان محاسبه‌ای می‌آید که صفحه‌های داشبورد نشان
        می‌دهند، و برچسب‌های زیر هر پاسخ می‌گویند از کدام گزارش خوانده شده تا بتوانید
        همان صفحه را باز کنید و ببینید. {turns.length > 0 && `${num(turns.length)} پیام در این گفت‌وگو.`}
      </p>
    </>
  );
}
