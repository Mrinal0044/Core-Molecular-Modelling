import React from 'react';
import { 
  Rocket, 
  Play, 
  Brain, 
  Cpu, 
  ShieldCheck, 
  TrendingUp, 
  Activity, 
  Network
} from 'lucide-react';

export default function LandingPage({ onExplore, onWatchDemo }) {
  return (
    <div 
      className="min-h-screen bg-[#030612] text-slate-100 font-sans selection:bg-cyan-500/30 relative overflow-hidden"
      style={{
        backgroundImage: `linear-gradient(rgba(3, 6, 18, 0.88), rgba(3, 6, 18, 0.94)), url('cyberpunk_bg2.jpg')`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: 'fixed',
      }}
    >
      
      {/* 1. Global Atmosphere & Background Elements */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        {/* Deep ambient glow */}
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-cyan-950/20 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] rounded-full bg-blue-950/25 blur-[150px]" />
        
        {/* Subtle, dark tech-grid effect near the bottom section */}
        <div className="absolute bottom-0 left-0 right-0 h-[35%] opacity-20 bg-[linear-gradient(rgba(6,182,212,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(6,182,212,0.05)_1px,transparent_1px)] bg-[size:32px_32px] [mask-image:linear-gradient(to_top,rgba(0,0,0,1),transparent)]" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Navigation & Header */}
        <header className="flex justify-between items-center py-6 border-b border-slate-800/40">
          <div className="flex items-center gap-3 cursor-pointer group">
            {/* Logo Container supporting transparent logo blending */}
            <div className="relative w-10 h-10 flex items-center justify-center bg-cyan-950/30 rounded-lg border border-cyan-500/20 shadow-[0_0_15px_rgba(6,182,212,0.15)] group-hover:border-cyan-400 group-hover:shadow-[0_0_20px_rgba(6,182,212,0.3)] transition-all duration-300">
              <img 
                src="/medxai-logo.png" 
                alt="MEDxAI Logo" 
                className="w-8 h-8 object-contain mix-blend-lighten"
                onError={(e) => { e.currentTarget.style.display = 'none'; }}
              />
              <div className="absolute inset-0 bg-cyan-500/10 rounded-lg blur-sm group-hover:bg-cyan-500/20 transition-all" />
            </div>
            <span className="font-sans font-bold text-xl tracking-tight text-slate-100 group-hover:text-cyan-400 transition-colors duration-300">
              Quantum PharmX<span className="text-xs text-cyan-400 align-super ml-0.5">™</span>
            </span>
          </div>

          <nav className="hidden md:flex items-center gap-8">
            {['Home', 'Features', 'About Us', 'Contact'].map((item, idx) => (
              <a 
                key={item} 
                href={`#${item.toLowerCase().replace(' ', '-')}`} 
                className={`text-sm font-semibold tracking-wide transition-all duration-300 relative py-1 hover:text-slate-100 ${
                  idx === 0 ? 'text-slate-100' : 'text-slate-400'
                }`}
              >
                {item}
                {idx === 0 && (
                  <span className="absolute bottom-0 left-0 w-full h-[2px] bg-cyan-400 shadow-[0_0_8px_#22d3ee] rounded-full" />
                )}
              </a>
            ))}
          </nav>

          <button 
            onClick={onExplore}
            className="text-xs sm:text-sm font-semibold text-cyan-400 border border-cyan-500/30 bg-cyan-950/20 hover:bg-cyan-400/10 hover:border-cyan-400 hover:shadow-[0_0_15px_rgba(6,182,212,0.2)] rounded-lg px-4 py-2 transition-all duration-300"
          >
            Request Demo
          </button>
        </header>

        {/* Hero Section */}
        <section className="grid grid-cols-1 gap-12 pt-16 pb-24 items-center">
          {/* Hero Content */}
          <div className="flex flex-col items-center text-center space-y-8 max-w-4xl mx-auto">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-none text-slate-100 font-sans">
              Revolutionizing <span className="bg-gradient-to-r from-cyan-400 to-blue-600 bg-clip-text text-transparent drop-shadow-[0_0_15px_rgba(6,182,212,0.15)]">Drug Discovery</span>
            </h1>
            <p className="text-base sm:text-lg text-slate-400 font-light leading-relaxed max-w-2xl">
              AI-driven molecular intelligence powered by quantum-enhanced simulations for faster, safer, and smarter pharmaceutical innovation.
            </p>

            <div className="flex flex-wrap justify-center gap-4 pt-2">
              {/* Primary Button */}
              <button 
                onClick={onExplore}
                className="flex items-center gap-2 px-6 py-3.5 bg-cyan-400 hover:bg-cyan-300 text-slate-950 font-bold rounded-xl shadow-[0_0_20px_rgba(34,211,238,0.3)] hover:shadow-[0_0_25px_rgba(34,211,238,0.5)] transition-all duration-300 hover:-translate-y-0.5"
              >
                <Rocket className="w-5 h-5 fill-current" />
                <span>Explore Platform</span>
              </button>

              {/* Secondary Button */}
              <button 
                onClick={onWatchDemo}
                className="flex items-center gap-2 px-6 py-3.5 border border-cyan-400/60 hover:border-cyan-400 bg-transparent hover:bg-cyan-400/10 text-cyan-400 font-bold rounded-xl transition-all duration-300 hover:-translate-y-0.5"
              >
                <Play className="w-5 h-5 fill-cyan-400/20" />
                <span>Watch Demo</span>
              </button>
            </div>
          </div>

        </section>

        {/* Crisp Monochromatic Outline Icons Bottom Bar */}
        <section className="border-t border-slate-800/40 py-12 grid grid-cols-2 md:grid-cols-5 gap-6">
          {[
            { label: 'AI-Driven Intelligence', desc: 'Smarter insights for better decisions', icon: Brain },
            { label: 'Quantum Computing', desc: 'Enhanced accuracy and speed', icon: Cpu },
            { label: 'Faster & Safer', desc: 'Reduce time, cost and risk', icon: ShieldCheck },
            { label: 'Precision Therapeutics', desc: 'Personalized solutions', icon: Network },
            { label: 'Data-Driven Results', desc: 'Actionable analytics', icon: TrendingUp },
          ].map(({ label, desc, icon: Icon }, idx) => (
            <div key={idx} className="flex flex-col items-center text-center p-4 rounded-xl hover:bg-white/5 transition-all duration-300 group">
              <div className="w-12 h-12 rounded-xl bg-cyan-950/20 border border-cyan-500/30 flex items-center justify-center mb-4 transition-all duration-300 group-hover:scale-110 shadow-[0_0_10px_rgba(6,182,212,0.1)] group-hover:shadow-[0_0_15px_rgba(6,182,212,0.3)]">
                <Icon className="w-6 h-6 text-cyan-400 drop-shadow-[0_0_4px_rgba(34,211,238,0.6)]" strokeWidth={1.5} />
              </div>
              <h4 className="text-sm font-bold text-slate-200 group-hover:text-cyan-400 transition-colors">{label}</h4>
              <p className="text-[11px] text-slate-400 mt-1 max-w-[150px] leading-tight">{desc}</p>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}
