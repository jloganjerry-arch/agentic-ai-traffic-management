export const cardMotionVariants = {
  hidden: { opacity: 0, y: 14, scale: 0.99 },
  visible: { 
    opacity: 1, 
    y: 0, 
    scale: 1,
    transition: { 
      duration: 0.35, 
      ease: [0.16, 1, 0.3, 1] 
    } 
  },
};

export const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.06,
      delayChildren: 0.02,
    },
  },
};

export const workspaceTransitionVariants = {
  initial: { opacity: 0, y: 12, scale: 0.995 },
  animate: { 
    opacity: 1, 
    y: 0, 
    scale: 1,
    transition: { 
      duration: 0.3, 
      ease: [0.16, 1, 0.3, 1] 
    } 
  },
  exit: { 
    opacity: 0, 
    y: -8, 
    scale: 0.995,
    transition: { duration: 0.15 } 
  },
};

export const pulseAnimation = {
  animate: {
    scale: [1, 1.08, 1],
    opacity: [0.75, 1, 0.75],
  },
  transition: {
    duration: 2.2,
    repeat: Infinity,
    ease: 'easeInOut',
  },
};

export const smoothHeightTransition = {
  initial: { height: 0, opacity: 0 },
  animate: { height: 'auto', opacity: 1 },
  exit: { height: 0, opacity: 0 },
  transition: { duration: 0.25, ease: 'easeInOut' },
};

export const interactiveHover = {
  whileHover: { 
    y: -2,
    transition: { duration: 0.2, ease: 'easeOut' }
  },
  whileTap: { 
    scale: 0.98,
    transition: { duration: 0.1 }
  }
};
