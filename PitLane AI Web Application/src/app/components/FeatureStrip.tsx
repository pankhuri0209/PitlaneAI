import { Video, Zap, Car, MessageSquare } from 'lucide-react';

export function FeatureStrip() {
  const features = [
    {
      icon: Video,
      stat: '4 AI Operators',
      description: 'Find errors, highlights, ask anything, coaching report',
    },
    {
      icon: Zap,
      stat: '< 30 seconds',
      description: 'Full lap analysis from upload to insights',
    },
    {
      icon: Car,
      stat: '$1.82B Market',
      description: 'Zero AI coaching tools exist in karting today',
    },
    {
      icon: MessageSquare,
      stat: 'Plain English',
      description: 'No telemetry expertise needed to understand results',
    },
  ];

  return (
    <section
      className="border-t border-b py-8"
      style={{
        backgroundColor: 'var(--bg-surface)',
        borderColor: 'var(--border-subtle)',
      }}
    >
      <div className="max-w-[1400px] mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="flex flex-col items-center text-center gap-2">
              <feature.icon size={20} strokeWidth={1.5} style={{ color: 'var(--accent-green)' }} />
              <div className="text-2xl font-bold text-white">{feature.stat}</div>
              <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                {feature.description}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
