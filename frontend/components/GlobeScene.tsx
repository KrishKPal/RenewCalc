"use client";
import { useState, type MouseEvent } from "react";
import { ArrowUpRight, SunMedium } from "lucide-react";

export default function GlobeScene() {
  const [position, setPosition] = useState({x: 0, y: 0});
  const motion = (event: MouseEvent<HTMLDivElement>) => {
    const box = event.currentTarget.getBoundingClientRect();
    setPosition({x: ((event.clientX - box.left) / box.width - .5) * 9, y: ((event.clientY - box.top) / box.height - .5) * -9});
  };
  return <div className="globe-scene" onMouseMove={motion} onMouseLeave={() => setPosition({x:0,y:0})}
     role="img" aria-label="Illustrated globe showing the Indian subcontinent and an orbiting solar satellite">
    <div className="globe-aura"/>
    <div className="globe-ring globe-ring-a"/><div className="globe-ring globe-ring-b"/>
    <div className="globe-body" style={{transform:`rotateX(${position.y}deg) rotateY(${position.x}deg)`}}>
      <svg viewBox="0 0 500 500" aria-hidden="true" className="globe-map"><defs>
        <clipPath id="sphere"><circle cx="250" cy="250" r="230"/></clipPath>
        <radialGradient id="ocean" cx="32%" cy="25%" r="83%"><stop stopColor="#287f89"/><stop offset=".49" stopColor="#145365"/><stop offset="1" stopColor="#082536"/></radialGradient>
        <linearGradient id="terrain" x1="0" x2="1" y1="0" y2="1"><stop stopColor="#b4e9a7"/><stop offset=".54" stopColor="#58b894"/><stop offset="1" stopColor="#247565"/></linearGradient>
        <radialGradient id="shine" cx="25%" cy="20%" r="83%"><stop stopColor="#d5fff1" stopOpacity=".35"/><stop offset=".45" stopColor="#bcf4d9" stopOpacity=".04"/><stop offset="1" stopColor="#001621" stopOpacity=".66"/></radialGradient>
      </defs>
      <g clipPath="url(#sphere)"><circle cx="250" cy="250" r="230" fill="url(#ocean)"/>
      <g fill="url(#terrain)" stroke="#8cdbb7" strokeWidth="1.5" opacity=".98">
        <path d="M26 120L88 92L105 53L154 38L195 72L220 104L206 137L159 153L137 180L97 183L73 226L43 215L16 175Z"/>
        <path d="M106 223L144 207L162 231L159 266L198 287L190 333L169 376L143 422L115 399L109 355L89 308L96 264Z"/>
        <path d="M215 90L259 72L299 76L327 59L377 86L437 96L480 133L475 196L447 232L400 228L367 251L339 233L322 265L292 244L278 208L250 216L219 190L181 185L183 145Z"/>
        <path d="M240 238L277 231L306 242L319 276L311 312L292 349L275 373L248 351L227 299L217 259Z"/>
        <path d="M328 270L345 287L353 311L371 341L389 336L382 366L356 375L340 352Z"/>
        <path d="M388 361L432 349L469 371L479 401L455 432L413 434L390 414L365 397Z"/>
        <path d="M311 391L318 403L311 414L306 403Z"/>
      </g>
      <g fill="none" stroke="#d0fff1" opacity=".15" strokeWidth="1.5"><ellipse cx="250" cy="250" rx="120" ry="230"/><ellipse cx="250" cy="250" rx="205" ry="230"/><path d="M19 250H481M45 157H455M45 343H455"/></g>
      <circle cx="250" cy="250" r="230" fill="url(#shine)"/>
      </g><circle cx="250" cy="250" r="230" fill="none" stroke="#b4ffdc" strokeOpacity=".5" strokeWidth="2"/>
      <circle cx="294" cy="281" r="9" fill="#e6ffb1"/><circle cx="294" cy="281" r="22" fill="none" stroke="#e6ffb1" strokeOpacity=".65" strokeWidth="2"/>
      </svg>
    </div>
    <div className="sun-marker"><SunMedium size={25}/></div>
    <div className="globe-info globe-info-top"><span>YOUR LOCATION</span><strong>Solar starts here</strong><ArrowUpRight size={17}/></div>
    <div className="globe-info globe-info-bottom"><span>ENERGY · COST · CLARITY</span><strong>Your space. Your scenario.</strong></div>
    <div className="globe-ground"/>
  </div>;
}
