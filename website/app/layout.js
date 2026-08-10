import "./globals.css";

export const metadata = {
  title: "کلینیک دندان‌پزشکی فرهاد باقری طاهری | خدمات جامع دندان‌پزشکی در تهران",
  description:
    "ارائه خدمات دندان‌پزشکی شامل معاینه، جرم‌گیری، ترمیم، عصب‌کشی، ایمپلنت، ارتودنسی و طراحی لبخند. رزرو نوبت آنلاین و پذیرش بیمه‌های اصلی.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="fa" dir="rtl">
      <head>
        {/* Vazirmatn via Google Fonts CDN */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;700;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-sans">{children}</body>
    </html>
  );
}
