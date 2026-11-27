import { send } from '@/api/client';
import type { components } from '@/api/schema.generated';

export type Topics = components['schemas']['Topics'];
export type Subscription = components['schemas']['SubscriptionResponse'];
export type Teaser = components['schemas']['TeaserResponse'];

/** The page's language becomes the language of every email this subscription receives. */
export function subscribe(email: string, topics: Topics, locale: 'id' | 'en' = 'id'): Promise<{ status: string }> {
  return send('POST', '/api/v1/subscriptions', { email, topics, locale });
}

export function confirmSubscription(token: string): Promise<Subscription> {
  return send('POST', '/api/v1/subscriptions/confirm', { token });
}

export function readSubscription(token: string): Promise<Subscription> {
  return send('POST', '/api/v1/subscriptions/manage', { token });
}

export function updateTopics(token: string, topics: Topics): Promise<Subscription> {
  return send('PUT', '/api/v1/subscriptions/manage', { token, topics });
}

export function unsubscribe(token: string): Promise<Subscription> {
  return send('POST', '/api/v1/subscriptions/unsubscribe', { token });
}

export function setInvestorDigest(id: string, actingPartyId: string, version: number, enabled: boolean): Promise<unknown> {
  return send('PUT', `/api/v1/inventions/${id}/investor-digest`, { acting_party_id: actingPartyId, expected_version: version, enabled });
}

/** Split "air, filter surya" into up to five keywords. */
export function keywordsOf(text: string): string[] {
  return [...new Set(text.split(',').map((word) => word.trim()).filter(Boolean))].slice(0, 5);
}

export function hasTopics(topics: Topics): boolean {
  return Boolean(topics.sectors?.length || topics.stages?.length || topics.keywords?.length);
}

export type Follow = components['schemas']['FollowResponse'];

/** Follow one invention's public updates; the page's language becomes the language of its emails (053). */
export function follow(inventionId: string, email: string, locale: 'id' | 'en' = 'id'): Promise<{ status: string }> {
  return send('POST', '/api/v1/follows', { invention_id: inventionId, email, locale });
}

export function previewFollow(token: string): Promise<Follow> {
  return send('POST', '/api/v1/follows/preview', { token });
}

export function confirmFollow(token: string): Promise<Follow> {
  return send('POST', '/api/v1/follows/confirm', { token });
}

export function readFollow(token: string): Promise<Follow> {
  return send('POST', '/api/v1/follows/manage', { token });
}

export function setFollowLanguage(token: string, locale: 'id' | 'en'): Promise<Follow> {
  return send('PUT', '/api/v1/follows/manage', { token, locale });
}

export function unfollow(token: string): Promise<Follow> {
  return send('POST', '/api/v1/follows/unfollow', { token });
}
