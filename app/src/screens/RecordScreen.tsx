import { useEffect, useRef, useState } from 'react';
import { copy } from '../content/copy';
import { MicButton } from '../components/MicButton';
import { useFlow } from '../flow/FlowProvider';
import { useSession } from '../session/SessionProvider';
import { computeRms, setMicActive, setMicLevel } from '../webgl/micLevel';

export function RecordScreen() {
  const { advance } = useFlow();
  const { update } = useSession();
  const [recording, setRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState(false);
  const recRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const startedRef = useRef(0);
  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    if (!recording) return;
    const t = setInterval(() => setSeconds(Math.floor((Date.now() - startedRef.current) / 1000)), 250);
    return () => clearInterval(t);
  }, [recording]);

  // Drives the WebGL ink sheet's seed-splat — reads the mic in real time and writes an RMS level
  // into the module-level micLevel store (see webgl/micLevel.ts). Not React state: this runs at
  // animation-frame rate, and nothing outside the 3D layer needs the instantaneous value.
  const pumpMicLevel = () => {
    const analyser = analyserRef.current;
    if (!analyser) return;
    const bytes = new Uint8Array(analyser.fftSize);
    const tick = () => {
      if (!analyserRef.current) return;
      analyserRef.current.getByteTimeDomainData(bytes);
      setMicLevel(computeRms(bytes));
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
  };

  const teardownAudio = () => {
    if (rafRef.current !== null) { cancelAnimationFrame(rafRef.current); rafRef.current = null; }
    analyserRef.current = null;
    audioCtxRef.current?.close();
    audioCtxRef.current = null;
    setMicActive(false);
  };

  const start = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const rec = new MediaRecorder(stream);
      chunksRef.current = [];
      rec.ondataavailable = (e) => chunksRef.current.push(e.data);
      rec.onstop = () => {
        const url = URL.createObjectURL(new Blob(chunksRef.current, { type: 'audio/webm' }));
        update({ recordingUrl: url, recordingDurationSec: seconds });
        stream.getTracks().forEach((tk) => tk.stop());
        streamRef.current = null;
        teardownAudio();
        advance();
      };
      recRef.current = rec;
      startedRef.current = Date.now();
      setSeconds(0);
      rec.start();
      setRecording(true);

      const audioCtx = new AudioContext();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      audioCtxRef.current = audioCtx;
      analyserRef.current = analyser;
      setMicActive(true);
      pumpMicLevel();
    } catch {
      setError(true);
    }
  };

  const stop = () => { recRef.current?.stop(); setRecording(false); };
  const skip = () => { update({ recordingUrl: 'simulated', recordingDurationSec: 0 }); advance(); };

  useEffect(() => teardownAudio, []); // safety net if the screen unmounts mid-recording

  // Centred is deliberate here, not a default: the ink bloom InkSheet renders is seeded at the
  // canvas centre, and MicButton has to sit exactly where the ink is forming — the one screen
  // where the ledger-margin composition steps aside for the mechanic underneath it.
  return (
    <div className="sheet sheet--plain" style={{ alignItems: 'center', justifyContent: 'center', gap: 'var(--space-6)', padding: 28, textAlign: 'center' }}>
      <span className="sheet__spine">05 — say it</span>
      <p className="lede" style={{ maxWidth: 240, fontSize: 'var(--text-title)', color: 'var(--ink-soft)', lineHeight: 1.3 }}>{copy.record.prompt}</p>
      {recording && <p className="headline headline--hand" style={{ margin: 0, fontSize: 'var(--text-hand-lg)' }}>{seconds}s</p>}
      <MicButton recording={recording} onToggle={recording ? stop : start} />
      {recording && <button onClick={stop} className="stamp stamp--ghost" style={{ borderColor: 'var(--accent)', color: 'var(--accent)' }}>{copy.record.stop}</button>}
      {error && <button onClick={skip} className="kicker" style={{ textDecoration: 'underline' }}>skip — we’ll imagine it</button>}
    </div>
  );
}
