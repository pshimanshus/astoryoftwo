import { AnimatePresence, LayoutGroup, MotionConfig, motion } from 'framer-motion';
import './styles/tokens.css';
import './styles/global.css';
import './styles/screens.css';
import { screenSettle } from './styles/motion';
import { PhoneFrame } from './components/PhoneFrame';
import { PaperBackground } from './components/PaperBackground';
import { ProgressRule } from './components/ProgressRule';
import { FlowProvider, useFlow } from './flow/FlowProvider';
import { SessionProvider } from './session/SessionProvider';
import { LandingScreen } from './screens/LandingScreen';
import { HelloScreen } from './screens/HelloScreen';
import { PhotoSelectScreen } from './screens/PhotoSelectScreen';
import { PhotoReviewScreen } from './screens/PhotoReviewScreen';
import { RecordScreen } from './screens/RecordScreen';
import { PrintingScreen } from './screens/PrintingScreen';
import { RevealScreen } from './screens/RevealScreen';
import { RateScreen } from './screens/RateScreen';
import { SendScreen } from './screens/SendScreen';
import { CapReachedScreen } from './screens/CapReachedScreen';

function CurrentScreen() {
  const { step } = useFlow();
  return (
    <>
      {/* Persistent across the crossfade below — a sense of journey the old dead-centred
          screens gave none of. Reads step itself so it doesn't remount with each screen. */}
      <ProgressRule step={step} />
      <AnimatePresence mode="popLayout">
        <motion.div
          key={step}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={screenSettle}
          style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative', zIndex: 1, minHeight: 0 }}
        >
          {step === 'landing' && <LandingScreen />}
          {step === 'hello' && <HelloScreen />}
          {step === 'photos' && <PhotoSelectScreen />}
          {step === 'review' && <PhotoReviewScreen />}
          {step === 'record' && <RecordScreen />}
          {step === 'printing' && <PrintingScreen />}
          {step === 'reveal' && <RevealScreen />}
          {step === 'rate' && <RateScreen />}
          {step === 'send' && <SendScreen />}
          {step === 'cap-reached' && <CapReachedScreen />}
        </motion.div>
      </AnimatePresence>
    </>
  );
}

export default function App() {
  return (
    <SessionProvider>
      <FlowProvider>
        <PhoneFrame>
          {/* PaperBackground owns the persistent WebGL canvas — it mounts once, as a sibling of
              CurrentScreen's AnimatePresence, never inside it. See PaperBackground.tsx. */}
          <PaperBackground>
            <MotionConfig reducedMotion="user">
              <LayoutGroup>
                <CurrentScreen />
              </LayoutGroup>
            </MotionConfig>
          </PaperBackground>
        </PhoneFrame>
      </FlowProvider>
    </SessionProvider>
  );
}
