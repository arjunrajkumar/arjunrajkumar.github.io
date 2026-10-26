const gallery = document.querySelector('#gallery');
const galleryLink = document.querySelector('#gallery-link');
const galleryImage = document.querySelector('#gallery-image');
const galleryToggle = document.querySelector('#gallery-toggle');
const galleryProgress = document.querySelector('#gallery-progress');
const slideDuration = 3000;

const photos = [
  {
    file: 'merchant-review.jpg',
    width: 720,
    height: 1059,
    alt: 'A five-star Shopify review: the app optimized 50,000 images for a store with 17,000 products in less than 24 hours.'
  },
  {
    file: 'merchant-growth.jpg',
    width: 750,
    height: 1334,
    alt: 'A chart showing merchant numbers growing from January to July 2022.'
  },
  {
    file: '500-merchants.jpg',
    width: 750,
    height: 1334,
    alt: 'My post celebrating 500 merchants after 11 months and the introduction of paid plans in June.'
  },
  {
    file: '500-merchants-chart.jpg',
    width: 750,
    height: 1334,
    alt: 'A merchant growth chart marking 500 merchants in November 2022.'
  },
  {
    file: 'first-product-sale.jpg',
    width: 1125,
    height: 2000,
    alt: 'My announcement about selling my first product after building and growing it over two years, mainly part-time.'
  }
];

let currentPhoto = 0;
let elapsed = 0;
let lastFrame = null;
let frameId = null;
let paused = false;
let ready = false;
let renderVersion = 0;

const steps = photos.map((photo, index) => {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'gallery-step';
  button.setAttribute('aria-label', `View photo ${index + 1}`);
  const track = document.createElement('span');
  track.className = 'gallery-track';
  const fill = document.createElement('span');
  fill.className = 'gallery-fill';
  track.append(fill);
  button.append(track);
  button.addEventListener('click', () => showPhoto(index));
  galleryProgress.append(button);
  return { button, fill };
});

function stopTimer() {
  cancelAnimationFrame(frameId);
  frameId = null;
  lastFrame = null;
}

function tick(timestamp) {
  if (!gallery.open || paused || document.hidden || !ready) return;
  if (lastFrame !== null) elapsed += timestamp - lastFrame;
  lastFrame = timestamp;
  steps[currentPhoto].fill.style.transform = `scaleX(${Math.min(elapsed / slideDuration, 1)})`;
  if (elapsed >= slideDuration) {
    showPhoto(currentPhoto + 1);
  } else {
    frameId = requestAnimationFrame(tick);
  }
}

function syncPlayback() {
  stopTimer();
  galleryToggle.setAttribute('aria-label', paused ? 'Resume slideshow' : 'Pause slideshow');
  if (gallery.open && ready && !paused && !document.hidden) {
    frameId = requestAnimationFrame(tick);
  }
}

async function showPhoto(index) {
  stopTimer();
  const version = ++renderVersion;
  currentPhoto = (index + photos.length) % photos.length;
  elapsed = 0;
  ready = false;
  const photo = photos[currentPhoto];
  galleryImage.src = `assets/shopify-apps/${photo.file}`;
  galleryImage.width = photo.width;
  galleryImage.height = photo.height;
  galleryImage.alt = photo.alt;
  steps.forEach(({ button, fill }, step) => {
    button.setAttribute('aria-current', String(step === currentPhoto));
    fill.style.transform = `scaleX(${step < currentPhoto ? 1 : 0})`;
  });
  // Give each image its full viewing time after it has loaded.
  try { await galleryImage.decode(); } catch { /* Continue if a file cannot load. */ }
  if (version !== renderVersion || !gallery.open) return;
  ready = true;
  syncPlayback();
}

galleryLink.addEventListener('click', (event) => {
  if (typeof gallery.showModal !== 'function' || event.button !== 0 ||
      event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  paused = false;
  gallery.showModal();
  document.documentElement.classList.add('gallery-open');
  showPhoto(0);
  photos.forEach((photo) => { new Image().src = `assets/shopify-apps/${photo.file}`; });
});

galleryToggle.addEventListener('click', () => {
  paused = !paused;
  syncPlayback();
});

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

document.addEventListener('visibilitychange', syncPlayback);

gallery.addEventListener('close', () => {
  stopTimer();
  renderVersion++;
  ready = false;
  document.documentElement.classList.remove('gallery-open');
  galleryLink.focus();
});
