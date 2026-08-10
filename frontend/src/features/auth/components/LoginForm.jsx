import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "@/features/auth/hooks/useAuth";
import { PASSWORD_RE, USERNAME_RE } from "@/shared/config";
import { Alert } from "@/shared/ui/Alert";
import { Button } from "@/shared/ui/Button";
import { TextField } from "@/shared/ui/TextField";

const KEYBOARD_HINT = "صفحه‌کلید را روی انگلیسی بگذارید.";

/** Mirrors the server rule so the user is told before submitting. The server
 *  check is still the authoritative one. */
function validate({ username, password }) {
  const errors = {};
  if (!username) errors.username = "نام کاربری را وارد کنید.";
  else if (!USERNAME_RE.test(username))
    // Punctuation is spelled out in words: bare "." "_" "-" inside Persian
    // text get reordered by the bidi algorithm and render scrambled.
    errors.username = `نام کاربری فقط می‌تواند شامل حروف انگلیسی، ارقام، نقطه، زیرخط و خط تیره باشد. ${KEYBOARD_HINT}`;

  if (!password) errors.password = "رمز عبور را وارد کنید.";
  else if (!PASSWORD_RE.test(password))
    errors.password = `رمز عبور فقط می‌تواند شامل حروف و نمادهای انگلیسی و بدون فاصله باشد. ${KEYBOARD_HINT}`;

  return errors;
}

export function LoginForm() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [values, setValues] = useState({ username: "", password: "" });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const update = (name) => (event) => {
    setValues((v) => ({ ...v, [name]: event.target.value }));
    // Clear this field's error as soon as the user edits it; keeping it
    // visible while they fix it reads as though the fix did not register.
    setErrors((e) => (e[name] ? { ...e, [name]: undefined } : e));
    setFormError("");
  };

  async function handleSubmit(event) {
    event.preventDefault();
    const found = validate(values);
    if (Object.keys(found).length) {
      setErrors(found);
      return;
    }

    setSubmitting(true);
    setFormError("");
    try {
      await login(values.username, values.password);
      navigate(location.state?.from ?? "/dashboard", { replace: true });
    } catch (error) {
      if (error.fields && Object.keys(error.fields).length) setErrors(error.fields);
      else setFormError(error.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-5">
      <Alert className={formError ? "animate-shake" : ""}>{formError}</Alert>

      <TextField
        label="نام کاربری"
        name="username"
        value={values.username}
        onChange={update("username")}
        error={errors.username}
        autoComplete="username"
        autoFocus
        spellCheck={false}
        autoCapitalize="none"
        placeholder="admin"
        ltr
      />

      <TextField
        label="رمز عبور"
        name="password"
        type="password"
        value={values.password}
        onChange={update("password")}
        error={errors.password}
        autoComplete="current-password"
        placeholder="••••••••"
        revealable
        ltr
      />

      <Button type="submit" loading={submitting}>
        {submitting ? "در حال ورود…" : "ورود به پنل"}
      </Button>

      <p className="pt-1 text-center text-xs leading-6 text-ink-500">
        نام کاربری و رمز عبور با حروف انگلیسی وارد می‌شوند.
      </p>
    </form>
  );
}
