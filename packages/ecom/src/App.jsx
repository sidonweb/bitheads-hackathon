import { useEffect, useState } from 'react';
import { fetchVariant } from './lib/flag.js';
import { track } from './lib/track.js';
import { resolveVariation } from './lib/variations.js';
import { experimentIdForVariation } from './config.js';
import { CATALOG } from './data/catalog.js';
import Header from './components/Header.jsx';
import ProductGrid from './components/ProductGrid.jsx';
import ProductDetail from './components/ProductDetail.jsx';
import Cart from './components/Cart.jsx';
import OrderConfirmation from './components/OrderConfirmation.jsx';
import SiteFooter from './components/SiteFooter.jsx';
import CheckoutSteps from './components/CheckoutSteps.jsx';
import VariantBadge from './components/VariantBadge.jsx';
import CheckoutA from './variants/CheckoutA.jsx';
import CheckoutB from './variants/CheckoutB.jsx';
import ProductGridB from './variants/ProductGridB.jsx';
import ProductDetailB from './variants/ProductDetailB.jsx';
import CartB from './variants/CartB.jsx';

function resolveDeepLink(params) {
  const screen = params.get('screen');
  const productId = params.get('product') || 'p1';
  const product = CATALOG.find((p) => p.id === productId) || CATALOG[0];

  if (screen === 'checkout') {
    return { stage: 'checkout', cart: [CATALOG[0]], selected: null };
  }
  if (screen === 'cart') {
    return { stage: 'cart', cart: [product], selected: null };
  }
  if (screen === 'detail') {
    return { stage: 'detail', cart: [], selected: product };
  }
  return null;
}

export default function App() {
  const [variation] = useState(() => resolveVariation());
  const [variant, setVariant] = useState(null);
  const [stage, setStage] = useState('listing');
  const [selected, setSelected] = useState(null);
  const [cart, setCart] = useState([]);

  const expId = experimentIdForVariation(variation);

  useEffect(() => {
    fetchVariant(expId)
      .then((f) => {
        setVariant(f.variantId);
        track('page_view', f.variantId, 0, expId);
      })
      .catch(() => setVariant('A'));

    const deepLink = resolveDeepLink(new URLSearchParams(window.location.search));
    if (deepLink) {
      setStage(deepLink.stage);
      setCart(deepLink.cart);
      if (deepLink.selected) setSelected(deepLink.selected);
    }
  }, []);

  if (!variant) {
    return (
      <div className="page-shell">
        <div className="loading-state">
          <div className="loading-spinner" />
          <p>Loading store…</p>
        </div>
      </div>
    );
  }

  const total = cart.reduce((s, i) => s + i.price, 0);

  const goListing = () => setStage('listing');
  const openDetail = (p) => {
    setSelected(p);
    setStage('detail');
  };
  const addToCart = (qty) => {
    const items = Array.from({ length: qty }, () => selected);
    setCart((c) => [...c, ...items]);
    track('add_to_cart', variant, 0, expId);
    setStage('cart');
  };
  const removeItem = (idx) => setCart((c) => c.filter((_, i) => i !== idx));
  const goCheckout = () => {
    track('checkout_started', variant, 0, expId);
    setStage('checkout');
  };
  const complete = () => {
    track('checkout_completed', variant, 1, expId);
    setStage('done');
  };
  const shopAgain = () => {
    setCart([]);
    setStage('listing');
  };

  const handleCartClick = () => {
    if (cart.length > 0) setStage('cart');
  };

  const ListingView =
    variation === 'plp-social-proof' && variant === 'B' ? ProductGridB : ProductGrid;
  const DetailView =
    variation === 'pdp-sticky-cta' && variant === 'B' ? ProductDetailB : ProductDetail;
  const CartView = variation === 'cart-shipping-nudge' && variant === 'B' ? CartB : Cart;
  const CheckoutView =
    variation === 'checkout-cta' && variant === 'B' ? CheckoutB : CheckoutA;

  return (
    <div className="page-shell">
      <div className="page-content">
        <Header
          cartCount={cart.length}
          onCartClick={handleCartClick}
          onLogoClick={goListing}
        />

        <main className="main-content">
          {stage === 'listing' && (
            <ListingView variant={variant} onSelectProduct={openDetail} />
          )}

          {stage === 'detail' && selected && (
            <DetailView
              product={selected}
              variant={variant}
              onAddToCart={addToCart}
              onBack={goListing}
            />
          )}

          {stage === 'cart' && (
            <CartView
              cart={cart}
              total={total}
              variant={variant}
              onRemoveItem={removeItem}
              onCheckout={goCheckout}
              onContinueShopping={goListing}
            />
          )}

          {stage === 'checkout' && (
            <CheckoutView
              cart={cart}
              total={total}
              variant={variant}
              onComplete={complete}
            />
          )}

          {stage === 'done' && (
            <div className="confirmation-wrap">
              <div className="page-top-row confirmation-steps-row">
                <CheckoutSteps active="done" />
                <VariantBadge variant={variant} />
              </div>
              <OrderConfirmation
                cart={cart}
                total={total}
                variant={variant}
                onShopAgain={shopAgain}
              />
            </div>
          )}
        </main>
      </div>

      <SiteFooter />
    </div>
  );
}
