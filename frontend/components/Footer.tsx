import Link from "next/link";
import { Github, Mail, Leaf, ArrowUpRight } from "lucide-react";

export default function Footer() {
  return <footer className="footer"><div className="container footer-revamp">
    <div className="footer-main"><Link href="/" className="footer-brand"><Leaf size={24}/> Renew<span>Calc</span></Link><p>Better decisions start with better energy estimates.</p><small>Made to help you explore solar possibilities, from rooftops to businesses.</small></div>
    <div className="footer-connect"><h3>Explore</h3><Link href="/">Home</Link><Link href="/assess">Solar calculator</Link><Link href="/#how-it-works">How it works</Link></div>
    <div className="footer-connect"><h3>Contact</h3><a href="mailto:vordelx01@gmail.com"><Mail size={16}/> vordelx01@gmail.com</a><a href="https://github.com/KrishKPal" target="_blank" rel="noopener noreferrer"><Github size={16}/> github.com/KrishKPal <ArrowUpRight size={14}/></a></div>
    <div className="footer-bottom"><span>© {new Date().getFullYear()} RenewCalc</span><span>Solar projections are estimates, not installation or financial advice. Weather: Open-Meteo ERA5.</span></div>
  </div></footer>;
}
