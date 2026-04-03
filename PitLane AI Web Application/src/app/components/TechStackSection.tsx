import { Cpu, Database, Sparkles, Shield } from 'lucide-react';

export function TechStackSection() {
  const techItems = [
    {
      icon: Sparkles,
      title: 'Twelve Labs API',
      description: 'State-of-the-art multimodal AI for video understanding and temporal analysis.',
      tag: 'Video Intelligence',
    },
    {
      icon: Database,
      title: 'Voxel51 / FiftyOne',
      description: 'Advanced computer vision dataset management and model evaluation framework.',
      tag: 'CV Pipeline',
    },
    {
      icon: Cpu,
      title: 'Multi-Agent Architecture',
      description: 'Four specialized AI operators working in parallel for comprehensive analysis.',
      tag: 'AI System',
    },
    {
      icon: Shield,
      title: 'Secure Processing',
      description: 'Your videos are processed securely and deleted after analysis. Zero data retention.',
      tag: 'Privacy First',
    },
  ];

  return (
    <section className="py-20 px-6" style={{ backgroundColor: 'var(--bg-surface)' }}>
      <div className="max-w-[1200px] mx-auto">
        {/* Section Header */}
        <div className="text-center mb-16">
          <div className="text-xs font-semibold tracking-wider mb-4" style={{ color: 'var(--text-muted)' }}>
            TECHNOLOGY
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Built on <span style={{ color: 'var(--accent-green)' }}>cutting-edge</span> AI infrastructure
          </h2>
          <p className="text-lg max-w-[600px] mx-auto" style={{ color: 'var(--text-secondary)' }}>
            Powered by best-in-class tools from Twelve Labs and Voxel51, developed at the Voxel51 Hackathon 2026.
          </p>
        </div>

        {/* Tech Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {techItems.map((item, index) => (
            <div
              key={index}
              className="p-6 rounded-xl border group hover:border-[var(--accent-green)] transition-all duration-300"
              style={{
                backgroundColor: 'var(--bg-card)',
                borderColor: 'var(--border-subtle)',
              }}
            >
              <div className="flex items-start gap-4">
                {/* Icon */}
                <div
                  className="w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: 'var(--accent-green-glow)' }}
                >
                  <item.icon size={24} strokeWidth={1.5} style={{ color: 'var(--accent-green)' }} />
                </div>

                {/* Content */}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-lg font-bold text-white">{item.title}</h3>
                    <span
                      className="text-xs px-2 py-1 rounded"
                      style={{
                        backgroundColor: 'var(--bg-surface)',
                        color: 'var(--text-muted)',
                      }}
                    >
                      {item.tag}
                    </span>
                  </div>
                  <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                    {item.description}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
