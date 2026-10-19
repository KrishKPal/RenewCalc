import Link from "next/link";
import { ArrowRight, ArrowUpRight, BatteryCharging, ChartNoAxesCombined, Check, CircleDollarSign, Leaf, MapPin, MoveUpRight, Sun, Zap } from "lucide-react";
import GlobeScene from "@/components/GlobeScene";

const reasons = [
  {icon: MapPin, number:"01", title:"Start with your location", text:"Choose a place in India. We bring regional solar resource data into your assessment."},
  {icon: Sun, number:"02", title:"Make the roof count", text:"Explore panel capacity, orientation and how much usable space you really have."},
  {icon: CircleDollarSign, number:"03", title:"See the money side", text:"Compare electricity use, estimated bill savings and long-term payback using your inputs."},
];
export default function Home() {
  return <>
    <section className="rc-hero"><div className="container rc-hero-inner">
      <div className="rc-hero-content"><div className="rc-overline"><span className="live-indicator"/> SMARTER SOLAR, STARTING HERE</div>
        <h1>Your space.<br/>Your sunlight.<br/><em>Real potential.</em></h1>
        <p>Thinking about going solar? RenewCalc helps you explore what your location and rooftop could generate—and whether the numbers work for you.</p>
        <div className="hero-actions"><Link href="/assess" className="button button-primary">Calculate my solar potential <ArrowRight size={19}/></Link><a href="#how-it-works" className="hero-text-link">See how it works <MoveUpRight size={17}/></a></div>
        <div className="rc-hero-proof"><span><Check size={16}/> No signup</span><span><Check size={16}/> Location based</span><span><Check size={16}/> Your numbers, your estimate</span></div>
      </div>
      <GlobeScene/>
    </div><div className="rc-hero-micro">DISCOVER MORE <span>↓</span></div></section>
    <section className="rc-benefits"><div className="container rc-benefits-grid">
      <div><Sun/><strong>Understand production</strong><span>How much sunlight becomes energy</span></div>
      <div><Zap/><strong>Estimate bill impact</strong><span>How solar changes grid electricity use</span></div>
      <div><ChartNoAxesCombined/><strong>Compare configurations</strong><span>See why system size matters</span></div>
      <div><BatteryCharging/><strong>Plan with confidence</strong><span>View annual and lifetime estimates</span></div>
    </div></section>
    <section id="how-it-works" className="rc-section rc-how"><div className="container">
      <div className="rc-section-top"><div><p className="rc-section-label">IT STARTS WITH ONE PLACE</p><h2>From an address to<br/><em>a clearer decision.</em></h2></div><p>There isn't a one-size-fits-all answer to solar. We'll walk through your site, energy needs and budget to build a scenario you can actually explore.</p></div>
      <div className="rc-steps">{reasons.map(({icon:Icon,number,title,text})=><article className="rc-step-card" key={number}><div className="rc-step-top"><div className="rc-step-icon"><Icon size={26}/></div><span>{number}</span></div><h3>{title}</h3><p>{text}</p></article>)}</div>
    </div></section>
    <section className="rc-section rc-outro"><div className="container rc-outro-grid"><div className="rc-outro-symbol"><Leaf size={112} strokeWidth={1}/><div className="rc-pulse rc-pulse-one"/><div className="rc-pulse rc-pulse-two"/></div><div><p className="rc-section-label">MADE FOR REAL DECISIONS</p><h2>Solar looks good.<br/><em>Make sure the numbers do, too.</em></h2><p>Get a location-aware estimate, explore a different panel layout or change your budget. Your scenario updates with the choices you make.</p><Link href="/assess" className="button button-primary">Explore your options <ArrowUpRight size={18}/></Link></div></div>
    <div className="container"><p className="rc-trust-note">Estimates use historical regional weather and editable tariff assumptions. Not a structural assessment, utility quote, or guaranteed return. Weather data: Open-Meteo ERA5.</p></div></section>
  </>;
}
