import { ArrowRight, Rocket } from 'lucide-react';

export function CTASection() {
  return (
    <section className="py-20 px-6">
      <div className="max-w-[900px] mx-auto">
        <div
          className="p-12 rounded-2xl border text-center relative overflow-hidden"
          style={{
            backgroundColor: 'var(--bg-card)',
            borderColor: 'var(--border-subtle)',
          }}
        >
          {/* Background Glow Effect */}
          <div
            className="absolute inset-0 opacity-10"
            style={{
              background: 'radial-gradient(circle at 50% 50%, var(--accent-green) 0%, transparent 70%)',
            }}
          ></div>

          {/* Content */}
          <div className="relative z-10">
            <div
              className="inline-flex items-center justify-center w-16 h-16 rounded-full mb-6"
              style={{
                backgroundColor: 'var(--accent-green-glow)',
              }}
            >
              <Rocket size={32} strokeWidth={1.5} style={{ color: 'var(--accent-green)' }} />
            </div>

            <h2 className="text-4xl md:text-5xl font-extrabold text-white mb-4">
              Ready to go faster?
            </h2>
            <p className="text-lg mb-8 max-w-[600px] mx-auto" style={{ color: 'var(--text-secondary)' }}>
              Join hundreds of drivers using AI to improve their lap times. Upload your first video and get instant
              coaching — free, no credit card required.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                className="flex items-center gap-2 px-8 py-4 rounded-lg text-black font-semibold text-lg transition-all hover:scale-105"
                style={{
                  backgroundColor: 'var(--accent-green)',
                  boxShadow: 'var(--shadow-glow-green)',
                }}
              >
                <span>Get Started Free</span>
                <ArrowRight size={20} strokeWidth={2.5} />
              </button>
              <button
                className="px-8 py-4 rounded-lg font-semibold text-lg transition-colors border"
                style={{
                  borderColor: 'var(--border-active)',
                  color: 'var(--text-primary)',
                }}
              >
                Book a Demo
              </button>
            </div>

            <div className="mt-8 flex items-center justify-center gap-6 text-sm" style={{ color: 'var(--text-muted)' }}>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[var(--accent-green)]"></div>
                <span>Free 3-lap trial</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[var(--accent-green)]"></div>
                <span>No credit card</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[var(--accent-green)]"></div>
                <span>30-second setup</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
