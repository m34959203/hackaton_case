import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Providers from "@/app/providers";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin", "cyrillic"],
});

export const metadata: Metadata = {
  title: "ZanAlytics — AI-анализ законодательства РК",
  description:
    "AI-система выявления противоречий, дублирований и устаревших норм в законодательстве Республики Казахстан. Проект для Decentrathon 5.0.",
  icons: {
    icon: "/favicon.svg",
  },
  openGraph: {
    title: "ZanAlytics — AI-анализ законодательства РК",
    description:
      "Выявление противоречий, дублирований и устаревших норм в НПА Казахстана с помощью искусственного интеллекта",
    type: "website",
    locale: "ru_RU",
  },
  keywords: [
    "законодательство",
    "Казахстан",
    "AI",
    "анализ",
    "противоречия",
    "дублирование",
    "НПА",
    "ZanAlytics",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" className={`${inter.variable} dark h-full antialiased`}>
      <body className="flex h-full min-h-screen bg-background text-foreground font-sans">
        <Providers>
          <Sidebar />
          <div className="flex flex-1 flex-col overflow-hidden">
            <Header />
            <main className="flex-1 overflow-y-auto p-6">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
