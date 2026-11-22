
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Grama Sahayak",
  description:
    "Your trusted multilingual digital assistant for agriculture, healthcare, education, and government schemes.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

