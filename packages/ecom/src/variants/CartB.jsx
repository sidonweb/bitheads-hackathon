import Cart from '../components/Cart.jsx';

// Variant B (exp_4): free-shipping progress nudge + emphasized checkout CTA.
export default function CartB(props) {
  return <Cart {...props} showShippingNudge />;
}
