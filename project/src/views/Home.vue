<script setup lang="ts">
import { useRouter } from 'vue-router'
import { CATEGORIES, coverFor } from '../photos'

const router = useRouter()

// Vignettes de secours, utilisees tant qu'une categorie ne contient aucune photo.
const fallbacks: Record<string, string> = {
  football: 'https://images.pexels.com/photos/46798/the-ball-stadion-football-the-pitch-46798.jpeg',
  basketball: 'https://images.pexels.com/photos/358042/pexels-photo-358042.jpeg',
  handball: 'https://images.pexels.com/photos/3639486/pexels-photo-3639486.jpeg',
  boxing: 'https://images.pexels.com/photos/4761792/pexels-photo-4761792.jpeg'
}

const categories = CATEGORIES.map((category) => ({
  ...category,
  image: coverFor(category.slug)?.src ?? fallbacks[category.slug],
  route: `/gallery/${category.slug}`
}))
</script>

<template>
  <div>
    <h1 class="text-4xl font-bold text-center mb-12 text-white">Photographie Sportive</h1>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-8">
      <div v-for="category in categories" :key="category.slug"
           @click="router.push(category.route)"
           class="gallery-item cursor-pointer h-64">
        <img :src="category.image" :alt="category.label" loading="lazy" decoding="async">
        <div class="absolute inset-0 bg-black bg-opacity-60 flex items-center justify-center">
          <h2 class="text-white text-2xl font-bold">{{ category.label }}</h2>
        </div>
      </div>
    </div>
  </div>
</template>
