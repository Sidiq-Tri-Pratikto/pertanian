'use client';

import NextLink from 'next/link';
import { useState } from 'react';

import { send } from '@/api/client';
import type { components } from '@/api/schema.generated';
import { formatDateTime } from '@/features/organizations';

export type Notice = components['schemas']['NotificationResponse'];

/** In-app notifications on Beranda; opening one marks it read for the acting party only. */
export function NotificationList({ notifications, zone }: { notifications: Notice[]; zone: string }) {
  const [read, setRead] = useState<string[]>([]);
  return (
    <section className="tr-stack" aria-labelledby="pemberitahuan">
      <h2 id="pemberitahuan" className="tr-sys-type-heading-sm">
        Pemberitahuan
      </h2>
      <ul className="tr-stack">
        {notifications.map((notice) => {
          const unread = !notice.read && !read.includes(notice.id);
          return (
            <li key={notice.id} className="tr-panel tr-stack">
              <p className="tr-muted tr-sys-type-support">{`${formatDateTime(notice.created_at, zone)}${unread ? ' · Belum dibaca' : ''}`}</p>
              {notice.pitch_id ? (
                <NextLink
                  className="tr-link"
                  href={`/pitches/${notice.pitch_id}?tab=${notice.tab}`}
                  onClick={() => {
                    setRead((current) => [...current, notice.id]);
                    void send('PUT', `/api/v1/notifications/${notice.id}/read`).catch(() => undefined);
                  }}>
                  {notice.text}
                </NextLink>
              ) : (
                <p>{notice.text}</p>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
