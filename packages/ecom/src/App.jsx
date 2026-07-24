import { useEffect, useState } from 'react';
import { fetchVariant } from './lib/flag.js';
import { track } from './lib/track.js';
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

export default function App() {
  const [variant, setVariant] = useState(null);
  const [stage, setStage] = useState('listing');
  const [selected, setSelected] = useState(null);
  const [cart, setCart] = useState([]);

  useEffect(() => {
    fetchVariant()
      .then((f) => {
        setVariant(f.variantId);
        track('page_view', f.variantId);
      })
      .catch(() => setVariant('A'));

    // Deep-link: ?screen=checkout jumps straight to the checkout page with a
    // seeded cart, so the A/B difference (the CTA) is directly viewable without
    // clicking through the funnel. Used by the copilot's page-inspection tool.
    const screen = new URLSearchParams(window.location.search).get('screen');
    if (screen === 'checkout') {
      setCart([CATALOG[0]]);
      setStage('checkout');
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
    track('add_to_cart', variant);
    setStage('cart');
  };
  const removeItem = (idx) => setCart((c) => c.filter((_, i) => i !== idx));
  const goCheckout = () => {
    track('checkout_started', variant);
    setStage('checkout');
  };
  const complete = () => {
    track('checkout_completed', variant, 1);
    setStage('done');
  };
  const shopAgain = () => {
    setCart([]);
    setStage('listing');
  };

  const handleCartClick = () => {
    if (cart.length > 0) setStage('cart');
  };

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
            <ProductGrid variant={variant} onSelectProduct={openDetail} />
          )}

          {stage === 'detail' && selected && (
            <ProductDetail
              product={selected}
              variant={variant}
              onAddToCart={addToCart}
              onBack={goListing}
            />
          )}

          {stage === 'cart' && (
            <Cart
              cart={cart}
              total={total}
              variant={variant}
              onRemoveItem={removeItem}
              onCheckout={goCheckout}
              onContinueShopping={goListing}
            />
          )}

          {stage === 'checkout' &&
            (variant === 'B' ? (
              <CheckoutB
                cart={cart}
                total={total}
                variant={variant}
                onComplete={complete}
              />
            ) : (
              <CheckoutA
                cart={cart}
                total={total}
                variant={variant}
                onComplete={complete}
              />
            ))}

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
