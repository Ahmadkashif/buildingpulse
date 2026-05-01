import type { Metadata } from "next";
import { Manrope, Inter } from "next/font/google";
import { QueryProvider } from "@/providers/query-provider";
import { MSWProvider } from "@/providers/msw-provider";
import { UnlockProvider } from "@/providers/unlock-provider";
import { AppShell } from "@/components/shell/app-shell";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "buildingPulse",
  description: "Energy forecasting for NYC buildings — buildingPulse.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${manrope.variable} h-full`}>
      <body className="min-h-full">
        <MSWProvider>
          <QueryProvider>
            <UnlockProvider>
              <AppShell>{children}</AppShell>
            </UnlockProvider>
          </QueryProvider>
        </MSWProvider>
      </body>
    </html>
  );
}
