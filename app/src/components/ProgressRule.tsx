import { motion } from 'framer-motion';
import { ORDER, type Step } from '../flow/steps';
import { screenSettle } from '../styles/motion';

// A ruled line at the top of the sheet, crossing the vertical margin rule (see screens.css's
// .sheet::before) — together they read as a ledger page, not app progress chrome.
export function ProgressRule({ step }: { step: Step | 'cap-reached' }) {
  if (step === 'cap-reached') return null;
  const index = ORDER.indexOf(step);
  if (index < 0) return null;
  const progress = index / (ORDER.length - 1);

  return (
    <div className="progress" aria-hidden>
      <motion.div className="progress__fill" initial={false}
        animate={{ width: `${progress * 100}%` }} transition={screenSettle} />
      <div className="progress__ticks">
        {ORDER.map((s, i) => (
          <span key={s} className={`progress__tick${i <= index ? ' progress__tick--done' : ''}`} />
        ))}
      </div>
    </div>
  );
}
