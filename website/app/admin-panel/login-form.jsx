"use client";

import { useFormState, useFormStatus } from "react-dom";

import { loginAction } from "./actions";

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="w-full rounded-xl bg-brand-600 py-3.5 text-sm font-bold text-white shadow-sm transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {pending ? "در حال بررسی…" : "ورود به پنل"}
    </button>
  );
}

export default function LoginForm({ next }) {
  const [state, formAction] = useFormState(loginAction, { error: null });

  return (
    <form action={formAction} className="space-y-4">
      <input type="hidden" name="next" value={next ?? ""} />

      <div>
        <label htmlFor="username" className="mb-1.5 block text-sm font-bold text-slate-700">
          نام کاربری
        </label>
        <input
          id="username"
          name="username"
          autoComplete="username"
          required
          dir="ltr"
          className="w-full rounded-xl border border-slate-300 px-4 py-3 text-left text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
        />
      </div>

      <div>
        <label htmlFor="password" className="mb-1.5 block text-sm font-bold text-slate-700">
          رمز عبور
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          dir="ltr"
          className="w-full rounded-xl border border-slate-300 px-4 py-3 text-left text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
        />
      </div>

      {state?.error ? (
        <p
          role="alert"
          className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
        >
          {state.error}
        </p>
      ) : null}

      <SubmitButton />
    </form>
  );
}
