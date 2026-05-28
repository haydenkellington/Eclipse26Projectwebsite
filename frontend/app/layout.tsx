import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pitch Sequencing Run Value Recommender",
  description: "Baseball pitch sequencing dashboard powered by Q-values, model sequence dRE, and empirical dRE.",
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
