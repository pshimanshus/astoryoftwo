import type { SessionState } from '../session/session';
import { displayPartnerName } from '../session/session';

export const INVITE_URL = 'https://astoryof.two/app';

export interface ShareMessage { text: string; inviteUrl: string; }

export function buildShareMessage(session: SessionState): ShareMessage {
  const creator = session.creatorName.trim() || 'someone who loves you';
  const partner = displayPartnerName(session);
  return {
    text: `${partner} — ${creator} made this for you. our story, drawn. ${INVITE_URL}`,
    inviteUrl: INVITE_URL,
  };
}

export type ShareTargetId =
  | 'whatsapp' | 'whatsapp-status' | 'instagram-story' | 'wallpaper-mobile' | 'wallpaper-desktop';

export interface ShareTarget { id: ShareTargetId; label: string; }

export const SHARE_TARGETS: ShareTarget[] = [
  { id: 'whatsapp', label: 'send on WhatsApp' },
  { id: 'whatsapp-status', label: 'WhatsApp status' },
  { id: 'instagram-story', label: 'Instagram story' },
  { id: 'wallpaper-mobile', label: 'set as phone wallpaper' },
  { id: 'wallpaper-desktop', label: 'desktop wallpaper' },
];

// Side-effecting: uses the Web Share API where available, else simulates.
export async function shareTo(target: ShareTarget, msg: ShareMessage): Promise<void> {
  if (target.id === 'whatsapp' && 'share' in navigator) {
    try { await navigator.share({ text: msg.text, url: msg.inviteUrl }); return; } catch { /* fall through */ }
  }
  // Prototype fallback: log the intended action.
  console.info(`[share] ${target.label}:`, msg.text);
}
