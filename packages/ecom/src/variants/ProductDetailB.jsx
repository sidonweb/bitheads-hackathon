import ProductDetail from '../components/ProductDetail.jsx';

// Variant B (exp_3): sticky bottom add-to-cart bar.
export default function ProductDetailB(props) {
  return <ProductDetail {...props} stickyCta />;
}
