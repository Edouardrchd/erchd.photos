import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// https://astro.build/config
export default defineConfig({
  // L'adresse publique du site. Elle sert a fabriquer sitemap.xml et les
  // adresses completes des apercus de lien. A changer ici si le domaine change.
  site: 'https://edouardvisuals.com',
  integrations: [sitemap()],
  build: {
    // Un site d'une seule page : on garde /404.html plutot que /404/index.html
    format: 'file'
  }
});
