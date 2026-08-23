// All user-facing brand-voice strings live here so they can be tuned in one place.
export const copy = {
  landing: {
    cta: 'say your story, get it illustrated',
    disclaimer:
      'We may post your story on A Story of Two. If it’s unique and our agent loves it, you’ll get your illustrated carousel. Max 3 per person.',
  },
  hello: {
    prompt: 'Are you here with your special one — or sending them something from afar?',
    together: 'We’re together',
    sending: 'I’m sending them something',
    yourName: 'your name',
    theirName: 'their name',
    continue: 'begin',
  },
  photos: { title: 'choose your photos', hint: 'pick the moments that are you two', done: 'these are us' },
  review: { mic: 'record your story — we draw from your voice' },
  record: { prompt: 'tell us about you two. take your time.', stop: 'that’s our story' },
  printing: {
    greet: (name: string) => `${name}, while your story prints — let me tell you ours.`,
    askOnce: 'no pressure — follow only if this already feels like you.',
    follow: 'follow A Story of Two',
  },
  reveal: { title: 'your story, drawn' },
  rate: { prompt: 'did this feel like you?' },
  send: {
    primary: (name: string) => `send it to ${name}`,
    note: 'no downloads — this is meant to be given, not saved.',
  },
  cap: { title: 'you’ve made your three.', body: 'three stories is all we draw per heart. thank you for trusting us with them.' },
} as const;
