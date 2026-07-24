const FEATURE_ICONS = ['noise', 'battery', 'bluetooth', 'comfort', 'speed', 'shield', 'plug', 'star'];

export function formatBadge(badge) {
  if (!badge) return null;
  if (badge === 'Best Seller') return 'BEST SELLER';
  if (badge === 'New') return 'NEW ARRIVAL';
  if (badge === 'Sale') return 'SALE';
  return badge.toUpperCase();
}

export function buildGallery(imageUrl) {
  const base = imageUrl.split('?')[0];
  return [
    imageUrl,
    `${base}?auto=format&fit=crop&w=600&h=600&crop=entropy&q=80`,
    `${base}?auto=format&fit=crop&w=600&h=600&crop=faces&q=80`,
    `${base}?auto=format&fit=crop&w=600&h=600&crop=edges&q=80`,
  ];
}

export function buildFeatures(specs) {
  const labels = [...specs];
  while (labels.length < 4) labels.push('Premium build quality');
  return labels.slice(0, 4).map((label, i) => ({
    icon: FEATURE_ICONS[i],
    label: label.charAt(0).toUpperCase() + label.slice(1),
  }));
}

export function enrichProduct(product) {
  return {
    ...product,
    shortDescription:
      product.shortDescription ||
      (product.description.length > 110
        ? `${product.description.slice(0, 107)}…`
        : product.description),
    features: product.features || buildFeatures(product.specs),
    gallery: product.gallery || buildGallery(product.image),
  };
}

export const CATEGORY_META = {
  All: {
    title: 'All Products',
    subtitle: 'Browse our full collection of premium tech essentials.',
  },
  Audio: {
    title: 'Premium Audio',
    subtitle:
      'Immersive sound for every moment. From studio-grade headphones to portable speakers.',
  },
  Workspace: {
    title: 'Workspace Essentials',
    subtitle: 'Build your perfect desk setup with premium peripherals and accessories.',
  },
  Mobile: {
    title: 'Mobile Accessories',
    subtitle: 'Power up and protect your devices on the go.',
  },
};
