import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "DRISHTI — Crowd Density Monitoring Dashboard",
  description:
    "Real-time crowd counting and alert system using YOLO-CROWD and CSRNet models. Monitor crowd density and receive emergency notifications when thresholds are exceeded.",
  keywords: ["crowd counting", "density estimation", "surveillance", "YOLO", "CSRNet", "real-time monitoring"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased`}>
        <Sidebar />
        <main className="ml-[72px] min-h-screen">
          {children}
        </main>
      </body>
    </html>
  );
}
