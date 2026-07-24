import ProductGrid from '../components/ProductGrid.jsx';

// Variant B (exp_2): star ratings + review counts on product cards.
export default function ProductGridB(props) {
  return <ProductGrid {...props} showSocialProof />;
}
