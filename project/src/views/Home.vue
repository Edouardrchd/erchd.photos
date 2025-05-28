<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const categories = [
  { name: 'Football', image: 'https://images.pexels.com/photos/46798/the-ball-stadion-football-the-pitch-46798.jpeg', route: '/gallery/football' },
  { name: 'Basketball', image: 'https://images.pexels.com/photos/358042/pexels-photo-358042.jpeg', route: '/gallery/basketball' },
  { name: 'Handball', image: 'https://images.pexels.com/photos/3639486/pexels-photo-3639486.jpeg', route: '/gallery/handball' },
  { name: 'Boxe', image: 'https://images.pexels.com/photos/4761792/pexels-photo-4761792.jpeg', route: '/gallery/boxing' }
]
</script>

<template>
  <div>
    <h1 class="text-4xl font-bold text-center mb-12 text-white">Photographie Sportive</h1>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-8">
      <div v-for="category in categories" :key="category.name" 
           @click="router.push(category.route)"
           class="gallery-item cursor-pointer h-64">
        <img :src="category.image" :alt="category.name">
        <div class="absolute inset-0 bg-black bg-opacity-60 flex items-center justify-center">
          <h2 class="text-white text-2xl font-bold">{{ category.name }}</h2>
        </div>
      </div>
    </div>
  </div>
</template>