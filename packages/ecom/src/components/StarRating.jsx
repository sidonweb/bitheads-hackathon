export default function StarRating({ rating, reviewCount }) {
  const full = Math.floor(rating);
  const half = rating - full >= 0.5;
  const stars = Array.from({ length: 5 }, (_, i) => {
    if (i < full) return 'full';
    if (i === full && half) return 'half';
    return 'empty';
  });

  return (
    <div className="star-rating">
      <span className="stars" aria-label={`${rating} out of 5 stars`}>
        {stars.map((s, i) => (
          <span key={i} className={`star star-${s}`}>★</span>
        ))}
      </span>
      {reviewCount != null && (
        <span className="review-count">({reviewCount.toLocaleString()})</span>
      )}
    </div>
  );
}
