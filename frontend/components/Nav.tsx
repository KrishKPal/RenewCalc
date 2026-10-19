"use client";
import Link from "next/link";
import { ArrowUpRight, Leaf, Menu, X } from "lucide-react";
import { usePathname } from "next/navigation";
import { useState } from "react";

export default function Nav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  return <header className="site-header"><div className="container header-inner">
    <Link href="/" className="wordmark" onClick={() => setOpen(false)}><span className="logo-icon"><Leaf size={21}/></span><span>Renew<span className="brand-accent">Calc</span></span></Link>
    <nav aria-label="Main navigation" className={`header-links ${open ? "nav-open" : ""}`}>
      <Link href="/" onClick={() => setOpen(false)} className={pathname === "/" ? "active" : ""}>Home</Link>
      <Link href="/assess" onClick={() => setOpen(false)} className={pathname.startsWith("/assess") ? "active" : ""}>Solar calculator</Link>
      <Link href="/#how-it-works" onClick={() => setOpen(false)}>How it works</Link>
      <a href="mailto:vordelx01@gmail.com" onClick={() => setOpen(false)}>Contact</a>
    </nav>
    <div className="header-actions"><Link href="/assess" className="button button-small button-dark">Get an estimate <ArrowUpRight size={16}/></Link>
      <button type="button" className="menu-toggle" aria-label={open ? "Close navigation" : "Open navigation"} aria-expanded={open} onClick={() => setOpen(!open)}>{open ? <X/> : <Menu/>}</button>
    </div>
  </div></header>;
}
