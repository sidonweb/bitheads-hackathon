import { formatBadge } from '../lib/catalogHelpers.js';

export default function ProductCard({ product, onSelect }) {
  const { name, price, compareAtPrice, image, shortDescription, badge } = product;
  const badgeLabel = formatBadge(badge);

  return (
    <article className="product-card">
      <div className="product-card-image-wrap">
        <img src={image} alt={name} className="product-card-image" loading="lazy" />
        {badgeLabel && (
          <span className={`product-badge badge-${badgeLabel.toLowerCase().replace(/\s+/g, '-')}`}>
            {badgeLabel}
          </span>
        )}
      </div>
      <div className="product-card-body">
        <h3 className="product-card-name">{name}</h3>
        <p className="product-card-desc">{shortDescription}</p>
        <div className="product-card-footer">
          <div className="product-card-price">
            <span className="price-current">${price.toFixed(2)}</span>
            {compareAtPrice && (
              <span className="price-compare">${compareAtPrice.toFixed(2)}</span>
            )}
          </div>
          <button type="button" className="btn btn-outline btn-sm" onClick={() => onSelect(product)}>
            View Details
          </button>
        </div>
      </div>
    </article>
  );
}
