import {Composition} from 'remotion';
import {AnimatedPetals} from './AnimatedPetals';

export const Root = () => {
  return (
    <Composition
      id="PetalLoop"
      component={AnimatedPetals}
      durationInFrames={180}
      fps={30}
      width={1003}
      height={1568}
    />
  );
};
