'use client';

import { useRouter } from 'next/navigation';

import { finderHref, type MyProduct } from '@/features/discovery/fit';
import type { Filters } from '@/features/discovery/model';
import { t } from '@/features/i18n/t';

type Props = {
  products: MyProduct[];
  selectedProduct?: string;
  filters: Filters;
  selectedPartner?: string;
};

/** Product selector bound to `?produk=` in the investor finder (spec 059). */
export function ProductPicker({ products, selectedProduct = '', filters, selectedPartner }: Props) {
  const router = useRouter();
  return (
    <div className="tr-field">
      <label htmlFor="finder-produk" className="tr-sys-type-label">
        {t('Cocokkan untuk')}
      </label>
      <select
        id="finder-produk"
        name="produk"
        className="tr-input tr-select"
        value={selectedProduct}
        onChange={(event) => {
          const next = event.target.value || undefined;
          router.push(finderHref(filters, next, selectedPartner));
        }}>
        <option value="">{t('Semua produk')}</option>
        {products.map((product) => (
          <option key={product.id} value={product.id}>
            {product.title}
          </option>
        ))}
      </select>
    </div>
  );
}
