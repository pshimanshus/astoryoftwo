import { useEffect, useRef, useState } from 'react';
import { copy } from '../content/copy';
import { MicButton } from '../components/MicButton';
import { useFlow } from '../flow/FlowProvider';
import { useSession } from '../session/SessionProvider';

export function RecordScreen() {
  const { advance } = useFlow();
  const { update } = useSession();
  const [recording, setRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState(false);
  const recRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const startedRef = useRef(0);

  useEffect(() => {
    if (!recording) return;
    const t = setInterval(() => setSeconds(Math.floor((Date.now() - startedRef.current) / 1000)), 250);
    return () => clearInterval(t);
  }, [recording]);

  const start = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const rec = new MediaRecorder(stream);
      chunksRef.current = [];
      rec.ondataavailable = (e) => chunksRef.current.push(e.data);
      rec.onstop = () => {
        const url = URL.createObjectURL(new Blob(chunksRef.current, { type: 'audio/webm' }));
        update({ recordingUrl: url, recordingDurationSec: seconds });
        stream.getTracks().forEach((tk) => tk.stop());
        advance();
      };
      recRef.current = rec;
      startedRef.current = Date.now();
      setSeconds(0);
      rec.start();
      setRecording(true);
    } catch {
      setError(true);
    }
  };

  const stop = () => { recRef.current?.stop(); setRecording(false); };
  const skip = () => { update({ recordingUrl: 'simulated', recordingDurationSec: 0 }); advance(); };

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 22, padding: 28, textAlign: 'center' }}>
      <p style={{ fontSize: 18, color: 'var(--ink-soft)' }}>{copy.record.prompt}</p>
      {recording && <p style={{ fontFamily: 'var(--font-hand)', fontSize: 28 }}>{seconds}s</p>}
      <MicButton recording={recording} onToggle={recording ? stop : start} />
      {recording && <button onClick={stop} style={{ color: 'var(--accent)' }}>{copy.record.stop}</button>}
      {error && <button onClick={skip} style={{ color: 'var(--ink-soft)', textDecoration: 'underline' }}>skip — we’ll imagine it</button>}
    </div>
  );
}
