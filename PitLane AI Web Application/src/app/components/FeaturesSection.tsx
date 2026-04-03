import { AlertTriangle, Trophy, Search, FileBarChart } from 'lucide-react';

export function FeaturesSection() {
  const features = [
    {
      icon: AlertTriangle,
      title: 'Error Detection',
      description: 'AI identifies late braking, wide exits, apex mistakes, and more — automatically tagged on your timeline.',
      color: 'var(--accent-red)',
      colorDim: 'var(--accent-red-dim)',
      glow: 'var(--shadow-glow-red)',
    },
    {
      icon: Trophy,
      title: 'Highlight Extraction',
      description: 'Perfect apex clips, overtakes, fastest sectors — auto-saved and ready to share on social media.',
      color: 'var(--accent-green)',
      colorDim: 'var(--accent-green-glow)',
      glow: 'var(--shadow-glow-green)',
    },
    {
      icon: Search,
      title: 'Natural Language Q&A',
      description: 'Ask anything: "Where was my best sector?" "When did I brake early?" AI searches your video and answers instantly.',
      color: 'var(--accent-blue)',
      colorDim: 'rgba(77, 158, 255, 0.15)',
      glow: '0 0 24px rgba(77, 158, 255, 0.2)',
    },
    {
      icon: FileBarChart,
      title: 'Coaching Reports',
      description: 'Full PDF breakdown with lap times, sector analysis, error frequency, and improvement priorities.',
      color: 'var(--accent-purple)',
      colorDim: 'rgba(168, 85, 247, 0.15)',
      glow: '0 0 24px rgba(168, 85, 247, 0.2)',
    },
  ];

  return (
    <section id="features" className="py-20 px-6" style={{ backgroundColor: 'var(--bg-surface)' }}>
      <div className="max-w-[1200px] mx-auto">
        {/* Section Header */}
        <div className="text-center mb-16">
          <div className="text-xs font-semibold tracking-wider mb-4" style={{ color: 'var(--text-muted)' }}>
            FEATURES
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Four AI operators.<br />One complete <span style={{ color: 'var(--accent-green)' }}>coaching system.</span>
          </h2>
          <p className="text-lg max-w-[600px] mx-auto" style={{ color: 'var(--text-secondary)' }}>
            Each specialized AI agent focuses on a different aspect of your performance, working together to give you the complete picture.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {features.map((feature, index) => (
            <div
              key={index}
              className="p-8 rounded-xl border group hover:border-opacity-50 transition-all duration-300"
              style={{
                backgroundColor: 'var(--bg-card)',
                borderColor: 'var(--border-subtle)',
              }}
            >
              {/* Icon */}
              <div
                className="w-14 h-14 rounded-lg flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300"
                style={{
                  backgroundColor: feature.colorDim,
                }}
              >
                <feature.icon size={28} strokeWidth={1.5} style={{ color: feature.color }} />
              </div>

              {/* Content */}
              <h3 className="text-2xl font-bold text-white mb-3">{feature.title}</h3>
              <p className="text-base leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                {feature.description}
              </p>

              {/* Visual Element */}
              <div className="mt-6 h-2 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--bg-surface)' }}>
                <div
                  className="h-full transition-all duration-500 group-hover:w-full"
                  style={{
                    backgroundColor: feature.color,
                    width: '60%',
                  }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
