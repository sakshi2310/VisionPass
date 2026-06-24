import type { ReactNode } from "react";

import "./globals.css";

export const metadata = {
  title: "VisionPass AI",
  description: "Centralized AI-powered attendance, visitor, and access intelligence.",
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
