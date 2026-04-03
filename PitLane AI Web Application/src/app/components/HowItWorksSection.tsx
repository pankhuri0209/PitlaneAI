import { Upload, Brain, Eye, FileText } from 'lucide-react';

export function HowItWorksSection() {
  const steps = [
    {
      icon: Upload,
      title: 'Upload Your Lap',
      description: 'Drop in any onboard video — GoPro, phone, track camera. MP4, MOV, AVI supported. Up to 4K resolution.',
    },
    {
      icon: Brain,
      title: 'AI Analyzes Everything',
      description: 'Four specialized AI operators scan your lap: error detection, highlight extraction, Q&A indexing, and coaching synthesis.',
    },
    {
      icon: Eye,
      title: 'Explore Your Results',
      description: 'See mistakes tagged on the timeline, watch your best moments, ask questions like "When did I brake too early?"',
    },
    {
      icon: FileText,
      title: 'Get Coaching Report',
      description: 'Download a full PDF with lap-by-lap breakdown, sector analysis, and prioritized improvement recommendations.',
    },
  ];

  return (
    <section id="how-it-works" className="py-20 px-6">
      <div className="max-w-[1200px] mx-auto">
        {/* Section Header */}
        <div className="text-center mb-16">
          <div className="text-xs font-semibold tracking-wider mb-4" style={{ color: 'var(--text-muted)' }}>
            HOW IT WORKS
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            From video to victory in <span style={{ color: 'var(--accent-green)' }}>four steps</span>
          </h2>
          <p className="text-lg max-w-[600px] mx-auto" style={{ color: 'var(--text-secondary)' }}>
            Our multi-agent AI system processes your race footage and delivers actionable insights in under a minute.
          </p>
        </div>

        {/* Steps Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {steps.map((step, index) => (
            <div
              key={index}
              className="p-8 rounded-xl border relative overflow-hidden group hover:border-[var(--accent-green)] transition-all duration-300"
              style={{
                backgroundColor: 'var(--bg-card)',
                borderColor: 'var(--border-subtle)',
              }}
            >
              {/* Step Number */}
              <div
                className="absolute top-4 right-4 text-6xl font-extrabold opacity-5"
                style={{ color: 'var(--accent-green)' }}
              >
                {index + 1}
              </div>

              {/* Icon */}
              <div
                className="w-12 h-12 rounded-lg flex items-center justify-center mb-4 group-hover:shadow-[var(--shadow-glow-green)] transition-shadow duration-300"
                style={{ backgroundColor: 'var(--accent-green-glow)' }}
              >
                <step.icon size={24} strokeWidth={1.5} style={{ color: 'var(--accent-green)' }} />
              </div>

              {/* Content */}
              <h3 className="text-xl font-bold text-white mb-3">{step.title}</h3>
              <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
