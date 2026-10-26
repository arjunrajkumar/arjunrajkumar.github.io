const gallery = document.querySelector('#gallery');
const galleryLink = document.querySelector('#gallery-link');
const galleryImage = document.querySelector('#gallery-image');
const galleryCaption = document.querySelector('#gallery-caption');
const galleryPosition = document.querySelector('#gallery-position');
const previousButton = document.querySelector('#gallery-previous');
const nextButton = document.querySelector('#gallery-next');

const photos = [
  {
    file: 'merchant-review.jpg',
    width: 720,
    height: 1059,
    caption: 'A review from a Shopify merchant.',
    alt: 'A five-star Shopify review: the app optimized 50,000 images for a store with 17,000 products in less than 24 hours.'
  },
  {
    file: 'merchant-growth.jpg',
    width: 750,
    height: 1334,
    caption: 'Merchant growth in 2022.',
    alt: 'A chart showing merchant numbers growing from January to July 2022.'
  },
  {
    file: '500-merchants.jpg',
    width: 750,
    height: 1334,
    caption: 'Reaching 500 merchants.',
    alt: 'My post celebrating 500 merchants after 11 months and the introduction of paid plans in June.'
  },
  {
    file: '500-merchants-chart.jpg',
    width: 750,
    height: 1334,
    caption: '500 merchants in November 2022.',
    alt: 'A merchant growth chart marking 500 merchants in November 2022.'
  },
  {
    file: 'first-product-sale.jpg',
    width: 1125,
    height: 2000,
    caption: 'Selling my first product.',
    alt: 'My announcement about selling my first product after building and growing it over two years, mainly part-time.'
  }
];

let currentPhoto = 0;

function showPhoto(index) {
  const focusedControl = document.activeElement;
  currentPhoto = Math.max(0, Math.min(index, photos.length - 1));
  const photo = photos[currentPhoto];
  galleryImage.src = `assets/shopify-apps/${photo.file}`;
  galleryImage.width = photo.width;
  galleryImage.height = photo.height;
  galleryImage.alt = photo.alt;
  galleryCaption.textContent = photo.caption;
  galleryPosition.textContent = `${currentPhoto + 1} of ${photos.length}`;
  previousButton.disabled = currentPhoto === 0;
  nextButton.disabled = currentPhoto === photos.length - 1;
  if (focusedControl === nextButton && nextButton.disabled) previousButton.focus();
  if (focusedControl === previousButton && previousButton.disabled) nextButton.focus();
}

galleryLink.addEventListener('click', (event) => {
  if (typeof gallery.showModal !== 'function' || event.button !== 0 ||
      event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  showPhoto(0);
  gallery.showModal();
  document.documentElement.classList.add('gallery-open');
});

document.querySelector('#gallery-close').addEventListener('click', () => gallery.close());
previousButton.addEventListener('click', () => showPhoto(currentPhoto - 1));
nextButton.addEventListener('click', () => showPhoto(currentPhoto + 1));

gallery.addEventListener('keydown', (event) => {
  if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
    event.preventDefault();
    showPhoto(currentPhoto + (event.key === 'ArrowRight' ? 1 : -1));
  }
});

gallery.addEventListener('click', (event) => {
  if (event.target !== gallery) return;
  const bounds = gallery.getBoundingClientRect();
  if (event.clientX < bounds.left || event.clientX > bounds.right ||
      event.clientY < bounds.top || event.clientY > bounds.bottom) gallery.close();
});

gallery.addEventListener('close', () => {
  document.documentElement.classList.remove('gallery-open');
  galleryLink.focus();
});
