import { useState } from 'react';
import { Navbar } from './components/Navbar';
import { HeroSection } from './components/HeroSection';
import { FeatureStrip } from './components/FeatureStrip';
import { FeaturesSection } from './components/FeaturesSection';
import { HowItWorksSection } from './components/HowItWorksSection';
import { PricingSection } from './components/PricingSection';
import { TechStackSection } from './components/TechStackSection';
import { CTASection } from './components/CTASection';
import { Footer } from './components/Footer';
import { AnalyzePage } from './components/AnalyzePage';

export default function App() {
  const [showAnalyze, setShowAnalyze] = useState(false);

  if (showAnalyze) {
    return <AnalyzePage onBack={() => setShowAnalyze(false)} />;
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <Navbar />
      <main>
        <HeroSection onAnalyzeClick={() => setShowAnalyze(true)} />
        <FeatureStrip />
        <FeaturesSection />
        <HowItWorksSection />
        <TechStackSection />
        <PricingSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}
