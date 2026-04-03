import { useState, useEffect } from 'react';
import { ArrowLeft, ChevronDown } from 'lucide-react';

const API = 'http://localhost:8000';

type Video = { id: string; filename: string };

function ResultPanel({ markdown }: { markdown: string }) {
  // Very simple markdown renderer for tables + headers
  const lines = markdown.split('\n');
  return (
    <div className="rounded-xl p-6 text-sm leading-relaxed overflow-auto" style={{ backgroundColor: 'var(--bg-card)', color: 'var(--text-primary)', maxHeight: '60vh' }}>
      {lines.map((line, i) => {
        if (line.startsWith('## ')) return <h2 key={i} className="text-xl font-bold mb-4 mt-2">{line.slice(3)}</h2>;
        if (line.startsWith('### ')) return <h3 key={i} className="text-base font-semibold mt-5 mb-2" style={{ color: 'var(--accent-green)' }}>{line.slice(4)}</h3>;
        if (line.startsWith('| ---') || line.startsWith('|----') || line.startsWith('|------')) return null;
        if (line.startsWith('|')) {
          const cells = line.split('|').filter(c => c.trim());
          return (
            <div key={i} className="grid gap-2 py-1 border-b" style={{ gridTemplateColumns: `repeat(${cells.length}, 1fr)`, borderColor: 'rgba(255,255,255,0.08)' }}>
              {cells.map((c, j) => <span key={j} className="px-1 text-xs" style={{ color: j === 0 ? 'var(--accent-green)' : 'var(--text-secondary)' }}>{c.trim()}</span>)}
            </div>
          );
        }
        if (line.startsWith('**') && line.endsWith('**')) return <p key={i} className="font-semibold mt-4">{line.slice(2, -2)}</p>;
        if (line.trim() === '') return <div key={i} className="h-2" />;
        if (line.startsWith('_') && line.endsWith('_')) return <p key={i} className="italic" style={{ color: 'var(--text-secondary)' }}>{line.slice(1, -1)}</p>;
        return <p key={i} style={{ color: 'var(--text-secondary)' }}>{line}</p>;
      })}
    </div>
  );
}

export function AnalyzePage({ onBack }: { onBack: () => void }) {
  const [videos, setVideos] = useState<Video[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');
  const [activeOp, setActiveOp] = useState('');
  const [errorTypes, setErrorTypes] = useState('all driving errors');
  const [question, setQuestion] = useState('');
  const [fetchError, setFetchError] = useState('');

  useEffect(() => {
    fetch(`${API}/videos`)
      .then(r => r.json())
      .then(d => {
        setVideos(d.videos || []);
        if (d.videos?.length) setSelectedVideo(d.videos[0].id);
      })
      .catch(() => setFetchError('Could not reach backend. Make sure uvicorn is running on port 8000.'));
  }, []);

  async function run(op: string) {
    if (!selectedVideo) return;
    setActiveOp(op);
    setLoading(true);
    setResult('');
    try {
      let res;
      if (op === 'errors') {
        res = await fetch(`${API}/analyze/errors`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ video_id: selectedVideo, error_types: errorTypes }),
        });
      } else if (op === 'moments') {
        res = await fetch(`${API}/analyze/best-moments`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ video_id: selectedVideo }),
        });
      } else {
        res = await fetch(`${API}/analyze/ask`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ video_id: selectedVideo, question }),
        });
      }
      const data = await res.json();
      setResult(data.result || data.detail || 'No result returned.');
    } catch (e) {
      setResult('Error contacting backend. Is uvicorn running?');
    }
    setLoading(false);
  }

  const selectedFilename = videos.find(v => v.id === selectedVideo)?.filename || '';

  return (
    <div className="min-h-screen px-6 py-12" style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      <div className="max-w-3xl mx-auto">

        {/* Back */}
        <button onClick={onBack} className="flex items-center gap-2 mb-8 text-sm hover:opacity-80 transition-opacity" style={{ color: 'var(--text-secondary)' }}>
          <ArrowLeft size={16} /> Back to home
        </button>

        <h1 className="text-3xl font-bold mb-2">🏎️ Analyze Your Lap</h1>
        <p className="mb-8 text-sm" style={{ color: 'var(--text-secondary)' }}>
          Select a video, choose an operator, and get instant AI coaching.
        </p>

        {fetchError && (
          <div className="rounded-lg p-4 mb-6 text-sm" style={{ backgroundColor: 'rgba(255,60,60,0.1)', color: '#ff6b6b', border: '1px solid rgba(255,60,60,0.3)' }}>
            ⚠️ {fetchError}
          </div>
        )}

        {/* Video selector */}
        <div className="mb-6">
          <label className="block text-xs font-semibold mb-2 uppercase tracking-widest" style={{ color: 'var(--text-secondary)' }}>Select Video</label>
          <div className="relative">
            <select
              value={selectedVideo}
              onChange={e => setSelectedVideo(e.target.value)}
              className="w-full px-4 py-3 rounded-lg appearance-none text-sm font-medium pr-10"
              style={{ backgroundColor: 'var(--bg-card)', color: 'var(--text-primary)', border: '1px solid rgba(255,255,255,0.1)' }}
            >
              {videos.map(v => (
                <option key={v.id} value={v.id}>{v.filename}</option>
              ))}
            </select>
            <ChevronDown size={16} className="absolute right-3 top-3.5 pointer-events-none" style={{ color: 'var(--text-secondary)' }} />
          </div>
        </div>

        {/* Operators */}
        <div className="grid grid-cols-1 gap-4 mb-6">

          {/* Op 1 - Find Lap Errors */}
          <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div className="flex items-start justify-between gap-4 mb-3">
              <div>
                <h3 className="font-semibold text-base">🔴 Find Lap Errors</h3>
                <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>Detect every driving mistake with timestamps</p>
              </div>
              <button
                onClick={() => run('errors')}
                disabled={loading || !selectedVideo}
                className="px-4 py-2 rounded-lg text-sm font-semibold shrink-0 disabled:opacity-50 transition-all"
                style={{ backgroundColor: 'var(--accent-green)', color: '#000' }}
              >
                {loading && activeOp === 'errors' ? 'Analyzing...' : 'Run'}
              </button>
            </div>
            <input
              value={errorTypes}
              onChange={e => setErrorTypes(e.target.value)}
              placeholder="Error types (e.g. missed apex, late braking)"
              className="w-full px-3 py-2 rounded-lg text-xs"
              style={{ backgroundColor: 'rgba(255,255,255,0.05)', color: 'var(--text-primary)', border: '1px solid rgba(255,255,255,0.08)' }}
            />
          </div>

          {/* Op 2 - Find Best Moments */}
          <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="font-semibold text-base">🌟 Find Best Moments</h3>
                <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>Highlight top driving moments across 6 categories</p>
              </div>
              <button
                onClick={() => run('moments')}
                disabled={loading || !selectedVideo}
                className="px-4 py-2 rounded-lg text-sm font-semibold shrink-0 disabled:opacity-50 transition-all"
                style={{ backgroundColor: 'var(--accent-green)', color: '#000' }}
              >
                {loading && activeOp === 'moments' ? 'Searching...' : 'Run'}
              </button>
            </div>
          </div>

          {/* Op 3 - Ask About Lap */}
          <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div className="flex items-start justify-between gap-4 mb-3">
              <div>
                <h3 className="font-semibold text-base">💬 Ask About This Lap</h3>
                <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>Ask any question and get a timestamped answer</p>
              </div>
              <button
                onClick={() => run('ask')}
                disabled={loading || !selectedVideo || !question.trim()}
                className="px-4 py-2 rounded-lg text-sm font-semibold shrink-0 disabled:opacity-50 transition-all"
                style={{ backgroundColor: 'var(--accent-green)', color: '#000' }}
              >
                {loading && activeOp === 'ask' ? 'Asking...' : 'Ask'}
              </button>
            </div>
            <input
              value={question}
              onChange={e => setQuestion(e.target.value)}
              placeholder="e.g. Was my racing line through Turn 3 correct?"
              className="w-full px-3 py-2 rounded-lg text-xs"
              style={{ backgroundColor: 'rgba(255,255,255,0.05)', color: 'var(--text-primary)', border: '1px solid rgba(255,255,255,0.08)' }}
              onKeyDown={e => e.key === 'Enter' && run('ask')}
            />
          </div>
        </div>

        {/* Result */}
        {loading && (
          <div className="rounded-xl p-6 text-center text-sm" style={{ backgroundColor: 'var(--bg-card)', color: 'var(--text-secondary)' }}>
            <div className="animate-spin inline-block w-5 h-5 border-2 rounded-full mb-3" style={{ borderColor: 'var(--accent-green)', borderTopColor: 'transparent' }} />
            <p>AI is analyzing your lap...</p>
          </div>
        )}

        {result && !loading && <ResultPanel markdown={result} />}

      </div>
    </div>
  );
}
