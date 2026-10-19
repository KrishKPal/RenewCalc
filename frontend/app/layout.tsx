import type { Metadata } from "next";
import "./globals.css";
import "leaflet/dist/leaflet.css";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "RenewCalc | Solar made practical",
  description: "Plan a solar installation, explore production and estimate savings for your location in India.",
};

export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><body><Nav/><main>{children}</main><Footer/></body></html>;
}
