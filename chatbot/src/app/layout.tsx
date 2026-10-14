import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sunset Kuakata - AI Sales Operations & RAG Assistant",
  description:
    "Production-grade Retrieval-Augmented Generation (RAG) assistant for Sunset Kuakata Hotel & Resort Ltd. operations, pricing models, and executive metrics.",
  keywords: [
    "Sunset Kuakata",
    "Hotel Share",
    "RAG Chatbot",
    "Groq LLM",
    "Sales Operations",
    "Lead Qualification",
    "Real Estate Bangladesh",
  ],
  authors: [{ name: "Sunset Kuakata Operations Team" }],
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#090d16",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
