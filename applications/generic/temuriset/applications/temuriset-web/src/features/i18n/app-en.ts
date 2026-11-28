/**
 * English for the signed-in app, merged from per-area dictionaries so Track A and Track B never collide (spec 055).
 * Keyed by the Indonesian source text that `t()` receives; placeholders stay identical in both languages.
 */
import { CORE_EN } from './app-en/core';
import { FINDER_EN } from './app-en/finder';
import { MAIL_EN } from './app-en/mail';
import { MATCHING_EN } from './app-en/matching';
import { TKT_EN } from './app-en/tkt';

export const APP_EN: Record<string, string> = {
  ...CORE_EN,
  ...TKT_EN,
  ...MATCHING_EN,
  ...FINDER_EN,
  ...MAIL_EN,
};
