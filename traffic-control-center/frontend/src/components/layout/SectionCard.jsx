import React from 'react';
import { motion } from 'framer-motion';
import { cardMotionVariants } from '../../theme/motion';

export function SectionCard({ title, icon: Icon, children, className = '', action }) {
  return (
    <motion.div
      variants={cardMotionVariants}
      initial="hidden"
      animate="visible"
      className={`glass-panel rounded-xl p-5 border border-slate-800/80 shadow-xl relative overflow-hidden ${className}`}
    >
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800/60">
        <div className="flex items-center space-x-2.5">
          {Icon && <Icon className="w-4 h-4 text-cyan-400" />}
          <h2 className="text-sm font-semibold tracking-wide text-slate-200 uppercase">
            {title}
          </h2>
        </div>
        {action}
      </div>
      {children}
    </motion.div>
  );
}
