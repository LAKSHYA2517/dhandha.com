// Demo/testing fallback so products without an uploaded photo still render a
// real (stable, per-product) image instead of a broken/empty box.
export function posterUrl(product) {
  return product.image_url || `https://picsum.photos/seed/${product.id}/600/800`
}
