import { useEffect, useState } from 'react';
import { fetchVariant } from './lib/flag.js';
import { track } from './lib/track.js';
import CheckoutA from './variants/CheckoutA.jsx';
import CheckoutB from './variants/CheckoutB.jsx';

const CATALOG = [
  { id: 'p1', name: 'Wireless Headphones', price: 79.99 },
  { id: 'p2', name: 'Mechanical Keyboard', price: 119.0 },
  { id: 'p3', name: 'USB-C Hub', price: 34.5 },
];

export default function App() {
  const [variant, setVariant] = useState(null);
  const [stage, setStage] = useState('listing'); // listing | detail | cart | checkout | done
  const [selected, setSelected] = useState(null);
  const [cart, setCart] = useState([]);

  useEffect(() => {
    fetchVariant()
      .then((f) => {
        setVariant(f.variantId);
        track('page_view', f.variantId); // exposure
      })
      .catch(() => setVariant('A'));
  }, []);

  if (!variant) return <div className="app"><p>Loading store…</p></div>;

  const total = cart.reduce((s, i) => s + i.price, 0);

  const openDetail = (p) => { setSelected(p); setStage('detail'); };
  const addToCart = () => {
    setCart((c) => [...c, selected]);
    track('add_to_cart', variant);
    setStage('cart');
  };
  const goCheckout = () => { track('checkout_started', variant); setStage('checkout'); };
  const complete = () => { track('checkout_completed', variant, 1); setStage('done'); };

  return (
    <div className="app">
      <header>
        <h1>ShopMock</h1>
        <span className="variant-badge">Variant {variant}</span>
      </header>

      {stage === 'listing' && (
        <div className="grid">
          {CATALOG.map((p) => (
            <div key={p.id} className="card" onClick={() => openDetail(p)}>
              <div className="thumb" />
              <div className="name">{p.name}</div>
              <div className="price">${p.price.toFixed(2)}</div>
            </div>
          ))}
        </div>
      )}

      {stage === 'detail' && selected && (
        <div className="detail">
          <h2>{selected.name}</h2>
          <div className="price big">${selected.price.toFixed(2)}</div>
          <button className="btn" onClick={addToCart}>Add to cart</button>
          <button className="btn btn-link" onClick={() => setStage('listing')}>← Back</button>
        </div>
      )}

      {stage === 'cart' && (
        <div className="cart">
          <h2>Your cart</h2>
          {cart.map((i, idx) => (
            <div key={idx} className="cart-row"><span>{i.name}</span><span>${i.price.toFixed(2)}</span></div>
          ))}
          <div className="order-total">Total: ${total.toFixed(2)}</div>
          <button className="btn" onClick={goCheckout}>Proceed to checkout</button>
        </div>
      )}

      {stage === 'checkout' &&
        (variant === 'B'
          ? <CheckoutB total={total} onComplete={complete} />
          : <CheckoutA total={total} onComplete={complete} />)}

      {stage === 'done' && (
        <div className="done">
          <h2>✅ Order placed!</h2>
          <p className="muted">A checkout_completed event was sent for Variant {variant}.</p>
          <button className="btn btn-link" onClick={() => { setCart([]); setStage('listing'); }}>
            Shop again
          </button>
        </div>
      )}
    </div>
  );
}
