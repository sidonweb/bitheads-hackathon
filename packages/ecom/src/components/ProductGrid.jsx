import { useMemo, useState } from 'react';
import { CATALOG, CATEGORIES } from '../data/catalog.js';
import { CATEGORY_META } from '../lib/catalogHelpers.js';
import ProductCard from './ProductCard.jsx';
import VariantBadge from './VariantBadge.jsx';

const PAGE_SIZE = 8;

export default function ProductGrid({ variant, onSelectProduct, showSocialProof = false }) {
  const [category, setCategory] = useState('All');
  const [page, setPage] = useState(1);
  const [sortOpen, setSortOpen] = useState(false);

  const filtered = useMemo(
    () => (category === 'All' ? CATALOG : CATALOG.filter((p) => p.category === category)),
    [category],
  );

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageItems = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const meta = CATEGORY_META[category];

  const selectCategory = (cat) => {
    setCategory(cat);
    setPage(1);
  };

  return (
    <div className="listing">
      <div className="listing-header">
        <div className="listing-header-text">
          <h1>{meta.title}</h1>
          <p>{meta.subtitle}</p>
        </div>
        <div className="listing-header-actions">
          <VariantBadge variant={variant} />
          <div className="sort-wrap">
            <button
              type="button"
              className="btn btn-outline btn-sm"
              onClick={() => setSortOpen((o) => !o)}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M4 6h16M7 12h10M10 18h4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
              Filter &amp; Sort
            </button>
            {sortOpen && (
              <div className="sort-dropdown">
                <button type="button" onClick={() => setSortOpen(false)}>Featured</button>
                <button type="button" onClick={() => setSortOpen(false)}>Price: Low to High</button>
                <button type="button" onClick={() => setSortOpen(false)}>Price: High to Low</button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="category-pills">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            type="button"
            className={`pill ${category === cat ? 'pill-active' : ''}`}
            onClick={() => selectCategory(cat)}
          >
            {cat}
          </button>
        ))}
      </div>

      <div className="product-grid">
        {pageItems.map((p) => (
          <ProductCard
            key={p.id}
            product={p}
            onSelect={onSelectProduct}
            showSocialProof={showSocialProof}
          />
        ))}
      </div>

      {totalPages > 1 && (
        <nav className="pagination" aria-label="Product pages">
          <button
            type="button"
            className="page-btn"
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
            aria-label="Previous page"
          >
            ‹
          </button>
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((n) => (
            <button
              key={n}
              type="button"
              className={`page-btn ${page === n ? 'page-btn-active' : ''}`}
              onClick={() => setPage(n)}
            >
              {n}
            </button>
          ))}
          <button
            type="button"
            className="page-btn"
            disabled={page === totalPages}
            onClick={() => setPage((p) => p + 1)}
            aria-label="Next page"
          >
            ›
          </button>
        </nav>
      )}
    </div>
  );
}
