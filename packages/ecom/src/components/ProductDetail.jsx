import { useState } from 'react';
import FeatureIcon from './FeatureIcon.jsx';
import VariantBadge from './VariantBadge.jsx';

export default function ProductDetail({ product, variant, onAddToCart, onBack }) {
  const [qty, setQty] = useState(1);
  const [activeImage, setActiveImage] = useState(0);
  const [wishlisted, setWishlisted] = useState(false);
  const { name, price, compareAtPrice, gallery, description, features } = product;

  const dec = () => setQty((q) => Math.max(1, q - 1));
  const inc = () => setQty((q) => q + 1);

  return (
    <div className="product-detail-page">
      <div className="page-top-row">
        <button type="button" className="btn btn-link" onClick={onBack}>
          ← Back to shop
        </button>
        <VariantBadge variant={variant} />
      </div>

      <div className="product-detail">
        <div className="detail-image-col">
          <div className="detail-image-wrap">
            <img src={gallery[activeImage]} alt={name} className="detail-image" />
          </div>
          <div className="detail-thumbs">
            {gallery.map((src, idx) => (
              <button
                key={src}
                type="button"
                className={`detail-thumb ${activeImage === idx ? 'detail-thumb-active' : ''}`}
                onClick={() => setActiveImage(idx)}
              >
                <img src={src} alt="" />
              </button>
            ))}
          </div>
        </div>

        <div className="detail-info-col">
          <div className="detail-title-row">
            <h1>{name}</h1>
            <button
              type="button"
              className={`wishlist-btn ${wishlisted ? 'wishlist-btn-active' : ''}`}
              onClick={() => setWishlisted((w) => !w)}
              aria-label={wishlisted ? 'Remove from wishlist' : 'Add to wishlist'}
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path
                  d="M12 21s-6.5-4.5-6.5-9.5A4.5 4.5 0 0112 7a4.5 4.5 0 016.5 4.5C18.5 16.5 12 21 12 21z"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  fill={wishlisted ? 'currentColor' : 'none'}
                />
              </svg>
            </button>
          </div>

          <div className="price-block">
            <span className="price-current big">${price.toFixed(2)}</span>
            {compareAtPrice && (
              <span className="price-compare">${compareAtPrice.toFixed(2)}</span>
            )}
          </div>

          <p className="detail-description">{description}</p>

          <div className="feature-grid">
            {features.map((f) => (
              <div key={f.label} className="feature-cell">
                <FeatureIcon name={f.icon} />
                <span>{f.label}</span>
              </div>
            ))}
          </div>

          <div className="qty-row">
            <span className="qty-label">Quantity</span>
            <div className="qty-stepper">
              <button type="button" className="qty-btn" onClick={dec} aria-label="Decrease quantity">
                −
              </button>
              <span className="qty-value">{qty}</span>
              <button type="button" className="qty-btn" onClick={inc} aria-label="Increase quantity">
                +
              </button>
            </div>
          </div>

          <button type="button" className="btn btn-add-cart" onClick={() => onAddToCart(qty)}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path
                d="M6 6h15l-1.5 9h-12L6 6zm0 0L5 3H2"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            Add to Cart
          </button>

          <p className="shipping-note">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M3 7h11v8H3zM14 10h4l3 3v2h-7v-5z" stroke="currentColor" strokeWidth="1.6" fill="none" />
              <circle cx="7" cy="17" r="2" stroke="currentColor" strokeWidth="1.6" fill="none" />
              <circle cx="17" cy="17" r="2" stroke="currentColor" strokeWidth="1.6" fill="none" />
            </svg>
            Free shipping on orders over $50
          </p>
        </div>
      </div>
    </div>
  );
}
